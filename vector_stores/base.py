from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from document_loaders.base import Document
import numpy as np


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
        
        # 这里假设embedding_model有embed方法
        embeddings = self.embedding_model.embed(texts)
        return np.array(embeddings)


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
    
    def get_available_vector_stores(self) -> List[str]:
        """
        获取所有可用的向量存储名称
        
        Returns:
            向量存储名称列表
        """
        return list(self._vector_stores.keys())

# 创建全局向量存储工厂实例
vector_store_factory = VectorStoreFactory()