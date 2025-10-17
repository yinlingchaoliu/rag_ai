import os
import uuid
from typing import List, Dict, Any, Optional, Union
from document_loaders import DocumentLoaderFactory, loader_factory
from vector_stores import VectorStoreFactory, vector_store_factory
from models.model_manager import ModelManager


class RAGManager:
    """
    RAG（检索增强生成）管理器，集成文档加载、向量存储和模型调用功能
    """
    
    def __init__(self, 
                 embedding_model=None, 
                 model_manager: Optional[ModelManager] = None,
                 vector_store_type: str = "faiss",
                 vector_store_params: Optional[Dict[str, Any]] = None):
        """
        初始化RAG管理器
        
        Args:
            embedding_model: 嵌入模型
            model_manager: 模型管理器
            vector_store_type: 向量存储类型
            vector_store_params: 向量存储参数
        """
        self.embedding_model = embedding_model
        self.model_manager = model_manager
        
        # 设置默认向量存储参数
        if vector_store_params is None:
            vector_store_params = {}
        
        # 创建向量存储
        self.vector_store = vector_store_factory.create_vector_store(
            vector_store_type,
            embedding_model=embedding_model,
            **vector_store_params
        )
    
    def load_document(self, path: str, **kwargs) -> List[str]:
        """
        加载单个文档
        
        Args:
            path: 文件路径或URL
            **kwargs: 传递给文档加载器的参数
            
        Returns:
            添加的文档ID列表
        """
        # 选择合适的加载器
        loader = self._select_loader(path)
        if not loader:
            raise ValueError(f"无法找到适合路径的加载器: {path}")
        
        # 加载文档
        documents = loader.load(path, **kwargs)
        
        # 添加到向量存储
        return self.vector_store.add_documents(documents)
    
    def load_directory(self, directory: str = "./asset", recursive: bool = True, **kwargs) -> List[str]:
        """
        加载目录中的所有文档
        
        Args:
            directory: 目录路径，默认为项目的asset目录
            recursive: 是否递归加载子目录
            **kwargs: 传递给文档加载器的参数
            
        Returns:
            添加的文档ID列表
        """
        # 如果使用默认路径，确保它是绝对路径
        if directory == "./asset":
            directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "asset")
        
        # 确保目录存在
        if not os.path.exists(directory):
            raise ValueError(f"目录不存在: {directory}")
        
        # 收集所有文件
        all_files = []
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    all_files.append(os.path.join(root, file))
        else:
            all_files = [os.path.join(directory, f) for f in os.listdir(directory) 
                         if os.path.isfile(os.path.join(directory, f))]
        
        # 加载所有文件
        all_doc_ids = []
        for file_path in all_files:
            try:
                doc_ids = self.load_document(file_path, **kwargs)
                all_doc_ids.extend(doc_ids)
            except Exception as e:
                print(f"加载文件失败 {file_path}: {str(e)}")
        
        return all_doc_ids
    
    def query(self, question: str, k: int = 3) -> Dict[str, Any]:
        """
        基于知识库回答问题
        
        Args:
            question: 问题
            k: 检索的文档数量
            model_name: 使用的模型名称
            
        Returns:
            包含回答和源引用的字典
        """
        # 检索相关文档
        search_results = self.vector_store.search(question, k=k)
        
        # 构建上下文
        context = ""
        sources = []
        
        for i, result in enumerate(search_results):
            doc = result["document"]
            context += f"\n[{i+1}] {doc.content}\n"
            
            # 提取源信息
            source = doc.metadata.get("source", "未知来源")
            chunk_info = f"（块 {doc.chunk_id}）" if doc.chunk_id else ""
            
            # 避免重复添加相同的源
            source_entry = f"{source}{chunk_info}"
            if source_entry not in sources:
                sources.append(source_entry)
        
        # 构建提示词
        prompt = f"""你是一个知识渊博的助手，基于以下提供的信息回答用户问题。

如果信息中包含相关内容，请以自然、友好的语言回答，并确保回答准确、全面。
如果信息中没有相关内容，请直接说"根据提供的信息，我无法回答这个问题"，不要编造内容。

[上下文信息]
{context}

[用户问题]
{question}

[回答]
"""
        
        # 调用模型生成回答
        if self.model_manager:
            response = self.model_manager.generate(prompt)
        else:
            # 如果没有模型管理器，使用简单的回答
            response = "这是一个示例回答。请提供模型管理器以获得基于上下文的真实回答。"
        
        # 格式化源引用
        formatted_sources = []
        for i, source in enumerate(sources, 1):
            formatted_sources.append(f"[{i}] {source}")
        
        return {
            "answer": response,
            "sources": formatted_sources,
            "contexts": [result["document"].content for result in search_results]
        }
    
    def delete_document(self, document_id: str) -> bool:
        """
        删除单个文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            是否删除成功
        """
        return self.vector_store.delete([document_id])
    
    def delete_by_source(self, source: str) -> bool:
        """
        根据源删除文档
        
        Args:
            source: 文档源（文件路径或URL）
            
        Returns:
            是否删除成功
        """
        return self.vector_store.delete_by_source(source)
    
    def update_document(self, document_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新文档
        
        Args:
            document_id: 文档ID
            content: 新的内容
            metadata: 新的元数据
            
        Returns:
            是否更新成功
        """
        # 获取现有文档
        existing_doc = self.vector_store.get_document_by_id(document_id)
        if not existing_doc:
            return False
        
        # 创建新文档对象
        from document_loaders.base import Document
        new_doc = Document(
            id=document_id,
            content=content,
            metadata=metadata if metadata else existing_doc.metadata,
            chunk_id=existing_doc.chunk_id
        )
        
        # 更新文档
        return self.vector_store.update_document(document_id, new_doc)
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档信息字典，如果不存在则返回None
        """
        doc = self.vector_store.get_document_by_id(document_id)
        if doc:
            return {
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
                "chunk_id": doc.chunk_id
            }
        return None
    
    def list_documents(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有文档或指定源的文档
        
        Args:
            source: 可选，指定文档源
            
        Returns:
            文档信息列表
        """
        docs = self.vector_store.list_documents(source)
        return [
            {
                "id": doc.id,
                "content": doc.content,
                "metadata": doc.metadata,
                "chunk_id": doc.chunk_id
            }
            for doc in docs
        ]
    
    def change_vector_store(self, vector_store_type: str, vector_store_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        切换向量存储类型
        
        Args:
            vector_store_type: 向量存储类型
            vector_store_params: 向量存储参数
            
        Returns:
            是否切换成功
        """
        try:
            # 设置默认参数
            if vector_store_params is None:
                vector_store_params = {}
            
            # 创建新的向量存储
            new_vector_store = vector_store_factory.create_vector_store(
                vector_store_type,
                embedding_model=self.embedding_model,
                **vector_store_params
            )
            
            # 替换向量存储
            self.vector_store = new_vector_store
            return True
        except Exception as e:
            print(f"切换向量存储失败: {str(e)}")
            return False
    
    def _select_loader(self, path: str) -> Optional[Any]:
        """
        根据路径选择合适的加载器
        
        Args:
            path: 文件路径或URL
            
        Returns:
            文档加载器实例
        """
        # 使用loader_factory.create_loader创建适合该路径的加载器实例
        return loader_factory.create_loader(path)


# 创建一个全局的RAG管理器实例（可选）
_rag_manager = None

def get_rag_manager(**kwargs) -> RAGManager:
    """
    获取全局RAG管理器实例
    
    Args:
        **kwargs: RAGManager初始化参数
        
    Returns:
        RAGManager实例
    """
    global _rag_manager
    if _rag_manager is None:
        _rag_manager = RAGManager(**kwargs)
    return _rag_manager


# 导出公共接口
__all__ = ['RAGManager', 'get_rag_manager']