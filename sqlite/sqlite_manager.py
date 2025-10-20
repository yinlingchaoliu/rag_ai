#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite数据库管理器
负责聊天主题、消息和文件的增删改查操作
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class SQLiteManager:
    """SQLite数据库管理器类"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建聊天主题表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            folder_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建消息表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
        )
        ''')
        
        # 创建文件表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics (id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        # 返回字典格式的结果
        conn.row_factory = sqlite3.Row
        return conn
    
    # 主题相关操作
    def create_topic(self, name: str, folder_path: str) -> int:
        """创建新的聊天主题"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO topics (name, folder_path) VALUES (?, ?)",
            (name, folder_path)
        )
        topic_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return topic_id
    
    def get_all_topics(self) -> List[Dict[str, Any]]:
        """获取所有聊天主题"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topics ORDER BY updated_at DESC")
        topics = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return topics
    
    def get_topic_by_id(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取聊天主题"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM topics WHERE id = ?", (topic_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_topic_name(self, topic_id: int, new_name: str) -> bool:
        """更新聊天主题名称"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE topics SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_name, topic_id)
        )
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_topic(self, topic_id: int) -> bool:
        """删除聊天主题（会级联删除相关消息和文件记录）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # 消息相关操作
    def add_message(self, topic_id: int, role: str, content: str, message_type: str = 'text') -> int:
        """添加消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (topic_id, role, content, message_type) VALUES (?, ?, ?, ?)",
            (topic_id, role, content, message_type)
        )
        message_id = cursor.lastrowid
        # 更新主题的更新时间
        cursor.execute("UPDATE topics SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (topic_id,))
        conn.commit()
        conn.close()
        return message_id
    
    def get_messages_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """获取指定主题的所有消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE topic_id = ? ORDER BY created_at ASC",
            (topic_id,)
        )
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return messages
    
    def delete_message(self, message_id: int) -> bool:
        """删除单条消息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    # 文件相关操作
    def add_file(self, topic_id: int, filename: str, file_path: str, file_size: int) -> int:
        """添加文件记录"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (topic_id, filename, file_path, file_size) VALUES (?, ?, ?, ?)",
            (topic_id, filename, file_path, file_size)
        )
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id
    
    def get_files_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """获取指定主题的所有文件"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM files WHERE topic_id = ? ORDER BY upload_time DESC",
            (topic_id,)
        )
        files = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return files
    
    def delete_file_record(self, file_id: int) -> bool:
        """删除文件记录（不会删除实际文件）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取文件信息"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None


# 创建全局数据库管理器实例
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db", "sqlite", "rag_chat.db")
db_manager = SQLiteManager(DB_PATH)