import os
import hashlib
from typing import List, Dict, Any, Optional
from .base import BaseDocumentLoader, Document


class TextFileLoader(BaseDocumentLoader):
    """
    文本文件加载器，用于加载.txt、.md等文本文件并分块处理
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        初始化文本文件加载器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 块重叠大小
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load(self, source: str, **kwargs) -> List[Document]:
        """
        加载文本文件
        
        Args:
            source: 文本文件路径
            **kwargs: 其他可选参数
                encoding: 文件编码，默认为utf-8
            
        Returns:
            加载的文档列表
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件类型错误
        """
        # 检查文件是否存在
        if not os.path.exists(source):
            raise FileNotFoundError(f"文件不存在: {source}")
        
        # 检查文件类型
        supported_extensions = ['.txt', '.md', '.markdown', '.csv', '.log']
        if not any(source.lower().endswith(ext) for ext in supported_extensions):
            # 对于未明确指定支持的扩展名，尝试作为文本文件打开
            print(f"警告: 文件类型 {os.path.splitext(source)[1]} 未明确支持，尝试作为文本文件打开")
        
        # 设置分块参数（如果提供）
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        chunk_overlap = kwargs.get('chunk_overlap', self.chunk_overlap)
        encoding = kwargs.get('encoding', 'utf-8')
        
        # 临时保存原始分块参数
        original_chunk_size = self.chunk_size
        original_chunk_overlap = self.chunk_overlap
        
        # 更新分块参数
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            # 打开并读取文本文件
            with open(source, 'r', encoding=encoding) as file:
                text = file.read()
            
            # 生成文档ID
            doc_id = hashlib.md5(source.encode()).hexdigest()
            
            # 分块文本
            chunks = self.chunk_text(text)
            
            # 创建文档列表
            documents = []
            for i, chunk in enumerate(chunks):
                # 为每个块生成唯一ID
                chunk_id = f"{doc_id}_chunk_{i}"
                
                # 确定文件类型
                file_ext = os.path.splitext(source)[1].lower()
                file_type = "markdown" if file_ext in ['.md', '.markdown'] else "text"
                
                # 创建文档对象
                document = Document(
                    id=chunk_id,
                    content=chunk,
                    metadata={
                        "source": source,
                        "file_name": os.path.basename(source),
                        "file_type": file_type,
                        "encoding": encoding,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "file_extension": file_ext
                    },
                    chunk_id=chunk_id
                )
                documents.append(document)
            
            return documents
        
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(source, 'r', encoding='gbk') as file:
                    text = file.read()
                
                # 继续处理...
                doc_id = hashlib.md5(source.encode()).hexdigest()
                chunks = self.chunk_text(text)
                documents = []
                
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    file_ext = os.path.splitext(source)[1].lower()
                    file_type = "markdown" if file_ext in ['.md', '.markdown'] else "text"
                    
                    document = Document(
                        id=chunk_id,
                        content=chunk,
                        metadata={
                            "source": source,
                            "file_name": os.path.basename(source),
                            "file_type": file_type,
                            "encoding": 'gbk',
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "file_extension": file_ext
                        },
                        chunk_id=chunk_id
                    )
                    documents.append(document)
                
                return documents
            except Exception as e:
                raise ValueError(f"无法解码文件 {source}: {str(e)}")
        
        finally:
            # 恢复原始分块参数
            self.chunk_size = original_chunk_size
            self.chunk_overlap = original_chunk_overlap
    
    @staticmethod
    def get_loader_info() -> Dict[str, Any]:
        """
        获取加载器信息
        
        Returns:
            加载器信息字典
        """
        return {
            "name": "TextFileLoader",
            "supported_extensions": [".txt", ".md", ".markdown", ".csv", ".log"]
        }