from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """
    文档数据类，用于存储从各种来源加载的文档内容和元数据
    """
    id: str  # 文档唯一标识符
    content: str  # 文档内容
    metadata: Dict[str, Any]  # 文档元数据，如来源、创建时间等
    chunk_id: Optional[str] = None  # 块ID，用于分块后的文档


class BaseDocumentLoader(ABC):
    """
    文档加载器抽象基类，定义所有文档加载器需要实现的通用接口
    """
    
    def __init__(self):
        """
        初始化文档加载器
        """
        self.chunk_size = 1000  # 默认分块大小
        self.chunk_overlap = 100  # 默认块重叠大小
    
    @abstractmethod
    def load(self, source: str, **kwargs) -> List[Document]:
        """
        加载文档
        
        Args:
            source: 文档源，可以是文件路径或URL
            **kwargs: 其他可选参数
            
        Returns:
            加载的文档列表
        """
        pass
    
    def chunk_text(self, text: str) -> List[str]:
        """
        将文本分成多个块
        
        Args:
            text: 要分块的文本
            
        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    @staticmethod
    def get_loader_info() -> Dict[str, Any]:
        """
        获取加载器信息，包括支持的文件类型等
        
        Returns:
            加载器信息字典
        """
        return {
            "name": "BaseDocumentLoader",
            "supported_extensions": []
        }