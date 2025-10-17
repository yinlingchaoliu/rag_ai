#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统核心实现
集成向量存储、嵌入模型和LLM，支持FAISS持久化和配置化设置
"""

import os
from typing import List, Dict, Any, Optional
from document_loaders.base import Document
from embedding.base import embedding_model_factory
# 直接从vector_stores模块导入工厂，确保使用同一个实例
from vector_stores import vector_store_factory
import logging

# 导入配置
from config import (
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
    LOG_LEVEL
)

# 配置日志
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)

class RAGSystem:
    """
    RAG系统类，集成向量存储、嵌入模型和LLM，支持配置化和持久化
    """
    
    def __init__(self):
        """
        初始化RAG系统，使用配置文件中的设置
        """
        logger.info("初始化RAG系统...")
        
        # 初始化嵌入模型
        logger.info(f"初始化嵌入模型: {EMBEDDING_MODEL_TYPE} ({EMBEDDING_MODEL_NAME})")
        embedding_config = {
            "model_name": EMBEDDING_MODEL_NAME,
            "base_url": EMBEDDING_BASE_URL
        }
        self.embedding_model = embedding_model_factory.create(EMBEDDING_MODEL_TYPE, **embedding_config)
        
        # 确保向量存储目录存在
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        
        # 初始化向量存储
        logger.info(f"初始化向量存储: faiss (存储路径: {VECTOR_STORE_DIR})")
        
        # 移除FAISSVectorStore不支持的load_existing参数
        vector_store_config = {
            "persist_directory": VECTOR_STORE_DIR,
            "embedding_model": self.embedding_model
            # FAISSVectorStore初始化时会自动尝试加载已有索引
        }
        
        try:
            # 确保faiss存储已注册
            if 'faiss' not in vector_store_factory.get_available_vector_stores():
                logger.warning("faiss向量存储未注册，尝试手动注册...")
                from vector_stores.faiss_store import FAISSVectorStore
                vector_store_factory.register_vector_store('faiss', FAISSVectorStore)
                logger.info(f"手动注册后可用的向量存储: {vector_store_factory.get_available_vector_stores()}")
            
            self.vector_store = vector_store_factory.create("faiss", **vector_store_config)
            logger.info("向量存储初始化成功")
        except Exception as e:
            logger.error(f"向量存储初始化失败: {str(e)}")
            raise ValueError(f"初始化向量存储失败: {str(e)}")
        
        # 初始化LLM
        logger.info(f"初始化LLM: {LLM_MODEL_TYPE} ({LLM_MODEL_NAME})")
        if LLM_MODEL_TYPE == "ollama":
            # 动态导入以避免依赖问题
            from models.ollama_model import OllamaModel
            # 检查OllamaModel支持的参数，避免传入不支持的参数
            llm_config = {
                "model_name": LLM_MODEL_NAME
            }
            # 只添加OllamaModel支持的可选参数
            if hasattr(OllamaModel.__init__, '__code__'):
                init_params = OllamaModel.__init__.__code__.co_varnames
                if 'base_url' in init_params and LLM_BASE_URL:
                    llm_config['base_url'] = LLM_BASE_URL
                if 'max_tokens' in init_params and LLM_MAX_TOKENS:
                    llm_config['max_tokens'] = LLM_MAX_TOKENS
                # 注意：温度参数可能在OllamaModel中使用不同的名称或不支持
            
            logger.info(f"使用配置初始化OllamaModel: {llm_config}")
            self.llm = OllamaModel(**llm_config)
        elif LLM_MODEL_TYPE == "deepseek":
            # 可以根据需要添加DeepSeek模型支持
            logger.warning("DeepSeek模型支持尚未实现")
            # 暂时回退到Ollama模型
            from models.ollama_model import OllamaModel
            self.llm = OllamaModel(model_name=LLM_MODEL_NAME)
        else:
            raise ValueError(f"不支持的LLM类型: {LLM_MODEL_TYPE}")
        
        logger.info("RAG系统初始化完成")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        添加文档到向量存储
        
        Args:
            documents: 文档列表
            
        Returns:
            添加的文档ID列表
        """
        if not documents:
            logger.warning("尝试添加空文档列表")
            return []
        
        logger.info(f"添加 {len(documents)} 个文档到向量存储")
        
        # 调用向量存储的添加文档方法
        document_ids = self.vector_store.add_documents(documents)
        
        # 保存向量存储
        self.save()
        
        logger.info(f"成功添加 {len(document_ids)} 个文档")
        return document_ids
    
    def search(self, query: str, k: int = None, threshold: float = None) -> List[Dict[str, Any]]:
        """
        搜索相关文档
        
        Args:
            query: 查询文本
            k: 返回的文档数量，默认为配置文件中的值
            threshold: 相似度阈值，默认为配置文件中的值
            
        Returns:
            搜索结果列表
        """
        if k is None:
            k = RAG_SEARCH_TOP_K
        if threshold is None:
            threshold = RAG_SIMILARITY_THRESHOLD
        
        logger.info(f"搜索查询: '{query}' (k={k}, threshold={threshold})")
        
        # 调用向量存储的搜索方法
        results = self.vector_store.search(query, k, threshold=threshold)
        
        logger.info(f"找到 {len(results)} 个相关文档")
        
        # 打印搜索到的文档块内容
        for i, result in enumerate(results):
            doc_content = result['document'].content[:200] + '...' if len(result['document'].content) > 200 else result['document'].content
            source = result['document'].metadata.get('source', '未知源')
            print(f"\n[相关文档 {i+1}] 相似度: {result['score']:.4f}, 来源: {source}")
            print(f"内容: {doc_content}")
        
        return results
    
    def generate_answer(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """
        根据查询和搜索结果生成回答
        
        Args:
            query: 查询文本
            search_results: 搜索结果列表
            
        Returns:
            生成的回答
        """
        # 构建提示词
        if search_results:
            context = "\n".join([f"文档片段 {i+1} (相似度: {result['score']:.4f}):\n{result['document'].content}" 
                               for i, result in enumerate(search_results)])
            
            prompt = f"""基于以下提供的资料，回答用户的问题。请确保回答完全基于提供的资料，不要添加任何额外信息。
            
资料:
{context}
            
问题:
{query}
            
回答:
"""
        else:
            # 当没有找到相关文档时
            prompt = f"""用户的问题是: {query}

很抱歉，我无法找到与此问题相关的信息。请尝试提供更具体的问题或使用其他关键词重新提问。"""
        
        logger.info(f"调用LLM生成回答，搜索结果数: {len(search_results)}")
        
        # 调用LLM生成回答
        try:
            response = self.llm.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"LLM生成失败: {str(e)}")
            return f"生成回答时出错: {str(e)}"
    
    def query(self, query: str, k: int = None, return_sources: bool = False) -> Dict[str, Any]:
        """
        完整的查询流程: 搜索 -> 生成回答
        
        Args:
            query: 查询文本
            k: 返回的文档数量
            return_sources: 是否返回源文档信息
            
        Returns:
            查询结果字典
        """
        logger.info(f"执行RAG查询: '{query}'")
        
        # 搜索相关文档
        search_results = self.search(query, k)
        
        # 生成回答
        answer = self.generate_answer(query, search_results)
        
        # 构建返回结果
        result = {
            "query": query,
            "answer": answer,
            "search_results_count": len(search_results)
        }
        
        # 如果需要返回源文档信息
        if return_sources:
            sources = [
                {
                    "source": result["document"].metadata.get("source", "未知源"),
                    "content": result["document"].content,
                    "score": result["score"]
                }
                for result in search_results
            ]
            result["sources"] = sources
        
        logger.info(f"查询完成，找到 {len(search_results)} 个相关文档")
        return result
    
    def save(self) -> bool:
        """
        保存向量存储
        
        Returns:
            是否保存成功
        """
        try:
            logger.info(f"保存向量存储到: {VECTOR_STORE_DIR}")
            self.vector_store.save()
            return True
        except Exception as e:
            logger.error(f"保存向量存储失败: {str(e)}")
            return False
    
    def list_sources(self) -> List[str]:
        """
        列出所有文档源
        
        Returns:
            源文件路径列表
        """
        try:
            sources = self.vector_store.list_sources()
            logger.info(f"找到 {len(sources)} 个文档源")
            return sources
        except Exception as e:
            logger.error(f"列出文档源失败: {str(e)}")
            return []
    
    def delete_source(self, source: str) -> bool:
        """
        删除指定文档源
        
        Args:
            source: 源文件路径
            
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"删除文档源: {source}")
            result = self.vector_store.delete_by_source(source)
            if result:
                # 保存更改
                self.save()
            return result
        except Exception as e:
            logger.error(f"删除文档源失败: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """
        清空知识库
        
        Returns:
            是否清空成功
        """
        try:
            logger.info("清空向量存储")
            result = self.vector_store.clear()
            if result:
                # 保存更改
                self.save()
            return result
        except Exception as e:
            logger.error(f"清空向量存储失败: {str(e)}")
            return False


# 全局RAG系统实例
_rag_system_instance = None

def get_rag_system() -> RAGSystem:
    """
    获取全局RAG系统实例
    
    Returns:
        RAGSystem实例
    """
    global _rag_system_instance
    if _rag_system_instance is None:
        _rag_system_instance = RAGSystem()
    return _rag_system_instance