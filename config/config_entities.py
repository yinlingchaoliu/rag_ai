#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置实体类定义
使用Pydantic进行数据验证和类型提示
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class LLMConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=()  # 禁用保护命名空间检查
    )
    """
    LLM模型配置
    """
    model_type: str = "ollama"  # 可选: ollama, deepseek
    model_name: str = "qwen2:1.5b"  # 模型名称
    base_url: str = "http://127.0.0.1:11434"  # API基础URL
    temperature: float = 0.1  # 生成温度
    max_tokens: int = 2048  # 最大生成token数
    api_key: Optional[str] = None  # API密钥
    deepseek_api_key: Optional[str] = None  # API密钥
    deepseek_api_base_url: Optional[str] = None  # API基础地址


class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=()  # 禁用保护命名空间检查
    )
    """
    嵌入模型配置
    """
    model_type: str = "ollama"  # 可选: ollama
    model_name: str = "nomic-embed-text:latest"  # 嵌入模型名称
    dimension: int = 4096  # 嵌入维度
    base_url: str = "http://127.0.0.1:11434"  # API基础URL


class FAISSConfig(BaseModel):
    """
    FAISS向量存储配置
    """
    vector_store_dir: str = "db/vector_store"  # 向量存储目录
    index_file: str = "faiss_index.index"  # 索引文件名
    docs_file: str = "faiss_index_documents.json"  # 文档文件名
    mappings_file: str = "faiss_index_mappings.json"  # 映射文件名
    embeddings_file: str = "faiss_index_embeddings.json"  # 嵌入向量文件名


class RAGConfig(BaseModel):
    """
    RAG系统配置
    """
    search_top_k: int = 5  # 搜索时返回的文档数量
    similarity_threshold: float = 0.0  # 相似度阈值
    query_expansion: bool = False  # 是否启用查询扩展


class DocumentConfig(BaseModel):
    """
    文档处理配置
    """
    chunk_size: int = 1000  # 文档分块大小
    chunk_overlap: int = 100  # 文档块重叠大小


class LoggingConfig(BaseModel):
    """
    日志配置
    """
    log_level: str = "INFO"  # 日志级别: DEBUG, INFO, WARNING, ERROR
    log_file: str = "logs/rag_system.log"  # 日志文件路径


class AppConfig(BaseModel):
    """
    应用程序完整配置
    """
    llm: LLMConfig = LLMConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    faiss: FAISSConfig = FAISSConfig()
    rag: RAGConfig = RAGConfig()
    document: DocumentConfig = DocumentConfig()
    logging: LoggingConfig = LoggingConfig()