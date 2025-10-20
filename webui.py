#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebUI界面实现
使用Gradio构建聊天界面
"""

import os
import gradio as gr
from typing import Dict, List, Any, Optional
import time

from server import rag_server


class RAGWebUI:
    """RAG WebUI类"""
    
    def __init__(self):
        """初始化WebUI"""
        self.current_topic_id = None
        self.show_knowledge_panel = False
    
    def create_interface(self) -> gr.Blocks:
        """创建Gradio界面"""
        with gr.Blocks(title="专业知识小助手", theme=gr.themes.Soft()) as demo:
            # 设置主题ID的状态变量
            topic_id_state = gr.State(None)
            
            with gr.Row():
                # 左侧：主题列表
                with gr.Column(scale=1):
                    gr.Markdown("### 聊天主题")
                    
                    # 主题列表
                    topic_list = gr.Dropdown(
                        choices=self._get_topic_choices(),
                        label="选择或创建主题",
                        interactive=True
                    )
                    
                    # 创建新主题按钮
                    create_new_btn = gr.Button("创建新主题")
                    
                    # 重命名主题
                    new_topic_name = gr.Textbox(label="新主题名称")
                    rename_btn = gr.Button("重命名主题")
                    
                    # 删除主题
                    delete_topic_btn = gr.Button("删除主题", variant="stop")
                    
                    # 查看知识库按钮
                    toggle_knowledge_btn = gr.Button("📚 查看知识库")
                
                # 中间：聊天区域
                with gr.Column(scale=3):
                    gr.Markdown("### 专业知识小助手")
                    
                    # 聊天历史
                    chat_history = gr.Chatbot(label="聊天记录", height=500, type="messages")
                    
                    # 输入框
                    with gr.Row():
                        user_input = gr.Textbox(
                            label="输入您的问题",
                            placeholder="请输入您的问题...",
                            scale=4
                        )
                        send_btn = gr.Button("发送", variant="primary", scale=1)
                    
                    # 文件上传区域
                    with gr.Accordion("上传文件", open=False):
                        file_upload = gr.File(
                            file_types=[".pdf", ".txt", ".doc", ".docx", ".xlsx", ".xls", ".md", ".jpg", ".jpeg", ".png"],
                            label="上传文档或图片",
                            file_count="multiple"
                        )
                        upload_btn = gr.Button("添加到知识库")
                        
                        # 已上传文件列表
                        uploaded_files_output = gr.Dataframe(
                            headers=["文件名", "上传时间", "操作"],
                            datatype=["str", "str", "str"],
                            label="已上传文件"
                        )
                
                # 右侧：知识库面板（默认隐藏）
                with gr.Column(scale=2, visible=False) as knowledge_panel:
                    gr.Markdown("### 知识库管理")
                    
                    # 搜索框
                    knowledge_search = gr.Textbox(label="搜索知识库")
                    search_btn = gr.Button("搜索")
                    
                    # 搜索结果
                    search_results = gr.Textbox(
                        label="搜索结果",
                        lines=10,
                        interactive=False
                    )
                    
                    # 所有上传文件列表
                    all_files_output = gr.Dataframe(
                        headers=["文件名", "所属主题", "上传时间"],
                        datatype=["str", "str", "str"]
                    )
                    
                    # 关闭按钮
                    close_panel_btn = gr.Button("关闭")
            
            # 事件处理
            # 创建新主题
            create_new_btn.click(
                self._create_new_topic,
                inputs=[new_topic_name, topic_id_state],
                outputs=[topic_list, topic_id_state, chat_history, uploaded_files_output]
            )
            
            # 选择主题
            topic_list.change(
                self._select_topic,
                inputs=[topic_list, topic_id_state],
                outputs=[topic_id_state, chat_history, uploaded_files_output]
            )
            
            # 重命名主题
            rename_btn.click(
                self._rename_topic,
                inputs=[new_topic_name, topic_id_state],
                outputs=[topic_list, new_topic_name]
            )
            
            # 删除主题
            delete_topic_btn.click(
                self._delete_topic,
                inputs=[topic_id_state],
                outputs=[topic_list, topic_id_state, chat_history, uploaded_files_output]
            )
            
            # 发送消息
            send_btn.click(
                self._send_message,
                inputs=[user_input, chat_history, topic_id_state],
                outputs=[user_input, chat_history, topic_id_state]
            )
            
            # 输入框回车发送
            user_input.submit(
                self._send_message,
                inputs=[user_input, chat_history, topic_id_state],
                outputs=[user_input, chat_history, topic_id_state]
            )
            
            # 上传文件
            upload_btn.click(
                self._upload_files,
                inputs=[file_upload, topic_id_state],
                outputs=[uploaded_files_output, file_upload]
            )
            
            # 删除文件记录
            uploaded_files_output.select(
                self._delete_file,
                inputs=[topic_id_state],
                outputs=[uploaded_files_output]
            )
            
            # 切换知识库面板
            toggle_knowledge_btn.click(
                self._toggle_knowledge_panel,
                inputs=[knowledge_panel],
                outputs=[knowledge_panel]
            )
            
            # 关闭知识库面板
            close_panel_btn.click(
                lambda: gr.Column(visible=False),
                outputs=[knowledge_panel]
            )
            
            # 搜索知识库
            search_btn.click(
                self._search_knowledge,
                inputs=[knowledge_search],
                outputs=[search_results]
            )
            
            # 删除消息
            chat_history.select(
                self._delete_chat_message,
                inputs=[topic_id_state],
                outputs=[chat_history]
            )
        
        return demo
    
    def _get_topic_choices(self) -> List[tuple]:
        """获取主题选择列表"""
        topics = rag_server.get_all_topics()
        choices = [(topic['name'], topic['id']) for topic in topics]
        return choices
    
    def _create_new_topic(self, new_topic_name: str, current_topic_id: int) -> tuple:
        """创建新主题"""
        if not new_topic_name.strip():
            return gr.Dropdown(choices=self._get_topic_choices()), None, None, None
        
        # 创建新主题
        topic_id = rag_server.create_new_topic(new_topic_name)
        
        # 更新主题列表
        return (
            gr.Dropdown(choices=self._get_topic_choices(), value=topic_id),
            topic_id,
            [],  # 清空聊天历史
            gr.Dataframe(headers=["文件名", "上传时间", "操作"], datatype=["str", "str", "str"])  # 清空文件列表
        )
    
    def _select_topic(self, topic_id: int, current_topic_id: int) -> tuple:
        """选择主题"""
        if not topic_id:
            return None, None, None
        
        # 获取聊天记录
        messages = rag_server.get_topic_messages(topic_id)
        chat_history = []
        for msg in messages:
            chat_history.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # 获取文件列表
        files = rag_server.get_topic_files(topic_id)
        file_data = []
        for file in files:
            file_data.append([file['filename'], file['upload_time'], f"删除文件_{file['id']}"])
        
        return topic_id, chat_history, gr.Dataframe(value=file_data, headers=["文件名", "上传时间", "操作"])
    
    def _rename_topic(self, new_name: str, topic_id: int) -> tuple:
        """重命名主题"""
        if not topic_id or not new_name.strip():
            return gr.Dropdown(choices=self._get_topic_choices()), ""
        
        rag_server.rename_topic(topic_id, new_name.strip())
        return gr.Dropdown(choices=self._get_topic_choices(), value=topic_id), ""
    
    def _delete_topic(self, topic_id: int) -> tuple:
        """删除主题"""
        if not topic_id:
            return gr.Dropdown(choices=self._get_topic_choices()), None, None, None
        
        rag_server.delete_topic(topic_id)
        return (
            gr.Dropdown(choices=self._get_topic_choices()),
            None,
            [],
            gr.Dataframe(headers=["文件名", "上传时间", "操作"], datatype=["str", "str", "str"])
        )
    
    def _send_message(self, user_input: str, chat_history: List[dict], topic_id: int) -> tuple:
        """发送消息"""
        print(f"chentong 调试 - 进入_send_message: user_input={user_input}, topic_id={topic_id}")
        if not user_input.strip():
            return "", chat_history
        
        # 如果没有选择主题，自动创建一个默认主题
        if not topic_id:
            print("chentong 调试 - 没有选择主题，自动创建默认主题")
            # 创建默认主题
            topic_id = rag_server.create_new_topic("默认主题")
            print(f"chentong 调试 - 已创建默认主题，ID: {topic_id}")
            # 更新界面上的主题选择器（通过返回新的topic_id）
        
        print(f"chentong 发送消息: {user_input}")
        # 添加用户消息到历史
        chat_history.append({"role": "user", "content": user_input})
        print(f"chentong 添加chat_history消息: {chat_history}")
        # 添加助手正在输入的占位符
        chat_history.append({"role": "assistant", "content": None})
        
        # 生成回复
        try:
            response = rag_server.chat(topic_id, user_input)
            print(f"chentong 获取回复: {response}")
            chat_history[-1]["content"] = response
        except Exception as e:
            error_msg = f"发生错误: {str(e)}"
            print(f"chentong 错误: {error_msg}")
            chat_history[-1]["content"] = error_msg

        print(f"chentong 最终chat_history消息: {chat_history}")
        # 返回空输入框、更新后的聊天历史和新的topic_id
        return "", chat_history, topic_id
    
    def _upload_files(self, files: List, topic_id: int) -> tuple:
        """上传文件"""
        if not files or not topic_id:
            return gr.Dataframe(headers=["文件名", "上传时间", "操作"], datatype=["str", "str", "str"]), None
        
        # 上传每个文件
        for file in files:
            try:
                # 直接传递文件对象给server
                rag_server.upload_file(topic_id, file)
            except Exception as e:
                print(f"上传文件失败: {str(e)}")
        
        # 更新文件列表
        files = rag_server.get_topic_files(topic_id)
        file_data = []
        for file in files:
            file_data.append([file['filename'], file['upload_time'], f"删除文件_{file['id']}"])
        
        return gr.Dataframe(value=file_data, headers=["文件名", "上传时间", "操作"]), None
    
    def _delete_file(self, evt: gr.SelectData, topic_id: int) -> gr.Dataframe:
        """删除文件记录"""
        if not topic_id or not evt.data:
            return gr.Dataframe(headers=["文件名", "上传时间", "操作"], datatype=["str", "str", "str"])
        
        # 获取文件ID
        action_str = evt.data[2]
        if action_str.startswith("删除文件_"):
            file_id = int(action_str.split("_")[-1])
            rag_server.delete_file_record(file_id)
        
        # 更新文件列表
        files = rag_server.get_topic_files(topic_id)
        file_data = []
        for file in files:
            file_data.append([file['filename'], file['upload_time'], f"删除文件_{file['id']}"])
        
        return gr.Dataframe(value=file_data, headers=["文件名", "上传时间", "操作"])
    
    def _toggle_knowledge_panel(self, panel: gr.Column) -> gr.Column:
        """切换知识库面板显示状态"""
        return gr.Column(visible=not panel.visible)
    
    def _search_knowledge(self, query: str) -> str:
        """搜索知识库"""
        if not query.strip():
            return "请输入搜索关键词"
        
        results = rag_server.search_knowledge(query)
        formatted_results = "\n\n---\n\n".join([
            f"相似度: {result['similarity']:.4f}\n内容: {result['content'][:200]}..." 
            for result in results[:5]
        ])
        
        return formatted_results or "未找到相关内容"
    
    def _delete_chat_message(self, evt: gr.SelectData, topic_id: int) -> List[dict]:
        """删除聊天消息"""
        if not topic_id or evt.index is None:
            return []
        
        # 获取消息列表
        messages = rag_server.get_topic_messages(topic_id)
        
        # 现在每条消息都是独立的，直接使用索引
        message_index = evt.index[0]
        
        if 0 <= message_index < len(messages):
            # 删除消息
            rag_server.delete_message(messages[message_index]['id'])
        
        # 重新获取聊天历史
        return self._select_topic(topic_id, topic_id)[1]
    
    def launch(self):
        """启动WebUI"""
        demo = self.create_interface()
        demo.launch(server_name="0.0.0.0", server_port=7861, share=False)


# 创建WebUI实例
webui = RAGWebUI()