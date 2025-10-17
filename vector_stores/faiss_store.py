import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional
from .base import BaseVectorStore
from document_loaders.base import Document
from embedding import embedding_model_factory


class FAISSVectorStore(BaseVectorStore):
    """
    FAISS向量存储实现，使用FAISS库进行高效的向量搜索
    """
    
    def __init__(self, embedding_model=None, persist_directory: str = "./vector_store", index_name: str = "faiss_index"):
        """
        初始化FAISS向量存储
        
        Args:
            embedding_model: 嵌入模型
            persist_directory: 持久化目录
            index_name: 索引名称
        """
        # 如果没有提供嵌入模型，使用默认的Ollama嵌入模型
        if embedding_model is None:
            try:
                embedding_model = embedding_model_factory.create("ollama")
            except Exception as e:
                print(f"创建默认嵌入模型失败: {str(e)}")
                # 仍然允许创建，后续可以手动设置嵌入模型
        
        super().__init__(embedding_model, persist_directory)
        self.index_name = index_name
        self.index = None  # FAISS索引
        self.documents = {}  # 文档ID到文档对象的映射
        self.embeddings = []  # 嵌入向量列表
        self.id_to_index = {}  # 文档ID到嵌入索引的映射
        self.source_to_doc_ids = {}  # 源到文档ID的映射，用于快速查找
        
        # 尝试加载已存在的索引
        if self.persist_directory:
            self.load()
            # 如果加载后没有源映射，重建它
            if not hasattr(self, 'source_to_doc_ids') or not self.source_to_doc_ids:
                self._rebuild_source_to_doc_ids_map()
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            添加的文档ID列表
        """
        if not documents:
            return []
        
        # 过滤掉已存在的文档
        new_documents = []
        for doc in documents:
            if doc.id not in self.documents:
                new_documents.append(doc)
        
        if not new_documents:
            print("所有文档已存在，无需添加")
            return []
        
        # 提取文档内容
        texts = [doc.content for doc in new_documents]
        
        # 创建嵌入向量
        new_embeddings = self.create_embeddings(texts)
        
        # 如果索引不存在，创建新索引
        if self.index is None:
            dimension = new_embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)  # 使用L2距离
        
        # 添加新的嵌入向量到索引
        self.index.add(new_embeddings)
        
        # 更新文档和嵌入映射
        added_ids = []
        for i, doc in enumerate(new_documents):
            # 计算嵌入索引
            embedding_index = len(self.embeddings)
            
            # 存储文档
            self.documents[doc.id] = doc
            
            # 存储嵌入向量
            self.embeddings.append(new_embeddings[i])
            
            # 映射文档ID到嵌入索引
            self.id_to_index[doc.id] = embedding_index
            
            # 更新源到文档ID的映射
            if "source" in doc.metadata:
                source = doc.metadata["source"]
                if source not in self.source_to_doc_ids:
                    self.source_to_doc_ids[source] = []
                if doc.id not in self.source_to_doc_ids[source]:
                    self.source_to_doc_ids[source].append(doc.id)
            
            added_ids.append(doc.id)
        
        # 保存索引
        self.save()
        
        print(f"成功添加 {len(added_ids)} 个新文档")
        return added_ids
    
    def search(self, query: str, k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 搜索查询
            k: 返回结果数量
            **kwargs: 其他搜索参数，如source_filter（源过滤）、score_threshold（分数阈值）
            
        Returns:
            搜索结果列表，每个结果包含文档和相似度分数
        """
        if self.index is None or not self.documents:
            return []
        
        # 获取搜索参数
        source_filter = kwargs.get('source_filter', None)
        score_threshold = kwargs.get('score_threshold', None)
        
        # 创建查询嵌入
        query_embedding = self.create_embeddings([query])[0].reshape(1, -1)
        
        # 为了更好地过滤，搜索更多结果
        search_k = min(k * 2, len(self.documents))
        
        # 搜索相似向量
        distances, indices = self.index.search(query_embedding, search_k)
        
        # 构建结果
        results = []
        for i in range(len(indices[0])):
            index = indices[0][i]
            distance = distances[0][i]
            
            # 查找对应的文档ID
            doc_id = None
            for did, idx in self.id_to_index.items():
                if idx == index:
                    doc_id = did
                    break
            
            if doc_id and doc_id in self.documents:
                doc = self.documents[doc_id]
                score = 1.0 / (1.0 + distance)  # 将距离转换为相似度分数
                
                # 应用源过滤
                if source_filter and doc.metadata.get("source") != source_filter:
                    continue
                
                # 应用分数阈值
                if score_threshold and score < score_threshold:
                    continue
                
                results.append({
                    "document": doc,
                    "score": score,
                    "distance": float(distance)
                })
        
        # 按相似度分数排序并限制返回数量
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]
    
    def delete(self, document_ids: List[str]) -> bool:
        """
        根据文档ID删除文档
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            是否删除成功
        """
        if not document_ids or self.index is None:
            return False
        
        # 标记要删除的索引
        indices_to_delete = []
        for doc_id in document_ids:
            if doc_id in self.id_to_index:
                indices_to_delete.append(self.id_to_index[doc_id])
        
        if not indices_to_delete:
            return False
        
        # 更新源映射
        for doc_id in document_ids:
            if doc_id in self.documents:
                doc = self.documents[doc_id]
                if "source" in doc.metadata:
                    source = doc.metadata["source"]
                    if source in self.source_to_doc_ids and doc_id in self.source_to_doc_ids[source]:
                        self.source_to_doc_ids[source].remove(doc_id)
                        # 如果源映射为空，删除该源
                        if not self.source_to_doc_ids[source]:
                            del self.source_to_doc_ids[source]
        
        # 重建索引
        result = self._rebuild_vector_store(exclude_indices=indices_to_delete)
        if result:
            print(f"成功删除 {len(document_ids)} 个文档")
        return result
    
    def delete_by_source(self, source: str) -> bool:
        """
        根据源删除文档
        
        Args:
            source: 文档源（文件路径或URL）
            
        Returns:
            是否删除成功
        """
        # 使用源到文档ID的映射进行快速查找
        doc_ids_to_delete = self.source_to_doc_ids.get(source, [])
        
        if not doc_ids_to_delete:
            # 如果映射中没有，回退到遍历所有文档
            doc_ids_to_delete = []
            for doc_id, doc in self.documents.items():
                if "source" in doc.metadata and doc.metadata["source"] == source:
                    doc_ids_to_delete.append(doc_id)
        
        if not doc_ids_to_delete:
            return False
        
        # 删除文档
        result = self.delete(doc_ids_to_delete)
        if result:
            # 从源映射中删除
            if source in self.source_to_doc_ids:
                del self.source_to_doc_ids[source]
            print(f"成功从源 {source} 删除 {len(doc_ids_to_delete)} 个文档")
        
        return result
    
    def update_document(self, document_id: str, document: Document) -> bool:
        """
        更新文档
        
        Args:
            document_id: 文档ID
            document: 新的文档对象
            
        Returns:
            是否更新成功
        """
        if document_id not in self.documents:
            return False
        
        # 删除旧文档
        if not self.delete([document_id]):
            return False
        
        # 添加新文档
        new_ids = self.add_documents([document])
        return len(new_ids) > 0
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        根据ID获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档对象，如果不存在则返回None
        """
        return self.documents.get(document_id)
    
    def list_documents(self, source: Optional[str] = None) -> List[Document]:
        """
        列出所有文档或指定源的文档
        
        Args:
            source: 可选，指定文档源
            
        Returns:
            文档列表
        """
        if not source:
            return list(self.documents.values())
        
        # 使用源映射进行快速过滤
        if source in self.source_to_doc_ids:
            return [self.documents[doc_id] for doc_id in self.source_to_doc_ids[source] if doc_id in self.documents]
        
        # 回退到遍历所有文档
        return [doc for doc in self.documents.values() if doc.metadata.get("source") == source]
    
    def save(self) -> bool:
        """
        保存向量存储
        
        Returns:
            是否保存成功
        """
        if not self.persist_directory or self.index is None:
            return False
        
        try:
            # 创建目录（如果不存在）
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 保存FAISS索引
            index_path = os.path.join(self.persist_directory, f"{self.index_name}.index")
            if self.index is not None:
                faiss.write_index(self.index, index_path)
            
            # 保存文档
            documents_path = os.path.join(self.persist_directory, f"{self.index_name}_documents.json")
            # 将Document对象转换为字典
            documents_dict = {}
            for doc_id, doc in self.documents.items():
                documents_dict[doc_id] = {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "chunk_id": doc.chunk_id
                }
            
            with open(documents_path, "w", encoding="utf-8") as f:
                json.dump(documents_dict, f, ensure_ascii=False, indent=2)
            
            # 保存嵌入映射
            mappings_path = os.path.join(self.persist_directory, f"{self.index_name}_mappings.json")
            mappings = {
                "id_to_index": self.id_to_index,
                "source_to_doc_ids": self.source_to_doc_ids
            }
            
            with open(mappings_path, "w", encoding="utf-8") as f:
                json.dump(mappings, f, ensure_ascii=False, indent=2)
            
            # 保存嵌入向量
            embeddings_path = os.path.join(self.persist_directory, f"{self.index_name}_embeddings.npy")
            if self.embeddings:
                np.save(embeddings_path, np.array(self.embeddings))
            
            print(f"成功保存向量存储到 {self.persist_directory}")
            return True
        
        except Exception as e:
            print(f"保存向量存储失败: {str(e)}")
            return False
    
    def load(self) -> bool:
        """
        加载向量存储
        
        Returns:
            是否加载成功
        """
        if not self.persist_directory:
            return False
        
        try:
            # 加载FAISS索引
            index_path = os.path.join(self.persist_directory, f"{self.index_name}.index")
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
            
            # 加载文档
            documents_path = os.path.join(self.persist_directory, f"{self.index_name}_documents.json")
            if os.path.exists(documents_path):
                with open(documents_path, "r", encoding="utf-8") as f:
                    documents_dict = json.load(f)
                    
                # 将字典转换回Document对象
                self.documents = {}
                for doc_id, doc_data in documents_dict.items():
                    self.documents[doc_id] = Document(
                        id=doc_data["id"],
                        content=doc_data["content"],
                        metadata=doc_data["metadata"],
                        chunk_id=doc_data.get("chunk_id")
                    )
            
            # 加载嵌入映射
            mappings_path = os.path.join(self.persist_directory, f"{self.index_name}_mappings.json")
            if os.path.exists(mappings_path):
                with open(mappings_path, "r", encoding="utf-8") as f:
                    mappings = json.load(f)
                    self.id_to_index = mappings.get("id_to_index", {})
                    self.source_to_doc_ids = mappings.get("source_to_doc_ids", {})
            
            # 加载嵌入向量
            embeddings_path = os.path.join(self.persist_directory, f"{self.index_name}_embeddings.npy")
            if os.path.exists(embeddings_path):
                self.embeddings = np.load(embeddings_path).tolist()
            
            # 如果没有源映射，重建它
            if not hasattr(self, 'source_to_doc_ids') or not self.source_to_doc_ids:
                self.source_to_doc_ids = {}
                self._rebuild_source_to_doc_ids_map()
            
            print(f"成功加载向量存储，共 {len(self.documents)} 个文档")
            return True
        
        except Exception as e:
            print(f"加载向量存储失败: {str(e)}")
            return False
    
    def _rebuild_vector_store(self, exclude_indices: List[int] = None) -> bool:
        """
        重建向量存储
        
        Args:
            exclude_indices: 要排除的嵌入索引列表
            
        Returns:
            是否重建成功
        """
        try:
            # 准备保留的文档和嵌入
            if exclude_indices:
                exclude_set = set(exclude_indices)
            else:
                exclude_set = set()
            
            # 重新构建文档和嵌入映射
            new_documents = {}
            new_embeddings = []
            new_id_to_index = {}
            
            for doc_id, doc in self.documents.items():
                embedding_index = self.id_to_index.get(doc_id)
                if embedding_index is not None and embedding_index not in exclude_set:
                    new_documents[doc_id] = doc
                    new_embeddings.append(self.embeddings[embedding_index])
                    new_id_to_index[doc_id] = len(new_embeddings) - 1
            
            # 更新存储
            self.documents = new_documents
            self.embeddings = new_embeddings
            self.id_to_index = new_id_to_index
            
            # 重新创建索引
            if new_embeddings:
                dimension = len(new_embeddings[0])
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(np.array(new_embeddings))
            else:
                self.index = None
            
            # 重建源映射
            self._rebuild_source_to_doc_ids_map()
            
            # 保存更新后的索引
            self.save()
            
            return True
        
        except Exception as e:
            print(f"重建向量存储失败: {str(e)}")
            return False
    
    def _rebuild_source_to_doc_ids_map(self):
        """
        重建源到文档ID的映射
        """
        self.source_to_doc_ids = {}
        for doc_id, doc in self.documents.items():
            if "source" in doc.metadata:
                source = doc.metadata["source"]
                if source not in self.source_to_doc_ids:
                    self.source_to_doc_ids[source] = []
                if doc_id not in self.source_to_doc_ids[source]:
                    self.source_to_doc_ids[source].append(doc_id)
    
    def get_documents_by_source(self, source: str) -> List[Document]:
        """
        获取指定源的所有文档
        
        Args:
            source: 文档源
            
        Returns:
            文档列表
        """
        # 利用源映射进行快速查找
        if source in self.source_to_doc_ids:
            return [self.documents[doc_id] for doc_id in self.source_to_doc_ids[source] if doc_id in self.documents]
        return []
    
    def list_sources(self) -> List[str]:
        """
        列出所有文档源
        
        Returns:
            源列表
        """
        return list(self.source_to_doc_ids.keys())
    
    def get_source_to_documents_map(self) -> Dict[str, List[str]]:
        """
        获取源到文档ID的映射
        
        Returns:
            源到文档ID列表的映射
        """
        return self.source_to_doc_ids.copy()
    
    def clear(self) -> bool:
        """
        清空向量存储
        
        Returns:
            是否清空成功
        """
        self.index = None
        self.documents = {}
        self.embeddings = []
        self.id_to_index = {}
        self.source_to_doc_ids = {}
        
        # 如果有持久化目录，删除相关文件
        if self.persist_directory:
            try:
                files_to_delete = [
                    f"{self.index_name}.index",
                    f"{self.index_name}_documents.json",
                    f"{self.index_name}_mappings.json",
                    f"{self.index_name}_embeddings.npy"
                ]
                for filename in files_to_delete:
                    file_path = os.path.join(self.persist_directory, filename)
                    if os.path.exists(file_path):
                        os.remove(file_path)
            except Exception as e:
                print(f"删除持久化文件失败: {str(e)}")
        
        print("向量存储已清空")
        return True