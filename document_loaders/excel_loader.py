import os
import hashlib
from typing import List, Dict, Any, Optional
from .base import BaseDocumentLoader, Document
import pandas as pd


class ExcelFileLoader(BaseDocumentLoader):
    """
    Excel文件加载器，用于加载.xlsx和.xls文件并分块处理
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        """
        初始化Excel文件加载器
        
        Args:
            chunk_size: 分块大小
            chunk_overlap: 块重叠大小
        """
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load(self, source: str, **kwargs) -> List[Document]:
        """
        加载Excel文件
        
        Args:
            source: Excel文件路径
            **kwargs: 其他可选参数
                sheet_name: 要加载的工作表名称或索引，默认为所有工作表
            
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
        if not (source.lower().endswith('.xlsx') or source.lower().endswith('.xls')):
            raise ValueError(f"不支持的文件类型，需要Excel文件: {source}")
        
        # 设置分块参数（如果提供）
        chunk_size = kwargs.get('chunk_size', self.chunk_size)
        chunk_overlap = kwargs.get('chunk_overlap', self.chunk_overlap)
        sheet_name = kwargs.get('sheet_name', None)  # None表示所有工作表
        
        # 临时保存原始分块参数
        original_chunk_size = self.chunk_size
        original_chunk_overlap = self.chunk_overlap
        
        # 更新分块参数
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            # 读取Excel文件
            excel_file = pd.ExcelFile(source)
            
            # 确定要处理的工作表
            if sheet_name is None:
                sheet_names = excel_file.sheet_names
            elif isinstance(sheet_name, (list, tuple)):
                sheet_names = [name for name in sheet_name if name in excel_file.sheet_names]
            elif sheet_name in excel_file.sheet_names or isinstance(sheet_name, int):
                sheet_names = [sheet_name]
            else:
                raise ValueError(f"工作表 '{sheet_name}' 不存在")
            
            # 生成文档ID
            base_doc_id = hashlib.md5(source.encode()).hexdigest()
            
            documents = []
            chunk_index = 0
            
            # 处理每个工作表
            for sheet_idx, sheet in enumerate(sheet_names):
                # 读取工作表数据
                df = pd.read_excel(source, sheet_name=sheet)
                
                # 将DataFrame转换为文本
                sheet_text = f"\n\n--- 工作表: {sheet} ---\n\n"
                
                # 添加列名
                sheet_text += "列名: " + ", ".join(df.columns.tolist()) + "\n\n"
                
                # 添加数据行
                for idx, row in df.iterrows():
                    row_text = f"第 {idx + 1} 行: "
                    for col in df.columns:
                        row_text += f"{col}: {row[col]}, "
                    sheet_text += row_text[:-2] + "\n"
                
                # 添加工作表统计信息
                sheet_text += f"\n统计信息: {len(df)} 行, {len(df.columns)} 列\n"
                
                # 分块文本
                chunks = self.chunk_text(sheet_text)
                
                # 创建文档列表
                for i, chunk in enumerate(chunks):
                    # 为每个块生成唯一ID
                    chunk_id = f"{base_doc_id}_sheet_{sheet_idx}_chunk_{i}"
                    
                    # 创建文档对象
                    document = Document(
                        id=chunk_id,
                        content=chunk,
                        metadata={
                            "source": source,
                            "file_name": os.path.basename(source),
                            "file_type": "excel",
                            "sheet_name": str(sheet),
                            "row_count": len(df),
                            "column_count": len(df.columns),
                            "chunk_index": chunk_index,
                            "total_chunks": len(chunks),
                            "sheet_index": sheet_idx
                        },
                        chunk_id=chunk_id
                    )
                    documents.append(document)
                    chunk_index += 1
            
            return documents
        
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
            "name": "ExcelFileLoader",
            "supported_extensions": [".xlsx", ".xls"]
        }