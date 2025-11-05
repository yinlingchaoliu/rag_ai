#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多进程管理模块
提供高效的进程池创建、管理和任务调度功能
"""

import concurrent.futures
import multiprocessing
import threading
import time
import os
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from functools import wraps


class ProcessPoolManager:
    """
    进程池管理器
    提供进程池的创建、管理和任务调度功能
    """
    
    # 全局进程池字典
    _pools: Dict[str, concurrent.futures.ProcessPoolExecutor] = {}
    _pools_lock = threading.RLock()
    
    # 默认进程池
    _default_pool: Optional[concurrent.futures.ProcessPoolExecutor] = None
    
    # 进程启动方法
    _start_method: str = 'fork'  # 默认使用fork
    
    @classmethod
    def set_start_method(cls, method: str) -> None:
        """
        设置进程启动方法
        
        Args:
            method: 启动方法，可以是 'fork', 'spawn', 或 'forkserver'
        """
        valid_methods = ['fork', 'spawn', 'forkserver']
        if method not in valid_methods:
            raise ValueError(f"Invalid start method: {method}. Must be one of {valid_methods}")
        
        cls._start_method = method
    
    @classmethod
    def get_pool(cls, pool_name: str = "default", 
                 max_workers: int = None, 
                 initializer: Callable = None, 
                 initargs: Tuple = ()) -> concurrent.futures.ProcessPoolExecutor:
        """
        获取或创建进程池
        
        Args:
            pool_name: 进程池名称
            max_workers: 最大工作进程数，None则使用CPU核心数
            initializer: 进程初始化函数
            initargs: 初始化参数
            
        Returns:
            进程池执行器
        """
        with cls._pools_lock:
            # 如果进程池不存在则创建
            if pool_name not in cls._pools:
                # 自动计算最大工作进程数
                if max_workers is None:
                    max_workers = multiprocessing.cpu_count()
                
                # 创建进程池
                try:
                    # 尝试设置启动方法
                    multiprocessing.set_start_method(cls._start_method, force=True)
                except RuntimeError:
                    # 如果已经设置过，忽略错误
                    pass
                
                pool = concurrent.futures.ProcessPoolExecutor(
                    max_workers=max_workers,
                    initializer=initializer,
                    initargs=initargs
                )
                cls._pools[pool_name] = pool
                
                # 如果是默认进程池，保存引用
                if pool_name == "default":
                    cls._default_pool = pool
            
            return cls._pools[pool_name]
    
    @classmethod
    def submit(cls, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        提交任务到默认进程池
        
        Args:
            func: 要执行的函数（注意：函数必须是可序列化的）
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            未来对象
        """
        return cls.get_pool().submit(func, *args, **kwargs)
    
    @classmethod
    def submit_to_pool(cls, pool_name: str, 
                       func: Callable, 
                       *args, **kwargs) -> concurrent.futures.Future:
        """
        提交任务到指定进程池
        
        Args:
            pool_name: 进程池名称
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            未来对象
            
        Raises:
            ValueError: 如果进程池不存在
        """
        with cls._pools_lock:
            if pool_name not in cls._pools:
                raise ValueError(f"Process pool '{pool_name}' not found")
        
        return cls._pools[pool_name].submit(func, *args, **kwargs)
    
    @classmethod
    def map(cls, func: Callable, 
            *iterables, 
            timeout: float = None, 
            chunksize: int = None, 
            pool_name: str = "default") -> List[Any]:
        """
        映射函数到可迭代对象
        
        Args:
            func: 要执行的函数
            *iterables: 可迭代对象
            timeout: 超时时间
            chunksize: 块大小，None则自动计算
            pool_name: 进程池名称
            
        Returns:
            结果列表
        """
        pool = cls.get_pool(pool_name)
        return list(pool.map(func, *iterables, timeout=timeout, chunksize=chunksize))
    
    @classmethod
    def submit_batch(cls, tasks: List[Tuple[Callable, Tuple, Dict]], 
                    pool_name: str = "default") -> List[concurrent.futures.Future]:
        """
        批量提交任务
        
        Args:
            tasks: 任务列表，每个任务是(func, args, kwargs)的元组
            pool_name: 进程池名称
            
        Returns:
            未来对象列表
        """
        pool = cls.get_pool(pool_name)
        futures = []
        
        # 提交所有任务
        for func, args, kwargs in tasks:
            future = pool.submit(func, *args, **kwargs)
            futures.append(future)
        
        return futures
    
    @classmethod
    def wait_for_all(cls, futures: List[concurrent.futures.Future], 
                    timeout: float = None) -> List[Any]:
        """
        等待所有任务完成并获取结果
        
        Args:
            futures: 未来对象列表
            timeout: 超时时间
            
        Returns:
            结果列表
        """
        completed, _ = concurrent.futures.wait(
            futures, 
            timeout=timeout,
            return_when=concurrent.futures.ALL_COMPLETED
        )
        
        results = []
        for future in completed:
            try:
                results.append(future.result())
            except Exception as e:
                results.append(e)
        
        return results
    
    @classmethod
    def shutdown(cls, pool_name: str = None, wait: bool = True) -> bool:
        """
        关闭进程池
        
        Args:
            pool_name: 进程池名称，None表示关闭所有进程池
            wait: 是否等待所有任务完成
            
        Returns:
            是否成功关闭
        """
        with cls._pools_lock:
            if pool_name is None:
                # 关闭所有进程池
                for name, pool in list(cls._pools.items()):
                    pool.shutdown(wait=wait)
                    del cls._pools[name]
                
                # 重置默认进程池
                cls._default_pool = None
                return True
            else:
                # 关闭指定进程池
                if pool_name in cls._pools:
                    cls._pools[pool_name].shutdown(wait=wait)
                    del cls._pools[pool_name]
                    
                    # 如果是默认进程池，重置引用
                    if pool_name == "default":
                        cls._default_pool = None
                    
                    return True
                return False
    
    @classmethod
    def get_pool_stats(cls, pool_name: str = "default") -> Dict[str, Any]:
        """
        获取进程池统计信息
        
        Args:
            pool_name: 进程池名称
            
        Returns:
            统计信息字典
        """
        with cls._pools_lock:
            if pool_name not in cls._pools:
                raise ValueError(f"Process pool '{pool_name}' not found")
            
            pool = cls._pools[pool_name]
            
            return {
                "pool_name": pool_name,
                "max_workers": getattr(pool, "_max_workers", "unknown"),
                "start_method": cls._start_method,
                "running": not getattr(pool, "_shutdown", False),
                "current_process_id": os.getpid()
            }
    
    @classmethod
    def list_pools(cls) -> List[str]:
        """
        列出所有可用的进程池
        
        Returns:
            进程池名称列表
        """
        with cls._pools_lock:
            return list(cls._pools.keys())
    
    @classmethod
    def calculate_optimal_chunksize(cls, iterable_size: int, 
                                  max_workers: int = None, 
                                  pool_name: str = "default") -> int:
        """
        计算最佳的chunksize值
        
        Args:
            iterable_size: 可迭代对象的大小
            max_workers: 最大工作进程数
            pool_name: 进程池名称
            
        Returns:
            最佳chunksize
        """
        if max_workers is None:
            pool = cls.get_pool(pool_name)
            max_workers = getattr(pool, "_max_workers", multiprocessing.cpu_count())
        
        # 计算最佳chunksize
        chunksize, remainder = divmod(iterable_size, max_workers * 4)
        if remainder:
            chunksize += 1
        
        return max(1, chunksize)  # 至少为1


def process_pool_decorator(pool_name: str = "default"):
    """
    将函数装饰为在进程池中执行
    
    Args:
        pool_name: 进程池名称
        
    Returns:
        装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            future = ProcessPoolManager.submit_to_pool(pool_name, func, *args, **kwargs)
            return future.result()  # 阻塞等待结果
        
        # 也提供一个非阻塞版本
        def wrapper_run_async(*args, **kwargs):
            return ProcessPoolManager.submit_to_pool(pool_name, func, *args, **kwargs)
        
        wrapper.run_async = wrapper_run_async
        return wrapper
    
    return decorator


def async_process_pool_decorator(pool_name: str = "default"):
    """
    将函数装饰为返回Future对象的异步版本
    
    Args:
        pool_name: 进程池名称
        
    Returns:
        装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return ProcessPoolManager.submit_to_pool(pool_name, func, *args, **kwargs)
        
        return wrapper
    
    return decorator


# 便捷函数
def get_process_pool(pool_name: str = "default", 
                    max_workers: int = None) -> concurrent.futures.ProcessPoolExecutor:
    """获取进程池的便捷函数"""
    return ProcessPoolManager.get_pool(pool_name, max_workers)


def submit_process_task(func: Callable, *args, **kwargs) -> concurrent.futures.Future:
    """提交任务到默认进程池的便捷函数"""
    return ProcessPoolManager.submit(func, *args, **kwargs)


def shutdown_all_process_pools(wait: bool = True) -> None:
    """关闭所有进程池的便捷函数"""
    ProcessPoolManager.shutdown(wait=wait)


def set_process_start_method(method: str) -> None:
    """设置进程启动方法的便捷函数"""
    ProcessPoolManager.set_start_method(method)