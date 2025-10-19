#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器类
负责从YAML文件和环境变量加载配置，并使用Pydantic进行数据验证
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
# 添加dotenv支持
from dotenv import load_dotenv
from .config_entities import (
    AppConfig, LLMConfig, EmbeddingConfig, FAISSConfig,
    RAGConfig, DocumentConfig, LoggingConfig
)


class ConfigManager:
    """
    配置管理器，负责加载和管理所有配置
    
    支持从YAML文件和环境变量加载配置，并提供分类访问功能
    使用Pydantic实体类进行数据验证
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        # 首先加载.env文件中的环境变量
        load_dotenv()
        
        # 设置配置文件路径
        if config_file is None:
            base_dir = Path(__file__).parent.parent
            self.config_file = os.path.join(base_dir, "config", "default_config.yml")
        else:
            self.config_file = config_file
        
        # 加载配置
        self._config_dict = self._load_config()
        
        # 转换为Pydantic模型
        self._app_config = self._create_pydantic_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        从YAML文件和环境变量加载配置
        
        Returns:
            合并后的配置字典
        """
        # 从YAML文件加载配置
        config = self._load_from_yaml()
        
        # 替换环境变量引用
        config = self._resolve_env_variables(config)
        
        # 从.env文件和系统环境变量中加载额外配置
        self._override_from_env(config)
                
        return config
    
    def _load_from_yaml(self) -> Dict[str, Any]:
        """
        从YAML文件加载配置
        
        Returns:
            YAML文件中的配置
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                print(f"警告: 配置文件 {self.config_file} 不存在，使用默认配置")
                return {}
        except Exception as e:
            print(f"警告: 加载配置文件失败: {e}，使用默认配置")
            return {}
    
    def _resolve_env_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析配置中的环境变量引用
        格式: ${ENV_VAR_NAME}
        
        Args:
            config: 配置字典
            
        Returns:
            解析后的配置字典
        """
        if isinstance(config, dict):
            return {k: self._resolve_env_variables(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_variables(item) for item in config]
        elif isinstance(config, str):
            # 匹配 ${ENV_VAR_NAME}
            pattern = r'\$\{([^}]+)\}'
            
            def replace_var(match):
                env_var = match.group(1)
                return os.environ.get(env_var, '')
            
            return re.sub(pattern, replace_var, config)
        else:
            return config
    
    """
    强制覆盖变量 避免默认配置被环境变量覆盖
    """
    def _override_from_env(self, config: Dict[str, Any]) -> None:
        """
        从环境变量覆盖配置
        
        Args:
            config: 待覆盖的配置字典
        """
        # 处理LLM配置
        if "llm" not in config:
            config["llm"] = {}

        # 处理API密钥 - 支持多种模型的API密钥
        # 优先检查通用API_KEY环境变量
        if os.environ.get("API_KEY"):
            config["llm"]["api_key"] = os.environ.get("API_KEY")

    def _create_pydantic_config(self) -> AppConfig:
        """
        创建Pydantic配置实体
        
        Returns:
            完整的应用配置实体
        """
        return AppConfig(**self._config_dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，可以使用点号分隔（如 "llm.model_type"）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config_dict
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_llm_config(self) -> LLMConfig:
        """
        获取LLM配置
        
        Returns:
            LLM配置实体
        """
        return self._app_config.llm
    
    def get_embedding_config(self) -> EmbeddingConfig:
        """
        获取嵌入模型配置
        
        Returns:
            嵌入模型配置实体
        """
        return self._app_config.embedding
    
    def get_faiss_config(self) -> FAISSConfig:
        """
        获取FAISS配置
        
        Returns:
            FAISS配置实体
        """
        return self._app_config.faiss
    
    def get_rag_config(self) -> RAGConfig:
        """
        获取RAG配置
        
        Returns:
            RAG配置实体
        """
        return self._app_config.rag
    
    def get_document_config(self) -> DocumentConfig:
        """
        获取文档处理配置
        
        Returns:
            文档处理配置实体
        """
        return self._app_config.document
    
    def get_logging_config(self) -> LoggingConfig:
        """
        获取日志配置
        
        Returns:
            日志配置实体
        """
        return self._app_config.logging
    
    def get_app_config(self) -> AppConfig:
        """
        获取完整应用配置
        
        Returns:
            完整的应用配置实体
        """
        return self._app_config
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            new_config: 新的配置字典
        """
        # 深度合并配置
        self._merge_configs(self._config_dict, new_config)
        # 重新创建Pydantic配置
        self._app_config = self._create_pydantic_config()
    
    def _merge_configs(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """
        深度合并配置字典
        
        Args:
            base: 基础配置字典
            update: 更新配置字典
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value


# 创建全局配置管理器实例
config_manager = ConfigManager()

# 对外提供config
config = config_manager.get_app_config()