#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG服务层
集成RAG能力和数据库操作，为WebUI提供服务
"""

import os
import uuid
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path

from rag.rag_system import RAGSystem, get_rag_system
from document_loaders import DocumentLoaderFactory as document_loader_factory
from document_loaders.base import Document
from sqlite.sqlite_manager import db_manager


class RAGServer:
    """RAG服务类，提供聊天、文档处理等核心功能"""
    
    def __init__(self):
        """初始化RAG服务"""
        # 获取全局RAG系统实例
        self.rag_system = get_rag_system()
        # 上传文件根目录
        self.upload_root = os.path.join(os.path.dirname(__file__), "upload")
        os.makedirs(self.upload_root, exist_ok=True)
    
    # 主题管理
    def create_new_topic(self, first_message: str) -> int:
        """创建新的聊天主题"""
        # 生成主题名称（使用第一条消息的前15个字符）
        topic_name = first_message[:15] + ("..." if len(first_message) > 15 else "")
        # 创建唯一的文件夹路径
        folder_id = str(uuid.uuid4())[:8]
        folder_path = os.path.join("upload", folder_id)
        # 确保文件夹存在
        os.makedirs(os.path.join(os.path.dirname(__file__), folder_path), exist_ok=True)
        # 创建主题
        topic_id = db_manager.create_topic(topic_name, folder_path)
        return topic_id
    
    def get_all_topics(self) -> List[Dict[str, Any]]:
        """获取所有聊天主题"""
        return db_manager.get_all_topics()
    
    def rename_topic(self, topic_id: int, new_name: str) -> bool:
        """重命名聊天主题"""
        return db_manager.update_topic_name(topic_id, new_name)
    
    def delete_topic(self, topic_id: int) -> bool:
        """删除聊天主题"""
        return db_manager.delete_topic(topic_id)
    
    # 消息管理
    def add_message(self, topic_id: int, role: str, content: str, message_type: str = 'text') -> int:
        """添加消息"""
        return db_manager.add_message(topic_id, role, content, message_type)
    
    def get_topic_messages(self, topic_id: int) -> List[Dict[str, Any]]:
        """获取主题的所有消息"""
        return db_manager.get_messages_by_topic(topic_id)
    
    def delete_message(self, message_id: int) -> bool:
        """删除单条消息"""
        return db_manager.delete_message(message_id)
    
    # 文件管理
    def upload_file(self, topic_id: int, file_info: Any) -> Dict[str, Any]:
        """上传文件并添加到知识库"""
        # 获取主题信息
        topic = db_manager.get_topic_by_id(topic_id)
        if not topic:
            raise ValueError("主题不存在")
        
        # 从Gradio文件对象中获取文件名和临时路径
        if hasattr(file_info, 'name'):
            filename = file_info.name
        elif isinstance(file_info, str):
            # 兼容字符串路径输入
            filename = os.path.basename(file_info)
            temp_path = file_info
        else:
            raise ValueError(f"不支持的文件类型: {type(file_info)}")
        
        # 创建目标路径
        target_dir = os.path.join(os.path.dirname(__file__), topic['folder_path'])
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)
        
        # 复制文件到目标位置
        try:
            if hasattr(file_info, 'temp_file_path'):
                # Gradio文件对象的临时路径
                shutil.copy2(file_info.temp_file_path, target_path)
            elif isinstance(file_info, str):
                # 字符串路径
                shutil.copy2(temp_path, target_path)
        except Exception as e:
            raise ValueError(f"文件复制失败: {str(e)}")
        
        # 获取文件大小
        file_size = os.path.getsize(target_path)
        
        # 添加文件记录到数据库
        file_id = db_manager.add_file(topic_id, filename, target_path, file_size)
        
        # 加载文档到RAG系统
        documents = self._load_document(target_path)
        document_ids = self.rag_system.add_documents(documents)
        
        return {
            "id": file_id,
            "filename": filename,
            "filepath": target_path,
            "size": file_size,
            "document_count": len(document_ids)
        }
    
    def _load_document(self, file_path: str) -> List[Document]:
        """加载文档"""
        # 获取文件扩展名
        ext = Path(file_path).suffix.lower()
        
        # 根据扩展名选择合适的加载器
        loader_type = None
        if ext == '.pdf':
            loader_type = 'pdf'
        elif ext in ['.doc', '.docx']:
            loader_type = 'word'
        elif ext == '.txt':
            loader_type = 'text'
        elif ext in ['.xlsx', '.xls']:
            loader_type = 'excel'
        elif ext == '.md':
            loader_type = 'text'
        else:
            raise ValueError(f"不支持的文件类型: {ext}")
        
        # 获取加载器
        loader = document_loader_factory.create(loader_type)
        loader.chunk_size = 1000
        loader.chunk_overlap = 100
        
        # 加载文档
        documents = loader.load(file_path)
        return documents
    
    def get_topic_files(self, topic_id: int) -> List[Dict[str, Any]]:
        """获取主题的所有文件"""
        return db_manager.get_files_by_topic(topic_id)
    
    def delete_file_record(self, file_id: int) -> bool:
        """删除文件记录（不删除实际文件）"""
        return db_manager.delete_file_record(file_id)
    
    # RAG查询
    def chat(self, topic_id: int, user_query: str) -> str:
        """进行RAG聊天，支持使用历史消息作为上下文"""
        # 首先保存用户消息到数据库
        self.add_message(topic_id, "user", user_query)
        
        # 获取历史消息（不包含当前刚添加的消息）
        history_messages = self.get_topic_messages(topic_id)
        
        # 构建上下文字符串，包含历史对话
        conversation_history = ""
        if len(history_messages) > 1:  # 确保有历史消息
            # 只取最近的10条消息作为上下文（避免上下文过长）
            for msg in history_messages[:-1][-10:]:  # 排除当前刚添加的用户消息
                role = "用户" if msg['role'] == "user" else "助手"
                conversation_history += f"{role}: {msg['content']}\n"
        
        # 执行RAG查询
        try:
            # 使用RAGSystem.query方法获取回答，传递对话历史
            result = self.rag_system.query(
                user_query,
                k=5,
                return_sources=False,
                conversation_history=conversation_history
            )
            
            # 从结果字典中获取answer字段
            response_text = result.get('answer', '未获取到回答')
            
            # 保存助手回答到数据库
            self.add_message(topic_id, "assistant", response_text)
            
            return response_text
        except Exception as e:
            error_message = f"生成回答时出错: {str(e)}"
            # 保存错误消息
            self.add_message(topic_id, "assistant", error_message)
            return error_message
    
    def search_knowledge(self, query: str, topic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """搜索知识库"""
        # 如果指定了主题，可以添加主题相关的过滤
        # 这里简化处理，直接调用RAG系统的搜索
        results = self.rag_system.search(query, k=10)
        return results


# 创建全局服务实例
rag_server = RAGServer()