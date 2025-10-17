#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X公司知识库RAG系统配置文件

本文件包含RAG系统的所有可配置参数
"""

import os
from pathlib import Path

# 基础配置
BASE_DIR = Path(__file__).parent

# FAISS向量存储配置
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "db", "vector_store")
VECTOR_STORE_INDEX_FILE = "faiss_index.index"
VECTOR_STORE_DOCS_FILE = "faiss_index_documents.json"
VECTOR_STORE_MAPPINGS_FILE = "faiss_index_mappings.json"
VECTOR_STORE_EMBEDDINGS_FILE = "faiss_index_embeddings.json"

# 嵌入模型配置
EMBEDDING_MODEL_TYPE = "ollama"  # 可选: ollama
EMBEDDING_MODEL_NAME = "nomic-embed-text:latest"  # 使用更通用的模型名称，更容易获取
EMBEDDING_DIMENSION = 4096  # 根据模型调整，llama3为4096
EMBEDDING_BASE_URL = "http://127.0.0.1:11434"  # Ollama API基础URL

# LLM模型配置
LLM_MODEL_TYPE = "ollama"  # 可选: ollama, deepseek等
LLM_MODEL_NAME = "qwen2:1.5b"  # 使用更通用的模型名称，更容易获取
LLM_BASE_URL = "http://127.0.0.1:11434"  # Ollama API基础URL
LLM_TEMPERATURE = 0.1  # 生成温度，较低的值使输出更确定性
LLM_MAX_TOKENS = 2048  # 最大生成token数

# RAG系统配置
RAG_SEARCH_TOP_K = 5  # 搜索时返回的文档数量
RAG_SIMILARITY_THRESHOLD = 0.0  # 相似度阈值，默认全部接受
RAG_QUERY_EXPANSION = False  # 是否启用查询扩展

# 文档处理配置
DEFAULT_CHUNK_SIZE = 1000  # 默认文档分块大小
DEFAULT_CHUNK_OVERLAP = 100  # 默认文档块重叠大小

# 日志配置
LOG_LEVEL = "INFO"  # 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_FILE = os.path.join(BASE_DIR, "logs", "rag_system.log")  # 日志文件路径

# DeepSeek API配置 (如果使用)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"

# 环境变量覆盖配置
# 允许通过环境变量覆盖上述配置
for key in list(globals().keys()):
    if key.isupper() and not key.startswith("_"):
        env_value = os.environ.get(key)
        if env_value is not None:
            # 尝试转换类型
            if globals()[key] is True or globals()[key] is False:
                # 布尔值
                globals()[key] = env_value.lower() in ("true", "1", "yes")
            elif isinstance(globals()[key], int):
                # 整数
                try:
                    globals()[key] = int(env_value)
                except ValueError:
                    pass
            elif isinstance(globals()[key], float):
                # 浮点数
                try:
                    globals()[key] = float(env_value)
                except ValueError:
                    pass
            else:
                # 字符串
                globals()[key] = env_value