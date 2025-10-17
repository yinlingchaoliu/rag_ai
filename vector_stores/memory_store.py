import numpy as np
from typing import List, Dict, Any, Optional
from vector_stores.base import BaseVectorStore
from document_loaders.base import Document


class MemoryVectorStore(BaseVectorStore):
    """
    简单的内存向量存储实现，用于演示和测试
    不依赖外部向量数据库，所有数据存储在内存中
    """
    
    def __init__(self, embedding_model=None, persist_directory: str = None, **kwargs):
        """
        初始化内存向量存储
        
        Args:
            embedding_model: 嵌入模型
            persist_directory: 持久化目录
            **kwargs: 其他参数
        """
        super().__init__(embedding_model, persist_directory)
        self.documents = []  # 存储Document对象
        self.embeddings = []  # 存储向量嵌入
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: Document对象列表
            
        Returns:
            添加的文档ID列表
        """
        doc_ids = []
        
        for doc in documents:
            # 存储文档
            self.documents.append(doc)
            doc_ids.append(doc.id)
            
            # 创建嵌入向量
            if self.embedding_model:
                try:
                    # 尝试使用embed方法（根据基类中的create_embeddings方法）
                    embedding = self.embedding_model.embed([doc.content])[0]
                except AttributeError:
                    # 如果没有embed方法，尝试encode方法（作为备选）
                    try:
                        embedding = self.embedding_model.encode([doc.content])[0]
                    except AttributeError:
                        # 如果都没有，生成随机向量（仅用于演示）
                        embedding = np.random.rand(768).tolist()
            else:
                # 如果没有嵌入模型，生成随机向量（仅用于演示）
                embedding = np.random.rand(768).tolist()
            
            self.embeddings.append(embedding)
        
        return doc_ids
    
    def search(self, query: str, k: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 搜索查询
            k: 返回结果数量
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表，每个结果包含文档和相似度分数
        """
        if not self.embeddings:
            return []
        
        # 创建查询嵌入
        if self.embedding_model:
            try:
                query_embedding = self.embedding_model.embed([query])[0]
            except AttributeError:
                try:
                    query_embedding = self.embedding_model.encode([query])[0]
                except AttributeError:
                    query_embedding = np.random.rand(768).tolist()
        else:
            query_embedding = np.random.rand(768).tolist()
        
        # 计算相似度（余弦相似度）
        similarities = []
        for i, embedding in enumerate(self.embeddings):
            try:
                # 简单的余弦相似度计算
                dot_product = np.dot(query_embedding, embedding)
                norm_q = np.linalg.norm(query_embedding)
                norm_e = np.linalg.norm(embedding)
                if norm_q > 0 and norm_e > 0:
                    similarity = dot_product / (norm_q * norm_e)
                else:
                    similarity = 0
            except Exception:
                similarity = 0
            
            similarities.append((i, similarity))
        
        # 按相似度排序并返回结果
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = []
        
        for i, similarity in similarities[:k]:
            result = {
                'document': self.documents[i],
                'score': similarity
            }
            results.append(result)
        
        return results
    
    def delete(self, document_ids: List[str]) -> bool:
        """
        根据文档ID删除文档
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            是否删除成功
        """
        new_documents = []
        new_embeddings = []
        
        for i, doc in enumerate(self.documents):
            if doc.id not in document_ids:
                new_documents.append(doc)
                new_embeddings.append(self.embeddings[i])
        
        self.documents = new_documents
        self.embeddings = new_embeddings
        return True
    
    def delete_by_source(self, source: str) -> bool:
        """
        根据源删除文档
        
        Args:
            source: 文档源（文件路径或URL）
            
        Returns:
            是否删除成功
        """
        new_documents = []
        new_embeddings = []
        
        for i, doc in enumerate(self.documents):
            if doc.metadata.get('source') != source:
                new_documents.append(doc)
                new_embeddings.append(self.embeddings[i])
        
        self.documents = new_documents
        self.embeddings = new_embeddings
        return True
    
    def update_document(self, document_id: str, document: Document) -> bool:
        """
        更新文档
        
        Args:
            document_id: 文档ID
            document: 新的文档对象
            
        Returns:
            是否更新成功
        """
        for i, doc in enumerate(self.documents):
            if doc.id == document_id:
                # 更新文档内容
                self.documents[i] = document
                
                # 更新嵌入
                if self.embedding_model:
                    try:
                        embedding = self.embedding_model.embed([document.content])[0]
                    except AttributeError:
                        try:
                            embedding = self.embedding_model.encode([document.content])[0]
                        except AttributeError:
                            embedding = np.random.rand(768).tolist()
                else:
                    embedding = np.random.rand(768).tolist()
                
                self.embeddings[i] = embedding
                return True
        
        return False
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        根据ID获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档对象，如果不存在则返回None
        """
        for doc in self.documents:
            if doc.id == document_id:
                return doc
        
        return None
    
    def list_documents(self, source: Optional[str] = None) -> List[Document]:
        """
        列出所有文档或指定源的文档
        
        Args:
            source: 可选，指定文档源
            
        Returns:
            文档列表
        """
        if source:
            return [doc for doc in self.documents if doc.metadata.get('source') == source]
        else:
            return self.documents.copy()
    
    def save(self) -> bool:
        """
        保存向量存储（内存存储不进行实际保存）
        
        Returns:
            是否保存成功
        """
        # 对于内存存储，保存操作是可选的
        # 在实际应用中，可以实现将数据保存到文件
        return True
    
    def load(self) -> bool:
        """
        加载向量存储（内存存储不进行实际加载）
        
        Returns:
            是否加载成功
        """
        # 对于内存存储，加载操作是可选的
        # 在实际应用中，可以实现从文件加载数据
        return True
    
    @property
    def count(self) -> int:
        """
        获取文档数量
        """
        return len(self.documents)