#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理模块
提供统一的配置加载和访问功能
"""

from .config_manager import ConfigManager, config_manager ,config

from .constants import (
    VECTOR_STORE_DIR,
    EMBEDDING_MODEL_TYPE,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_BASE_URL,
    LLM_MODEL_TYPE,
    LLM_MODEL_NAME,
    LLM_BASE_URL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    RAG_SEARCH_TOP_K,
    RAG_SIMILARITY_THRESHOLD,
    RAG_QUERY_EXPANSION,
    LOG_LEVEL,
    DEEPSEEK_API_KEY,
    DEEPSEEK_API_BASE_URL,
    VECTOR_STORE_INDEX_FILE
)

__all__ = ["ConfigManager", "config_manager","constants"]