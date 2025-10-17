from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from document_loaders.base import Document
import numpy as np
from embedding.base import BaseEmbeddingModel


class BaseVectorStore(ABC):
    """
    向量存储抽象基类，定义所有向量存储需要实现的通用接口
    """
    
    def __init__(self, embedding_model=None, persist_directory: str = None):
        """
        初始化向量存储
        
        Args:
            embedding_model: 嵌入模型，用于将文本转换为向量
            persist_directory: 持久化目录，用于保存向量存储
        """
        self.embedding_model = embedding_model
        self.persist_directory = persist_directory
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            添加的文档ID列表
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def delete(self, document_ids: List[str]) -> bool:
        """
        根据文档ID删除文档
        
        Args:
            document_ids: 文档ID列表
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def delete_by_source(self, source: str) -> bool:
        """
        根据源删除文档
        
        Args:
            source: 文档源（文件路径或URL）
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def update_document(self, document_id: str, document: Document) -> bool:
        """
        更新文档
        
        Args:
            document_id: 文档ID
            document: 新的文档对象
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """
        根据ID获取文档
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_documents(self, source: Optional[str] = None) -> List[Document]:
        """
        列出所有文档或指定源的文档
        
        Args:
            source: 可选，指定文档源
            
        Returns:
            文档列表
        """
        pass
    
    @abstractmethod
    def save(self) -> bool:
        """
        保存向量存储
        
        Returns:
            是否保存成功
        """
        pass
    
    @abstractmethod
    def load(self) -> bool:
        """
        加载向量存储
        
        Returns:
            是否加载成功
        """
        pass
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        创建文本嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量数组
        """
        if not self.embedding_model:
            raise ValueError("未设置嵌入模型")
        
        try:
            # 优先使用embed方法（BaseEmbeddingModel接口）
            if hasattr(self.embedding_model, 'embed'):
                embeddings = self.embedding_model.embed(texts)
            elif hasattr(self.embedding_model, 'encode'):
                # 兼容其他常见接口如encode
                embeddings = self.embedding_model.encode(texts)
            else:
                raise ValueError(f"嵌入模型不支持embed或encode方法: {self.embedding_model}")
            
            return np.array(embeddings)
        except Exception as e:
            raise RuntimeError(f"创建嵌入向量失败: {str(e)}")
    
    def create_query_embedding(self, query: str) -> np.ndarray:
        """
        创建查询嵌入
        
        Args:
            query: 查询文本
            
        Returns:
            查询嵌入向量
        """
        if not self.embedding_model:
            raise ValueError("未设置嵌入模型")
        
        try:
            # 优先使用embed_query方法（BaseEmbeddingModel接口）
            if hasattr(self.embedding_model, 'embed_query'):
                embedding = self.embedding_model.embed_query(query)
            elif hasattr(self.embedding_model, 'embed'):
                # 如果没有embed_query，使用embed替代
                embedding = self.embedding_model.embed([query])[0]
            elif hasattr(self.embedding_model, 'encode'):
                # 兼容其他常见接口如encode
                embedding = self.embedding_model.encode([query])[0]
            else:
                raise ValueError(f"嵌入模型不支持嵌入方法: {self.embedding_model}")
            
            return np.array(embedding)
        except Exception as e:
            raise RuntimeError(f"创建查询嵌入向量失败: {str(e)}")
    
    def get_source_to_documents_map(self) -> Dict[str, List[str]]:
        """
        获取源到文档ID的映射
        
        Returns:
            源到文档ID列表的映射
        """
        # 默认实现，子类可以覆盖以提供更高效的实现
        source_map = {}
        for doc in self.list_documents():
            if "source" in doc.metadata:
                source = doc.metadata["source"]
                if source not in source_map:
                    source_map[source] = []
                source_map[source].append(doc.id)
        return source_map
    
    def has_document(self, document_id: str) -> bool:
        """
        检查文档是否存在
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档是否存在
        """
        try:
            doc = self.get_document_by_id(document_id)
            return doc is not None
        except Exception:
            return False
    
    def count_documents(self) -> int:
        """
        获取文档总数
        
        Returns:
            文档数量
        """
        return len(self.list_documents())
    
    def list_sources(self) -> List[str]:
        """
        列出所有文档源
        
        Returns:
            源列表
        """
        sources = set()
        for doc in self.list_documents():
            if "source" in doc.metadata:
                sources.add(doc.metadata["source"])
        return list(sources)
    
    def get_documents_by_source(self, source: str) -> List[Document]:
        """
        获取指定源的所有文档
        
        Args:
            source: 文档源
            
        Returns:
            文档列表
        """
        return self.list_documents(source=source)


class VectorStoreFactory:
    """
    向量存储工厂类，用于创建不同类型的向量存储
    """
    
    def __init__(self):
        """
        初始化向量存储工厂
        """
        self._vector_stores: Dict[str, type] = {}
    
    def register_vector_store(self, name: str, vector_store_class: type) -> "VectorStoreFactory":
        """
        注册一个向量存储实现
        
        Args:
            name: 向量存储名称
            vector_store_class: 向量存储类
            
        Returns:
            工厂实例，支持链式调用
        """
        if not issubclass(vector_store_class, BaseVectorStore):
            raise TypeError(f"向量存储必须是BaseVectorStore的子类: {vector_store_class.__name__}")
        
        self._vector_stores[name] = vector_store_class
        return self
    
    def create_vector_store(self, name: str, **kwargs) -> BaseVectorStore:
        """
        创建向量存储实例
        
        Args:
            name: 向量存储名称
            **kwargs: 向量存储初始化参数
            
        Returns:
            向量存储实例
            
        Raises:
            ValueError: 未找到指定的向量存储
        """
        if name not in self._vector_stores:
            raise ValueError(f"未找到向量存储: {name}")
        
        return self._vector_stores[name](**kwargs)
    
    def create(self, name: str, **kwargs) -> BaseVectorStore:
        """
        创建向量存储实例（create_vector_store的别名方法）
        
        Args:
            name: 向量存储名称
            **kwargs: 向量存储初始化参数
            
        Returns:
            向量存储实例
            
        Raises:
            ValueError: 未找到指定的向量存储
        """
        return self.create_vector_store(name, **kwargs)
    
    def get_available_vector_stores(self) -> List[str]:
        """
        获取所有可用的向量存储名称
        
        Returns:
            向量存储名称列表
        """
        return list(self._vector_stores.keys())

# 创建全局向量存储工厂实例
vector_store_factory = VectorStoreFactory()


class VectorDatabaseManager:
    """
    向量数据库管理器，用于协调管理多个向量存储实例
    """
    
    def __init__(self):
        """
        初始化向量数据库管理器
        """
        self._vector_stores: Dict[str, BaseVectorStore] = {}
    
    def register_store(self, name: str, vector_store: BaseVectorStore) -> "VectorDatabaseManager":
        """
        注册一个向量存储实例
        
        Args:
            name: 向量存储名称
            vector_store: 向量存储实例
            
        Returns:
            管理器实例，支持链式调用
        """
        if not isinstance(vector_store, BaseVectorStore):
            raise TypeError(f"向量存储必须是BaseVectorStore的实例: {type(vector_store).__name__}")
        
        self._vector_stores[name] = vector_store
        return self
    
    def get_store(self, name: str) -> Optional[BaseVectorStore]:
        """
        获取向量存储实例
        
        Args:
            name: 向量存储名称
            
        Returns:
            向量存储实例，如果不存在则返回None
        """
        return self._vector_stores.get(name)
    
    def remove_store(self, name: str) -> bool:
        """
        移除向量存储实例
        
        Args:
            name: 向量存储名称
            
        Returns:
            是否移除成功
        """
        if name in self._vector_stores:
            del self._vector_stores[name]
            return True
        return False
    
    def list_stores(self) -> List[str]:
        """
        列出所有注册的向量存储
        
        Returns:
            向量存储名称列表
        """
        return list(self._vector_stores.keys())
    
    def search_all_stores(self, query: str, k: int = 5, **kwargs) -> Dict[str, List[Dict[str, Any]]]:
        """
        在所有向量存储中搜索
        
        Args:
            query: 搜索查询
            k: 每个存储返回的结果数量
            **kwargs: 其他搜索参数
            
        Returns:
            存储名称到搜索结果的映射
        """
        results = {}
        for name, store in self._vector_stores.items():
            try:
                store_results = store.search(query, k=k, **kwargs)
                results[name] = store_results
            except Exception as e:
                print(f"搜索存储 {name} 失败: {str(e)}")
        return results
    
    def get_all_documents(self) -> Dict[str, List[Document]]:
        """
        获取所有存储中的文档
        
        Returns:
            存储名称到文档列表的映射
        """
        all_documents = {}
        for name, store in self._vector_stores.items():
            try:
                docs = store.list_documents()
                all_documents[name] = docs
            except Exception as e:
                print(f"获取存储 {name} 的文档失败: {str(e)}")
        return all_documents
    
    def count_all_documents(self) -> Dict[str, int]:
        """
        获取所有存储中的文档数量
        
        Returns:
            存储名称到文档数量的映射
        """
        counts = {}
        for name, store in self._vector_stores.items():
            try:
                counts[name] = store.count_documents()
            except Exception as e:
                print(f"计算存储 {name} 的文档数量失败: {str(e)}")
                counts[name] = 0
        return counts


# 创建全局向量数据库管理器实例
vector_db_manager = VectorDatabaseManager()