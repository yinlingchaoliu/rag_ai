from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np


class BaseEmbeddingModel(ABC):
    """
    嵌入模型抽象基类，定义所有嵌入模型需要实现的通用接口
    """
    
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        生成文本嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """
        生成单个查询的嵌入向量
        
        Args:
            query: 查询文本
            
        Returns:
            嵌入向量
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取模型名称
        
        Returns:
            模型名称
        """
        pass


class EmbeddingModelFactory:
    """
    嵌入模型工厂类，用于创建不同类型的嵌入模型
    """
    
    def __init__(self):
        """
        初始化嵌入模型工厂
        """
        self._models: Dict[str, type] = {}
    
    def register_model(self, name: str, model_class: type) -> "EmbeddingModelFactory":
        """
        注册一个嵌入模型实现
        
        Args:
            name: 模型名称
            model_class: 模型类
            
        Returns:
            工厂实例，支持链式调用
        """
        if not issubclass(model_class, BaseEmbeddingModel):
            raise TypeError(f"嵌入模型必须是BaseEmbeddingModel的子类: {model_class.__name__}")
        
        self._models[name] = model_class
        return self
    
    def create_model(self, name: str, **kwargs) -> BaseEmbeddingModel:
        """
        创建嵌入模型实例
        
        Args:
            name: 模型名称
            **kwargs: 模型初始化参数
            
        Returns:
            嵌入模型实例
            
        Raises:
            ValueError: 未找到指定的模型
        """
        if name not in self._models:
            raise ValueError(f"未找到嵌入模型: {name}")
        
        return self._models[name](**kwargs)
    
    def create(self, name: str, **kwargs) -> BaseEmbeddingModel:
        """
        创建嵌入模型实例（create_model 的别名）
        
        Args:
            name: 模型名称
            **kwargs: 模型初始化参数
            
        Returns:
            嵌入模型实例
            
        Raises:
            ValueError: 未找到指定的模型
        """
        return self.create_model(name, **kwargs)
    
    def get_available_models(self) -> List[str]:
        """
        获取所有可用的模型名称
        
        Returns:
            模型名称列表
        """
        return list(self._models.keys())


# 创建全局嵌入模型工厂实例
embedding_model_factory = EmbeddingModelFactory()