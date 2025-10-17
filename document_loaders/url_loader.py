import os
import hashlib
import re
import requests
from typing import List, Dict, Any, Optional
from .base import BaseDocumentLoader, Document
from bs4 import BeautifulSoup


class URLLoader(BaseDocumentLoader):
    """
    URL加载器，用于从网络加载文档并分块处理
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100, timeout: int = 10):
        """
        初始化URL加载器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 块重叠大小
            timeout: 请求超时时间（秒）
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.timeout = timeout
    
    def load(self, source: str, **kwargs) -> List[Document]:
        """
        从URL加载文档
        
        Args:
            source: URL地址
            **kwargs: 其他可选参数
                timeout: 请求超时时间
                headers: 请求头
            
        Returns:
            加载的文档列表
            
        Raises:
            ValueError: URL格式错误
            requests.exceptions.RequestException: 请求失败
        """
        # 验证URL格式
        if not self._is_valid_url(source):
            raise ValueError(f"无效的URL格式: {source}")
        
        # 设置参数
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        chunk_overlap = kwargs.get('chunk_overlap', self.chunk_overlap)
        timeout = kwargs.get('timeout', self.timeout)
        headers = kwargs.get('headers', {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 临时保存原始分块参数
        original_chunk_size = self.chunk_size
        original_chunk_overlap = self.chunk_overlap
        
        # 更新分块参数
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            # 发送请求
            response = requests.get(source, headers=headers, timeout=timeout)
            response.raise_for_status()  # 如果状态码不是200，抛出异常
            
            # 根据内容类型解析
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'text/html' in content_type:
                # 处理HTML内容
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 移除脚本和样式标签
                for script in soup(['script', 'style']):
                    script.decompose()
                
                # 提取文本
                text = soup.get_text(separator='\n', strip=True)
                
                # 清理文本
                text = self._clean_text(text)
            
            elif 'text/plain' in content_type:
                # 处理纯文本
                text = response.text
            
            else:
                # 对于其他类型，尝试提取文本
                text = f"URL: {source}\nContent-Type: {content_type}\n\n无法直接提取内容，请下载后查看。"
            
            # 生成文档ID
            doc_id = hashlib.md5(source.encode()).hexdigest()
            
            # 分块文本
            chunks = self.chunk_text(text)
            
            # 创建文档列表
            documents = []
            for i, chunk in enumerate(chunks):
                # 为每个块生成唯一ID
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # 创建文档对象
                document = Document(
                    id=chunk_id,
                    content=chunk,
                    metadata={
                        "source": source,
                        "file_name": self._extract_filename_from_url(source),
                        "file_type": "url",
                        "content_type": content_type,
                        "response_status": response.status_code,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    },
                    chunk_id=chunk_id
                )
                documents.append(document)
            
            return documents
        
        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException(f"请求URL失败: {source}. 错误: {str(e)}")
        
        finally:
            # 恢复原始分块参数
            self.chunk_size = original_chunk_size
            self.chunk_overlap = original_chunk_overlap
    
    def _is_valid_url(self, url: str) -> bool:
        """
        验证URL格式是否有效
        
        Args:
            url: 要验证的URL
            
        Returns:
            URL是否有效
        """
        url_pattern = re.compile(r'^(https?://|www\.)[^\s/$.?#].[^\s]*$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    def _clean_text(self, text: str) -> str:
        """
        清理文本，移除多余的空白字符和特殊字符
        
        Args:
            text: 要清理的文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符（保留基本标点符号）
        text = re.sub(r'[^\w\s,.!?-]', '', text)
        # 去除首尾空白
        return text.strip()
    
    def _extract_filename_from_url(self, url: str) -> str:
        """
        从URL中提取文件名
        
        Args:
            url: URL地址
            
        Returns:
            提取的文件名
        """
        # 移除URL参数
        url = url.split('?')[0]
        url = url.split('#')[0]
        
        # 提取最后一部分作为文件名
        filename = os.path.basename(url)
        
        # 如果没有文件名，使用域名
        if not filename:
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            filename = parsed_url.netloc.replace('.', '_')
        
        return filename
    
    @staticmethod
    def get_loader_info() -> Dict[str, Any]:
        """
        获取加载器信息
        
        Returns:
            加载器信息字典
        """
        return {
            "name": "URLLoader",
            "supported_extensions": ["http", "https", "www"]
        }