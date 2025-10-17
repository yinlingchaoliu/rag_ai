import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from .base_model import BaseModel


class OllamaModel(BaseModel):
    """
    Ollama本地模型实现
    """
    
    def __init__(self, model_name: str = None, base_url: str = None):
        """
        初始化Ollama模型
        
        Args:
            model_name: 模型名称，默认从环境变量读取
            base_url: Ollama服务地址，默认从环境变量读取
        """
        # 加载环境变量
        load_dotenv()
        
        # 使用传入的参数或环境变量中的配置
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        
        # 初始化LangChain的ChatOllama实例
        self.chat_model = ChatOllama(
            model=self.model_name,
            base_url=self.base_url
        )
        
        super().__init__(self.model_name)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        使用Ollama模型生成文本
        
        Args:
            prompt: 输入提示
            **kwargs: 其他可选参数
            
        Returns:
            生成的文本响应
        """
        try:
            # 生成参数处理
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1024)
            
            # 转换为聊天格式调用模型生成
            messages = [HumanMessage(content=prompt)]
            response = self.chat_model.invoke(
                messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content
        except Exception as e:
            raise Exception(f"Ollama模型生成失败: {str(e)}")
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        使用Ollama模型进行多轮对话
        
        Args:
            messages: 消息列表，每个消息包含role和content
            **kwargs: 其他可选参数
            
        Returns:
            生成的回复文本
        """
        try:
            # 转换消息格式
            prompt = ""
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "system":
                    prompt += f"[INST] <<SYS>>\n{content}\n<</SYS>>\n"
                elif role == "user":
                    prompt += f"{content} [/INST] "
                elif role == "assistant":
                    prompt += f"{content}\n"
            
            # 生成参数处理
            temperature = kwargs.get("temperature", 0.7)
            max_tokens = kwargs.get("max_tokens", 1024)
            
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
            
            # 调用模型生成
            response = self.chat_model.invoke(
                langchain_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.content
        except Exception as e:
            raise Exception(f"Ollama模型对话失败: {str(e)}")