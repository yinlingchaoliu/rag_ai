#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loop优化模块 - 基于批处理的高性能封装

提供基于批处理的同步优化方法，
专为大型文件处理和向量数据库操作优化。
"""

import os
import time
import sys
from typing import List, Dict, Any


class VectorStoreBatchOptimizer:
    """
    简单高效的向量存储批处理优化器
    使用纯同步方法，避免异步复杂性
    """
    
    def __init__(self, vector_store):
        """
        初始化向量存储批处理优化器
        
        Args:
            vector_store: 向量存储实例
        """
        self.vector_store = vector_store
        print(f"[批处理优化器] 已初始化向量存储: {vector_store.__class__.__name__}")
    
    def add_documents_batch_sync(self, documents: List[Any], 
                                batch_size: int = 100,
                                save_interval: int = 3) -> List[str]:
        """
        使用批处理方式添加文档（纯同步实现）
        
        Args:
            documents: 文档列表
            batch_size: 批处理大小
            save_interval: 保存间隔（批次）
            
        Returns:
            添加的文档ID列表
        """
        if not documents:
            return []
        
        all_doc_ids = []
        total = len(documents)
        total_batches = (total + batch_size - 1) // batch_size
        start_time = time.time()
        
        print(f"[批处理优化] 开始处理 {total} 个文档，批大小: {batch_size}")
        
        # 分批次处理文档
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            current_batch = i // batch_size + 1
            
            print(f"  处理批次 {current_batch}/{total_batches} ({len(batch)} 文档)")
            
            # 决定是否保存
            should_save = current_batch % save_interval == 0 or current_batch == total_batches
            
            # 直接同步调用add_documents方法
            try:
                # 尝试带save参数调用
                doc_ids = self.vector_store.add_documents(batch, save=should_save)
            except TypeError:
                # 如果不支持save参数，则直接调用
                doc_ids = self.vector_store.add_documents(batch)
            
            all_doc_ids.extend(doc_ids)
            
            # 显示进度
            elapsed = time.time() - start_time
            processed = min(i + batch_size, total)
            rate = processed / elapsed if elapsed > 0 else 0
            
            print(f"  ✓ 批次完成 - 进度: {processed}/{total} ({processed/total*100:.1f}%) - "
                  f"速度: {rate:.1f}文档/秒")
        
        print(f"\n[批处理优化] 处理完成！共添加 {len(all_doc_ids)} 个文档")
        return all_doc_ids


# 便捷函数
def create_batch_optimizer(vector_store):
    """
    创建向量存储批处理优化器
    
    Args:
        vector_store: 向量存储实例
        
    Returns:
        VectorStoreBatchOptimizer实例
    """
    return VectorStoreBatchOptimizer(vector_store)


def optimize_vector_store(vector_store):
    """
    快速创建向量存储优化器的别名
    
    Args:
        vector_store: 向量存储实例
        
    Returns:
        VectorStoreBatchOptimizer实例
    """
    return create_batch_optimizer(vector_store)