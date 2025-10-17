#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
x公司知识库RAG系统应用

支持文档导入、查询、源文件管理等功能
"""

import os
import sys
import argparse
from typing import List, Dict, Any
from pathlib import Path
from document_loaders import DocumentLoaderFactory as document_loader_factory
from rag.rag_system import RAGSystem, get_rag_system
from document_loaders.base import Document
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

def load_document_from_path(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> List[Document]:
    """
    从文件路径加载文档
    
    Args:
        file_path: 文件路径
        chunk_size: 分块大小
        chunk_overlap: 块重叠大小
        
    Returns:
        文档列表
    """
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return []
    
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
        loader_type = 'text'  # 使用文本加载器处理Markdown
    else:
        print(f"警告: 不支持的文件类型: {ext}")
        return []
    
    try:
        # 获取加载器
        loader = document_loader_factory.create(loader_type)
        loader.chunk_size = chunk_size
        loader.chunk_overlap = chunk_overlap
        
        # 加载文档
        documents = loader.load(file_path)
        print(f"成功加载文件: {file_path}, 生成 {len(documents)} 个文档块")
        return documents
    except Exception as e:
        print(f"加载文件 {file_path} 失败: {str(e)}")
        return []

def load_documents_from_directory(directory: str, recursive: bool = False) -> List[Document]:
    """
    从目录加载所有支持的文档
    
    Args:
        directory: 目录路径
        recursive: 是否递归加载子目录
        
    Returns:
        文档列表
    """
    if not os.path.exists(directory):
        print(f"错误: 目录不存在: {directory}")
        return []
    
    if not os.path.isdir(directory):
        print(f"错误: 不是有效的目录: {directory}")
        return []
    
    all_documents = []
    supported_extensions = {'.pdf', '.doc', '.docx', '.txt', '.xlsx', '.xls', '.md'}
    
    if recursive:
        for root, _, files in os.walk(directory):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in supported_extensions:
                    file_path = os.path.join(root, file)
                    documents = load_document_from_path(file_path)
                    all_documents.extend(documents)
    else:
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            if os.path.isfile(file_path):
                ext = Path(file).suffix.lower()
                if ext in supported_extensions:
                    documents = load_document_from_path(file_path)
                    all_documents.extend(documents)
    
    print(f"从目录 {directory} 共加载 {len(all_documents)} 个文档块")
    return all_documents

def process_files(rag: RAGSystem, paths: List[str], recursive: bool = False) -> int:
    """
    处理文件或目录路径列表
    
    Args:
        rag: RAG系统实例
        paths: 文件或目录路径列表
        recursive: 是否递归加载子目录
        
    Returns:
        添加的文档总数
    """
    total_added = 0
    
    for path in paths:
        if os.path.isdir(path):
            # 加载目录中的所有文档
            documents = load_documents_from_directory(path, recursive)
            added_ids = rag.add_documents(documents)
            total_added += len(added_ids)
        else:
            # 加载单个文件
            documents = load_document_from_path(path)
            added_ids = rag.add_documents(documents)
            total_added += len(added_ids)
    
    return total_added

def main():
    """
    主函数，处理命令行参数
    """
    parser = argparse.ArgumentParser(description='X公司知识库RAG系统')
    
    # 子命令解析器
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # load命令 - 加载文档
    load_parser = subparsers.add_parser('load', help='加载文档到知识库')
    load_parser.add_argument('paths', nargs='+', help='文件或目录路径')
    load_parser.add_argument('-r', '--recursive', action='store_true', help='递归加载子目录')
    
    # query命令 - 查询知识库
    query_parser = subparsers.add_parser('query', help='查询知识库')
    query_parser.add_argument('query_text', nargs='?', help='查询文本')
    query_parser.add_argument('-k', '--top-k', type=int, default=5, help='返回的相关文档数量')
    query_parser.add_argument('-s', '--show-sources', action='store_true', help='显示源文档信息')
    
    # list命令 - 列出所有源
    subparsers.add_parser('list-sources', help='列出所有文档源')
    
    # delete命令 - 删除指定源
    delete_parser = subparsers.add_parser('delete-source', help='删除指定文档源')
    delete_parser.add_argument('source', help='源文件路径')
    
    # clear命令 - 清空知识库
    subparsers.add_parser('clear', help='清空知识库')
    
    # 没有指定命令时，进入交互式查询模式
    args = parser.parse_args()
    
    try:
        # 初始化RAG系统
        rag = get_rag_system()
        
        # 处理不同的命令
        if args.command == 'load':
            # 加载文档
            total_added = process_files(rag, args.paths, args.recursive)
            print(f"总计添加 {total_added} 个文档到知识库")
            
        elif args.command == 'query':
            # 查询知识库
            if args.query_text:
                # 单次查询
                result = rag.query(
                    args.query_text, 
                    k=args.top_k,
                    return_sources=args.show_sources
                )
                
                print(f"\n问题: {result['query']}")
                print(f"\n回答: {result['answer']}")
                print(f"\n相关文档数: {result['search_results_count']}")
                
                if args.show_sources and 'sources' in result:
                    print(f"\n源文档信息:")
                    for i, source in enumerate(result['sources'], 1):
                        print(f"\n--- 来源 {i} ---")
                        print(f"文件: {source['source']}")
                        print(f"相似度: {source['score']:.4f}")
                        print(f"内容片段: {source['content'][:200]}...")
            else:
                # 交互式查询
                print("=== 进入交互式查询模式 (输入 'exit' 或 'quit' 退出) ===")
                while True:
                    try:
                        query_text = input("\n请输入问题: ")
                        if query_text.lower() in ['exit', 'quit', '退出']:
                            break
                        
                        result = rag.query(
                            query_text, 
                            k=args.top_k,
                            return_sources=args.show_sources
                        )
                        
                        print(f"\n回答: {result['answer']}")
                        print(f"相关文档数: {result['search_results_count']}")
                        
                    except KeyboardInterrupt:
                        print("\n查询已中断")
                        break
                    except Exception as e:
                        print(f"查询出错: {str(e)}")
        
        elif args.command == 'list-sources':
            # 列出所有源
            sources = rag.list_sources()
            if sources:
                print("\n知识库中的文档源:")
                for i, source in enumerate(sources, 1):
                    print(f"{i}. {source}")
            else:
                print("知识库中暂无文档")
        
        elif args.command == 'delete-source':
            # 删除指定源
            success = rag.delete_source(args.source)
            if success:
                print(f"成功删除源: {args.source}")
            else:
                print(f"删除源失败: {args.source} (源可能不存在)")
        
        elif args.command == 'clear':
            # 清空知识库
            confirm = input("确认清空整个知识库? (y/N): ")
            if confirm.lower() == 'y':
                success = rag.clear()
                if success:
                    print("知识库已清空")
                else:
                    print("清空知识库失败")
            else:
                print("操作已取消")
        
        else:
            # 默认模式: 如果有参数，作为路径加载文档；否则进入交互式查询
            if len(sys.argv) > 1:
                # 假设参数是文件路径
                total_added = process_files(rag, sys.argv[1:], False)
                print(f"总计添加 {total_added} 个文档到知识库")
            else:
                # 进入交互式查询
                print("=== X公司知识库RAG系统 ===")
                print("提示: 使用 'python x_rag_app.py load 文件路径' 加载文档")
                print("进入交互式查询模式 (输入 'exit' 或 'quit' 退出)")
                
                while True:
                    try:
                        query_text = input("\n请输入问题: ")
                        if query_text.lower() in ['exit', 'quit', '退出']:
                            break
                        
                        result = rag.query(query_text)
                        print(f"\n回答: {result['answer']}")
                        print(f"相关文档数: {result['search_results_count']}")
                        
                    except KeyboardInterrupt:
                        print("\n查询已中断")
                        break
                    except Exception as e:
                        print(f"查询出错: {str(e)}")
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()