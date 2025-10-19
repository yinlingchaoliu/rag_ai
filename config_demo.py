#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试配置管理器功能
重点测试Pydantic实体类的使用
"""

import os
from config.config_manager import ConfigManager, config_manager
from config.config_entities import LLMConfig, EmbeddingConfig, FAISSConfig

def test_config_manager():
    """
    测试配置管理器的基本功能
    """
    print("开始测试配置管理器...")
    
    # 测试LLM配置（使用Pydantic实体类）
    llm_config = config_manager.get_llm_config()
    print("\n1. LLM配置 (Pydantic实体类):")
    print(f"   类型: {type(llm_config).__name__}")
    print(f"   模型类型: {llm_config.model_type}")
    print(f"   模型名称: {llm_config.model_name}")
    print(f"   基础URL: {llm_config.base_url}")
    print(f"   温度: {llm_config.temperature}")
    print(f"   最大tokens: {llm_config.max_tokens}")
    print(f"   API密钥: {llm_config.api_key }")
    print(f"   DeepSeek API密钥: {llm_config.deepseek_api_key }")
    print(f"   DeepSeek API基础URL: {llm_config.deepseek_api_base_url }")
        
    # 测试嵌入模型配置（使用Pydantic实体类）
    embedding_config = config_manager.get_embedding_config()
    print("\n2. 嵌入模型配置 (Pydantic实体类):")
    print(f"   类型: {type(embedding_config).__name__}")
    print(f"   模型类型: {embedding_config.model_type}")
    print(f"   模型名称: {embedding_config.model_name}")
    print(f"   维度: {embedding_config.dimension}")
    print(f"   基础URL: {embedding_config.base_url}")
    
    # 测试FAISS配置（使用Pydantic实体类）
    faiss_config = config_manager.get_faiss_config()
    print("\n3. FAISS配置 (Pydantic实体类):")
    print(f"   类型: {type(faiss_config).__name__}")
    print(f"   向量存储目录: {faiss_config.vector_store_dir}")
    print(f"   索引文件: {faiss_config.index_file}")
    print(f"   文档文件: {faiss_config.docs_file}")
    
    # 测试get方法
    print("\n4. 测试get方法:")
    llm_type = config_manager.get("llm.model_type")
    embedding_name = config_manager.get("embedding.model_name")
    rag_k = config_manager.get("rag.search_top_k")
    
    print(f"   llm.model_type = {llm_type}")
    print(f"   embedding.model_name = {embedding_name}")
    print(f"   rag.search_top_k = {rag_k}")
    
    # 测试不存在的配置
    print("\n5. 测试不存在的配置:")
    nonexistent = config_manager.get("nonexistent.key", "默认值")
    print(f"   不存在的配置返回默认值: {nonexistent}")
    
    # 测试完整应用配置
    print("\n6. 测试完整应用配置:")
    app_config = config_manager.get_app_config()
    print(f"   应用配置类型: {type(app_config).__name__}")
    print(f"   LLM配置类型: {type(app_config.llm).__name__}")
    print(f"   嵌入配置类型: {type(app_config.embedding).__name__}")
    
    # 测试配置更新
    print("\n7. 测试配置更新:")
    print(f"   更新前温度: {llm_config.temperature}")
    config_manager.update_config({
        "llm": {
            "temperature": 0.3
        }
    })
    updated_llm_config = config_manager.get_llm_config()
    print(f"   更新后温度: {updated_llm_config.temperature}")
    
    print("\n配置管理器测试完成！")

if __name__ == "__main__":
    test_config_manager()