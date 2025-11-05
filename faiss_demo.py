#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG系统演示脚本

此脚本演示如何：
1. 扫描并加载asset目录下的所有支持的文件
2. 使用Ollama嵌入模型将文档内容转换为向量
3. 将向量存储到FAISS向量数据库中
4. 执行向量搜索以检索相关文档
5. 展示文档源管理功能

包含异步优化版本，用于处理大型文档如三国演义.txt
"""

import os
import sys
import argparse
import asyncio
from typing import List, Dict, Any, Optional

# 导入我们的自定义模块
from document_loaders.base import Document
from document_loaders.pdf_loader import PDFFileLoader
from document_loaders.text_loader import TextFileLoader
from document_loaders.word_loader import WordFileLoader
from vector_stores import vector_store_factory, VectorDatabaseManager, vector_db_manager
from embedding import embedding_model_factory, BaseEmbeddingModel

# 导入异步工具
from loop.async_utils import create_batch_optimizer, optimize_vector_store


class RAGDemo:
    """RAG系统演示类"""
    
    def __init__(self, asset_dir: str = "./asset", vector_store_dir: str = "./db/vector_store"):
        """
        初始化RAG演示
        
        Args:
            asset_dir: 资产目录路径
            vector_store_dir: 向量存储目录路径
        """
        self.asset_dir = asset_dir
        self.vector_store_dir = vector_store_dir
        
        # 创建文档加载器映射
        self.loaders = {
            ".pdf": PDFFileLoader(),
            ".txt": TextFileLoader(),
            ".md": TextFileLoader(),
            ".docx": WordFileLoader()
        }
        
        # 创建向量存储
        try:
            # 使用FAISS向量存储，会自动使用默认的Ollama嵌入模型
            self.vector_store = vector_store_factory.create(
                "faiss", 
                persist_directory=vector_store_dir,
                index_name="faiss_index"
            )
            print(f"成功创建FAISS向量存储")
            
            # 初始化批处理优化器
            self.batch_optimizer = create_batch_optimizer(self.vector_store)
            
        except Exception as e:
            print(f"创建向量存储失败: {str(e)}")
            raise
    
    def __del__(self):
        """析构函数，确保资源正确释放"""
        try:
            if hasattr(self, 'async_vector_store'):
                self.async_vector_store.close()
            if hasattr(self, 'async_manager'):
                self.async_manager.close()
        except:
            pass
    
    def get_supported_file_extensions(self) -> List[str]:
        """获取所有支持的文件扩展名"""
        return list(self.loaders.keys())
    
    def find_supported_files(self) -> List[str]:
        """
        查找资产目录下所有支持的文件
        
        Returns:
            支持的文件路径列表
        """
        supported_files = []
        
        if not os.path.exists(self.asset_dir):
            print(f"警告: 资产目录 {self.asset_dir} 不存在")
            return []
        
        for root, _, files in os.walk(self.asset_dir):
            for file in files:
                # 检查文件扩展名是否受支持
                ext = os.path.splitext(file)[1].lower()
                if ext in self.loaders:
                    file_path = os.path.join(root, file)
                    supported_files.append(file_path)
        
        return supported_files
    
    def load_document(self, file_path: str) -> List[Document]:
        """
        加载单个文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext not in self.loaders:
            print(f"不支持的文件类型: {ext}")
            return []
        
        loader = self.loaders[ext]
        try:
            print(f"正在加载文件: {file_path}")
            documents = loader.load(file_path)
            print(f"成功加载 {len(documents)} 个文档块")
            return documents
        except Exception as e:
            print(f"加载文件 {file_path} 失败: {str(e)}")
            return []
    
    async def load_document_async(self, file_path: str) -> List[Document]:
        """
        异步加载单个文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档列表
        """
        return await self.async_manager.run_in_executor(self.load_document, file_path)
    
    def load_all_documents(self) -> Dict[str, List[Document]]:
        """
        加载所有支持的文档
        
        Returns:
            文件路径到文档列表的映射
        """
        all_documents = {}
        supported_files = self.find_supported_files()
        
        if not supported_files:
            print(f"在 {self.asset_dir} 中没有找到支持的文件")
            return all_documents
        
        print(f"找到 {len(supported_files)} 个支持的文件")
        
        for file_path in supported_files:
            documents = self.load_document(file_path)
            if documents:
                all_documents[file_path] = documents
        
        return all_documents
    
    async def load_all_documents_async(self) -> Dict[str, List[Document]]:
        """
        异步加载所有支持的文档
        
        Returns:
            文件路径到文档列表的映射
        """
        all_documents = {}
        supported_files = self.find_supported_files()
        
        if not supported_files:
            print(f"在 {self.asset_dir} 中没有找到支持的文件")
            return all_documents
        
        print(f"找到 {len(supported_files)} 个支持的文件")
        
        # 创建文件加载任务
        tasks = []
        for file_path in supported_files:
            tasks.append((file_path, self.load_document_async(file_path)))
        
        # 等待所有加载完成
        for file_path, task in tasks:
            documents = await task
            if documents:
                all_documents[file_path] = documents
        
        return all_documents
    
    def store_documents(self, documents: List[Document]) -> List[str]:
        """
        将文档存储到向量数据库
        
        Args:
            documents: 文档列表
            
        Returns:
            存储的文档ID列表
        """
        if not documents:
            return []
        
        try:
            print(f"正在存储 {len(documents)} 个文档到向量数据库...")
            doc_ids = self.vector_store.add_documents(documents)
            print(f"成功存储 {len(doc_ids)} 个文档")
            return doc_ids
        except Exception as e:
            print(f"存储文档失败: {str(e)}")
            return []
    
    def store_documents_batch(self, documents: List[Document], batch_size: int = 50) -> List[str]:
        """
        使用批处理方式存储文档（同步实现）
        
        Args:
            documents: 文档列表
            batch_size: 批处理大小
            
        Returns:
            存储的文档ID列表
        """
        if not documents:
            return []
        
        try:
            # 使用批处理优化器添加文档
            return self.batch_optimizer.add_documents_batch_sync(
                documents, 
                batch_size=batch_size,
                save_interval=5
            )
        except Exception as e:
            print(f"存储文档失败: {str(e)}")
            return []
    
    def search(self, query: str, k: int = 3, **kwargs) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query: 搜索查询
            k: 返回结果数量
            **kwargs: 其他搜索参数
            
        Returns:
            搜索结果列表
        """
        try:
            print(f"\n搜索查询: '{query}'")
            print(f"搜索参数: k={k}, {kwargs}")
            
            results = self.vector_store.search(query, k=k, **kwargs)
            
            print(f"找到 {len(results)} 个相关文档:")
            for i, result in enumerate(results, 1):
                doc = result["document"]
                source = doc.metadata.get("source", "未知源")
                file_name = doc.metadata.get("file_name", source)
                chunk_index = doc.metadata.get("chunk_index", 0)
                total_chunks = doc.metadata.get("total_chunks", 1)
                
                print(f"\n结果 {i}:")
                print(f"源文件: {file_name}")
                print(f"块索引: {chunk_index + 1}/{total_chunks}")
                print(f"相似度分数: {result['score']:.4f}")
                print(f"内容片段: {doc.content[:100]}...")
            
            return results
        except Exception as e:
            print(f"搜索失败: {str(e)}")
            return []
    
    def list_sources(self) -> List[str]:
        """
        列出所有文档源
        
        Returns:
            文档源列表
        """
        try:
            sources = self.vector_store.list_sources()
            print(f"\n当前存储的文档源 ({len(sources)}):")
            for source in sources:
                # 获取源的文件名
                file_name = os.path.basename(source)
                # 获取该源的文档数量
                doc_count = len(self.vector_store.get_documents_by_source(source))
                print(f"- {file_name} (文档数量: {doc_count})")
            return sources
        except Exception as e:
            print(f"列出文档源失败: {str(e)}")
            return []
    
    def delete_by_source(self, source: str) -> bool:
        """
        根据源删除文档
        
        Args:
            source: 文档源
            
        Returns:
            是否删除成功
        """
        try:
            print(f"正在删除源为 '{source}' 的文档...")
            result = self.vector_store.delete_by_source(source)
            if result:
                print(f"成功删除源为 '{source}' 的所有文档")
            else:
                print(f"未找到源为 '{source}' 的文档或删除失败")
            return result
        except Exception as e:
            print(f"删除文档失败: {str(e)}")
            return False
    
    def show_vector_store_stats(self):
        """
        显示向量存储统计信息
        """
        try:
            all_docs = self.vector_store.list_documents()
            sources = self.vector_store.list_sources()
            
            print(f"\n=== 向量存储统计信息 ===")
            print(f"总文档数量: {len(all_docs)}")
            print(f"文档源数量: {len(sources)}")
            print(f"持久化目录: {self.vector_store.persist_directory}")
            
            # 显示每个源的文档数量
            if sources:
                print("\n各文档源统计:")
                for source in sources:
                    source_docs = self.vector_store.get_documents_by_source(source)
                    print(f"- {os.path.basename(source)}: {len(source_docs)} 个文档")
        except Exception as e:
            print(f"获取统计信息失败: {str(e)}")
    
    def run_demo(self):
        """
        使用Loop优化运行完整的演示流程
        """
        # 使用Loop优化运行演示
        process_with_loop(self.run_demo_async())
    
    async def run_demo_async(self):
        """
        异步运行完整的演示流程
        """
        print("=" * 60)
        print("        RAG 系统演示 (异步模式)        ")
        print("=" * 60)
        
        # 1. 异步加载所有文档
        print("\n1. 扫描并异步加载文档...")
        all_documents = await self.load_all_documents_async()
        
        # 2. 异步存储文档到向量数据库
        total_documents = sum(len(docs) for docs in all_documents.values())
        if total_documents > 0:
            print(f"\n2. 准备异步存储 {total_documents} 个文档...")
            
            # 对于大型文档（如三国演义.txt），使用更大的批处理大小
            batch_size = 100 if total_documents > 500 else 50
            
            # 合并所有文档以便批量处理
            all_docs_list = []
            file_info = []
            
            for file_path, documents in all_documents.items():
                file_name = os.path.basename(file_path)
                print(f"\n准备处理文件: {file_name} (包含 {len(documents)} 个文档块)")
                all_docs_list.extend(documents)
                file_info.append((file_name, len(documents)))
            
            # 显示文件信息摘要
            print(f"\n文件处理摘要:")
            for file_name, doc_count in file_info:
                print(f"- {file_name}: {doc_count} 个文档块")
            print(f"总计: {total_documents} 个文档块")
            
            # 异步批量存储所有文档
            await self.store_documents_async(all_docs_list, batch_size=batch_size)
        else:
            print("没有文档需要存储")
        
        # 3. 显示统计信息
        self.show_vector_store_stats()
        
        # 4. 列出所有文档源
        self.list_sources()
        
        # 5. 执行示例搜索
        print("\n3. 执行示例搜索...")
        example_queries = [
            "项目的主要功能是什么？",
            "如何使用这个系统？",
            "有哪些技术细节？"
        ]
        
        for query in example_queries:
            print("-" * 40)
            await self.async_vector_store.search_async(query, k=2)
        
        print("\n" + "=" * 60)
        print("演示完成！您可以使用以下命令进行更多操作:")
        print("- 搜索: python faiss_demo.py --search '查询内容'")
        print("- 列出源: python faiss_demo.py --list-sources")
        print("- 删除源: python faiss_demo.py --delete-source '源路径'")
        print("- 重新导入: python faiss_demo.py")
        print("=" * 60)
    
    def process_large_file(self, file_path: str, batch_size: int = 100) -> List[str]:
        """
        处理大型文件（同步批处理实现）
        
        Args:
            file_path: 文件路径
            batch_size: 批处理大小
            
        Returns:
            存储的文档ID列表
        """
        print(f"\n开始处理大型文件: {os.path.basename(file_path)}")
        print(f"批处理大小设置为: {batch_size}")
        
        try:
            # 直接加载文件
            documents = self.load_document(file_path)
            
            if not documents:
                print("未加载到任何文档")
                return []
            
            print(f"成功加载 {len(documents)} 个文档块，开始使用批处理存储...")
            
            # 使用批处理存储文档
            return self.store_documents_batch(documents, batch_size=batch_size)
        except Exception as e:
            print(f"处理文件时出错: {e}")
            raise


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='RAG系统演示')
    parser.add_argument('--asset-dir', default='./asset', help='资产目录路径')
    parser.add_argument('--vector-store-dir', default='./db/vector_store', help='向量存储目录路径')
    parser.add_argument('--search', help='执行搜索查询')
    parser.add_argument('--list-sources', action='store_true', help='列出所有文档源')
    parser.add_argument('--delete-source', help='删除指定源的所有文档')
    parser.add_argument('--search-k', type=int, default=3, help='搜索结果数量')
    parser.add_argument('--large-file', help='处理单个大型文件（使用异步优化）')
    parser.add_argument('--batch-size', type=int, default=100, help='处理大型文件时的批处理大小')
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    try:
        # 创建RAG演示实例
        demo = RAGDemo(args.asset_dir, args.vector_store_dir)
        
        # 根据命令行参数执行不同操作
        if args.search:
            # 执行搜索
            demo.search(args.search, k=args.search_k)
        elif args.list_sources:
            # 列出所有文档源
            demo.list_sources()
        elif args.delete_source:
            # 删除指定源的文档
            demo.delete_by_source(args.delete_source)
        elif args.large_file:
            # 同步处理大型文件
            print(f"使用批处理处理大型文件: {args.large_file}")
            print(f"批处理大小设置为: {args.batch_size}")
            demo.process_large_file(args.large_file, batch_size=args.batch_size)
        else:
            # 运行完整演示（默认使用异步模式）
            demo.run_demo()
            
    except KeyboardInterrupt:
        print("\n操作被用户中断")
    except Exception as e:
        print(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())