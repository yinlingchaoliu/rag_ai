#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X公司知识库RAG系统配置文件

本文件包含RAG系统的所有可配置参数
使用ConfigManager管理配置，保持向后兼容性
"""

import os
from pathlib import Path

# 导入配置管理器
from config.config_manager import config_manager

# 基础配置
BASE_DIR = Path(__file__).parent.parent

# 从配置管理器获取分类配置（使用Pydantic实体类）
llm_config = config_manager.get_llm_config()
embedding_config = config_manager.get_embedding_config()
faiss_config = config_manager.get_faiss_config()
rag_config = config_manager.get_rag_config()
document_config = config_manager.get_document_config()
logging_config = config_manager.get_logging_config()

# FAISS向量存储配置 (保持原有变量名，确保向后兼容)
VECTOR_STORE_DIR = os.path.join(BASE_DIR, faiss_config.vector_store_dir)
VECTOR_STORE_INDEX_FILE = faiss_config.index_file
VECTOR_STORE_DOCS_FILE = faiss_config.docs_file
VECTOR_STORE_MAPPINGS_FILE = faiss_config.mappings_file
VECTOR_STORE_EMBEDDINGS_FILE = faiss_config.embeddings_file

# 嵌入模型配置 (保持原有变量名，确保向后兼容)
EMBEDDING_MODEL_TYPE = embedding_config.model_type
EMBEDDING_MODEL_NAME = embedding_config.model_name
EMBEDDING_DIMENSION = embedding_config.dimension
EMBEDDING_BASE_URL = embedding_config.base_url

# LLM模型配置 (保持原有变量名，确保向后兼容)
LLM_MODEL_TYPE = llm_config.model_type
LLM_MODEL_NAME = llm_config.model_name
LLM_BASE_URL = llm_config.base_url
LLM_TEMPERATURE = llm_config.temperature
LLM_MAX_TOKENS = llm_config.max_tokens

# RAG系统配置 (保持原有变量名，确保向后兼容)
RAG_SEARCH_TOP_K = rag_config.search_top_k
RAG_SIMILARITY_THRESHOLD = rag_config.similarity_threshold
RAG_QUERY_EXPANSION = rag_config.query_expansion

# 文档处理配置 (保持原有变量名，确保向后兼容)
DEFAULT_CHUNK_SIZE = document_config.chunk_size
DEFAULT_CHUNK_OVERLAP = document_config.chunk_overlap

# 日志配置 (保持原有变量名，确保向后兼容)
LOG_LEVEL = logging_config.log_level
LOG_FILE = os.path.join(BASE_DIR, logging_config.log_file)

# DeepSeek API配置 (保持原有变量名，确保向后兼容)
DEEPSEEK_API_KEY = llm_config.deepseek_api_key
DEEPSEEK_API_BASE_URL = llm_config.deepseek_api_base_url

DEFAULT_MODEL = llm_config.model_type
# 注意：环境变量覆盖配置的逻辑已在ConfigManager中实现，
# 这里不再需要重复实现