from typing import Dict, Any, Optional, List
from .base_model import BaseModel
from .ollama_model import OllamaModel
from .openai_model import OpenAIModel
from .deepseek_model import DeepSeekModel
import os

class ModelManager:
    """
    模型管理器，用于管理和切换不同的模型
    """
    
    def __init__(self):
        """
        初始化模型管理器
        """
        # 注册的模型实例
        self.models: Dict[str, BaseModel] = {}
        # 默认模型名称
        self.default_model_name = None
        # 当前使用的模型
        self.current_model: Optional[BaseModel] = None
    
    def register_model(self, model_name: str, model: BaseModel) -> "ModelManager":
        """
        注册一个新模型
        
        Args:
            model_name: 模型名称（用于引用）
            model: 模型实例
            
        Returns:
            模型管理器实例，支持链式调用
        """
        if not isinstance(model, BaseModel):
            raise TypeError("注册的模型必须是BaseModel的子类")
        
        self.models[model_name] = model
        return self
    
    def register_default_models(self) -> "ModelManager":
        """
        注册默认的模型实现
        
        Returns:
            模型管理器实例，支持链式调用
        """
        try:
            # 注册Ollama本地模型
            self.register_model("ollama", OllamaModel())
        except Exception as e:
            print(f"注册Ollama模型失败: {str(e)}")
        
        try:
            # 尝试注册OpenAI模型（如果配置了API密钥）
            self.register_model("openai", OpenAIModel())
        except Exception as e:
            print(f"注册OpenAI模型失败: {str(e)}")
        
        try:
            # 尝试注册DeepSeek模型（如果配置了API密钥）
            self.register_model("deepseek", DeepSeekModel())
        except Exception as e:
            print(f"注册DeepSeek模型失败: {str(e)}")
        
        if not self.models:
            raise RuntimeError("未成功注册任何模型")
        
        self.default_model_name = os.getenv("DEFAULT_MODEL", "ollama")
        
        if self.default_model_name in self.models:
            print(f"切换到默认模型 {self.default_model_name} ")
            self.set_current_model(self.default_model_name)
        else:
            # 默认选择第一个成功注册的模型
            first_model_name = next(iter(self.models))
            self.set_current_model(first_model_name)
        
        return self
    
    def set_current_model(self, model_name: str) -> "ModelManager":
        """
        设置当前使用的模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            模型管理器实例，支持链式调用
        """
        if model_name not in self.models:
            raise ValueError(f"未找到模型: {model_name}")
        
        self.current_model = self.models[model_name]
        print(f"已切换到模型: {model_name} ({self.current_model.get_model_info()['model_type']})")
        return self
    
    def get_current_model(self) -> Optional[BaseModel]:
        """
        获取当前使用的模型
        
        Returns:
            当前模型实例
        """
        return self.current_model
    
    def get_available_models(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有可用的模型信息
        
        Returns:
            模型名称到模型信息的映射
        """
        return {
            name: model.get_model_info() 
            for name, model in self.models.items()
        }
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用当前模型生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他可选参数
            
        Returns:
            生成的文本响应
        """
        if not self.current_model:
            raise RuntimeError("未设置当前模型，请先设置模型")
        
        return self.current_model.generate(prompt, **kwargs)
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        使用当前模型进行多轮对话
        
        Args:
            messages: 消息列表，每个消息包含role和content
            **kwargs: 其他可选参数
            
        Returns:
            生成的回复文本
        """
        if not self.current_model:
            raise RuntimeError("未设置当前模型，请先设置模型")
        
        return self.current_model.chat(messages, **kwargs)