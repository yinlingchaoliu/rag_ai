import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from .base_model import BaseModel


class DeepSeekModel(BaseModel):
    """
    DeepSeek模型实现
    """
    
    def __init__(self, model_name: str = "deepseek-chat"):
        """
        初始化DeepSeek模型
        
        Args:
            model_name: 模型名称，默认使用deepseek-chat
        """
        # 加载环境变量
        load_dotenv()
        
        # 获取API密钥和基础URL
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com")
        
        if not self.api_key:
            raise ValueError("未设置DeepSeek API密钥，请在.env文件中配置DEEPSEEK_API_KEY")
        
        self.model_name = model_name
        
        # 初始化聊天模型
        self.chat_model = ChatOpenAI(
            api_key=self.api_key,
            base_url=f"{self.base_url}/v1",
            model=self.model_name
        )
        
        super().__init__(self.model_name)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用DeepSeek模型生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他可选参数
            
        Returns:
            生成的文本响应
        """
        try:
            # 将generate请求转换为chat格式
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            return self.chat(messages, **kwargs)
        except Exception as e:
            raise Exception(f"DeepSeek模型生成失败: {str(e)}")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        使用DeepSeek模型进行多轮对话
        
        Args:
            messages: 消息列表，每个消息包含role和content
            **kwargs: 其他可选参数
            
        Returns:
            生成的回复文本
        """
        try:
            # 转换消息格式
            langchain_messages = []
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            
            # 生成参数处理
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1024)
            
            # 调用模型生成
            response = self.chat_model.invoke(
                langchain_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.content
        except Exception as e:
            raise Exception(f"DeepSeek模型对话失败: {str(e)}")