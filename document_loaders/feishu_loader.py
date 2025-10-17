import os
import hashlib
import time
import requests
from typing import List, Dict, Any, Optional
from .base import BaseDocumentLoader, Document


class FeishuLoader(BaseDocumentLoader):
    """
    飞书文档加载器，用于加载飞书文档并分块处理
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        初始化飞书文档加载器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 块重叠大小
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # 从环境变量获取飞书配置
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        
        if not self.app_id or not self.app_secret:
            print("警告: 未设置FEISHU_APP_ID或FEISHU_APP_SECRET环境变量，将无法加载飞书文档")
        
        # 飞书API基础URL
        self.api_base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        self.token_expire_time = 0
    
    def _get_access_token(self) -> str:
        """
        获取飞书访问令牌
        
        Returns:
            访问令牌
            
        Raises:
            ValueError: 缺少必要的配置
            requests.exceptions.RequestException: 请求失败
        """
        # 检查是否已配置
        if not self.app_id or not self.app_secret:
            raise ValueError("未配置飞书App ID或App Secret")
        
        # 检查令牌是否有效
        if self.access_token and time.time() < self.token_expire_time:
            return self.access_token
        
        # 请求新令牌
        url = f"{self.api_base_url}/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if result.get("code") != 0:
            raise ValueError(f"获取飞书访问令牌失败: {result.get('msg')}")
        
        self.access_token = result.get("tenant_access_token")
        # 设置过期时间（提前10分钟过期）
        expire_in = result.get("expire", 7200)
        self.token_expire_time = time.time() + expire_in - 600
        
        return self.access_token
    
    def load(self, source: str, **kwargs) -> List[Document]:
        """
        加载飞书文档
        
        Args:
            source: 飞书文档链接或文档ID
            **kwargs: 其他可选参数
                chunk_size: 分块大小
                chunk_overlap: 块重叠大小
            
        Returns:
            加载的文档列表
            
        Raises:
            ValueError: 参数错误
            requests.exceptions.RequestException: 请求失败
        """
        # 提取文档ID
        document_id = self._extract_document_id(source)
        
        # 设置分块参数
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        chunk_overlap = kwargs.get('chunk_overlap', self.chunk_overlap)
        
        # 临时保存原始分块参数
        original_chunk_size = self.chunk_size
        original_chunk_overlap = self.chunk_overlap
        
        # 更新分块参数
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            # 获取访问令牌
            access_token = self._get_access_token()
            
            # 导出文档为TXT
            export_url = f"{self.api_base_url}/docx/v1/documents/{document_id}/export"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=utf-8"
            }
            data = {
                "type": "txt"
            }
            
            response = requests.post(export_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") != 0:
                raise ValueError(f"导出飞书文档失败: {result.get('msg')}")
            
            # 获取任务ID
            task_id = result.get("data", {}).get("task_id")
            if not task_id:
                raise ValueError("未获取到导出任务ID")
            
            # 轮询任务状态
            file_token = None
            max_retries = 30
            retry_interval = 2  # 秒
            
            for i in range(max_retries):
                status_url = f"{self.api_base_url}/docx/v1/documents/{document_id}/export/{task_id}"
                status_response = requests.get(status_url, headers=headers)
                status_response.raise_for_status()
                
                status_result = status_response.json()
                if status_result.get("code") != 0:
                    raise ValueError(f"查询导出任务状态失败: {status_result.get('msg')}")
                
                status = status_result.get("data", {}).get("status")
                if status == "done":
                    file_token = status_result.get("data", {}).get("file_token")
                    break
                elif status == "failed":
                    raise ValueError("飞书文档导出失败")
                
                time.sleep(retry_interval)
            
            if not file_token:
                raise TimeoutError("飞书文档导出超时")
            
            # 下载文件
            download_url = f"{self.api_base_url}/drive/v1/files/{file_token}/download"
            download_response = requests.get(download_url, headers=headers, stream=True)
            download_response.raise_for_status()
            
            # 读取文件内容
            text = download_response.content.decode('utf-8')
            
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
                        "file_name": f"feishu_{document_id}",
                        "file_type": "feishu",
                        "document_id": document_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    },
                    chunk_id=chunk_id
                )
                documents.append(document)
            
            return documents
        
        finally:
            # 恢复原始分块参数
            self.chunk_size = original_chunk_size
            self.chunk_overlap = original_chunk_overlap
    
    def _extract_document_id(self, source: str) -> str:
        """
        从飞书文档链接中提取文档ID
        
        Args:
            source: 飞书文档链接或文档ID
            
        Returns:
            文档ID
            
        Raises:
            ValueError: 无法提取文档ID
        """
        # 如果已经是文档ID，直接返回
        if re.match(r'^[a-zA-Z0-9]+$', source) and len(source) > 10:
            return source
        
        # 从URL中提取文档ID
        patterns = [
            r'https://.*\.feishu\.cn/docs/([a-zA-Z0-9]+)',
            r'docs/([a-zA-Z0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                return match.group(1)
        
        raise ValueError(f"无法从链接中提取飞书文档ID: {source}")
    
    @staticmethod
    def get_loader_info() -> Dict[str, Any]:
        """
        获取加载器信息
        
        Returns:
            加载器信息字典
        """
        return {
            "name": "FeishuLoader",
            "supported_extensions": ["feishu", "https://*.feishu.cn"]
        }

# 需要导入re模块
import re