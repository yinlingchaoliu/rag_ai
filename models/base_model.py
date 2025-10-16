from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class BaseModel(ABC):
    """
    模型抽象基类，定义所有模型需要实现的通用接口
    """
    
    def __init__(self, model_name: str):
        """
        初始化模型
        
        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示
            **kwargs: 其他可选参数
            
        Returns:
            生成的文本响应
        """
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        进行多轮对话
        
        Args:
            messages: 消息列表，每个消息包含role和content
            **kwargs: 其他可选参数
            
        Returns:
            生成的回复文本
        """
        pass
    
    def get_model_info(self) -> Dict[str, str]:
        """
        获取模型信息
        
        Returns:
            包含模型信息的字典
        """
        return {
            "model_type": self.__class__.__name__,
            "model_name": self.model_name
        }