import json
import requests
from typing import List, Dict, Any
from .base import BaseEmbeddingModel, embedding_model_factory


class OllamaEmbedding(BaseEmbeddingModel):
    """
    基于Ollama的嵌入模型实现
    """
    
    def __init__(self, model_name: str = "nomic-embed-text:latest", base_url: str = "http://localhost:11434"):
        """
        初始化Ollama嵌入模型
        
        Args:
            model_name: Ollama模型名称，默认为nomic-embed-text:latest
            base_url: Ollama API基础URL
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.embed_endpoint = f"{self.base_url}/api/embeddings"
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        生成多个文本的嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            embedding = self._get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """
        生成单个查询的嵌入向量
        
        Args:
            query: 查询文本
            
        Returns:
            嵌入向量
        """
        return self._get_embedding(query)
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        从Ollama获取单个文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量
            
        Raises:
            RuntimeError: API调用失败
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        try:
            response = requests.post(
                self.embed_endpoint,
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API调用失败: {response.status_code}, {response.text}")
            
            result = response.json()
            if "embedding" not in result:
                raise RuntimeError(f"Ollama API返回格式错误: {result}")
            
            return result["embedding"]
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"与Ollama服务器通信失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析Ollama API响应失败: {str(e)}")
    
    def get_name(self) -> str:
        """
        获取模型名称
        
        Returns:
            模型名称
        """
        return f"ollama-{self.model_name}"
    
    def test_connection(self) -> bool:
        """
        测试与Ollama服务器的连接
        
        Returns:
            连接是否成功
        """
        try:
            # 使用一个简单的文本进行测试
            self._get_embedding("test connection")
            return True
        except Exception:
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            配置字典
        """
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "endpoint": self.embed_endpoint
        }


# 注册Ollama嵌入模型到工厂
embedding_model_factory.register_model("ollama", OllamaEmbedding)