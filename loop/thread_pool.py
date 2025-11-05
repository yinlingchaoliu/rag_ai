#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程池管理模块
提供高效的线程池创建、管理和任务调度功能
"""

import concurrent.futures
import threading
import time
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from functools import wraps


class ThreadPoolManager:
    """
    线程池管理器
    提供线程池的创建、管理和任务调度功能
    """
    
    # 全局线程池字典
    _pools: Dict[str, concurrent.futures.ThreadPoolExecutor] = {}
    _pools_lock = threading.RLock()
    
    # 默认线程池
    _default_pool: Optional[concurrent.futures.ThreadPoolExecutor] = None
    
    @classmethod
    def get_pool(cls, pool_name: str = "default", 
                 max_workers: int = None, 
                 thread_name_prefix: str = "") -> concurrent.futures.ThreadPoolExecutor:
        """
        获取或创建线程池
        
        Args:
            pool_name: 线程池名称
            max_workers: 最大工作线程数，None则自动计算
            thread_name_prefix: 线程名称前缀
            
        Returns:
            线程池执行器
        """
        with cls._pools_lock:
            # 如果线程池不存在则创建
            if pool_name not in cls._pools:
                # 自动计算最大工作线程数
                if max_workers is None:
                    import multiprocessing
                    max_workers = multiprocessing.cpu_count() * 4
                
                # 创建线程池
                pool = concurrent.futures.ThreadPoolExecutor(
                    max_workers=max_workers,
                    thread_name_prefix=thread_name_prefix or f"{pool_name}_thread"
                )
                cls._pools[pool_name] = pool
                
                # 如果是默认线程池，保存引用
                if pool_name == "default":
                    cls._default_pool = pool
            
            return cls._pools[pool_name]
    
    @classmethod
    def submit(cls, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        提交任务到默认线程池
        
        Args:
            func: 要执行的函数
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
        提交任务到指定线程池
        
        Args:
            pool_name: 线程池名称
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            未来对象
            
        Raises:
            ValueError: 如果线程池不存在
        """
        with cls._pools_lock:
            if pool_name not in cls._pools:
                raise ValueError(f"Thread pool '{pool_name}' not found")
        
        return cls._pools[pool_name].submit(func, *args, **kwargs)
    
    @classmethod
    def map(cls, func: Callable, 
            *iterables, 
            timeout: float = None, 
            chunksize: int = 1, 
            pool_name: str = "default") -> List[Any]:
        """
        映射函数到可迭代对象
        
        Args:
            func: 要执行的函数
            *iterables: 可迭代对象
            timeout: 超时时间
            chunksize: 块大小
            pool_name: 线程池名称
            
        Returns:
            结果列表
        """
        pool = cls.get_pool(pool_name)
        return list(pool.map(func, *iterables, timeout=timeout, chunksize=chunksize))
    
    @classmethod
    def submit_batch(cls, tasks: List[Tuple[Callable, Tuple, Dict]], 
                    pool_name: str = "default",
                    max_concurrency: int = None) -> List[concurrent.futures.Future]:
        """
        批量提交任务
        
        Args:
            tasks: 任务列表，每个任务是(func, args, kwargs)的元组
            pool_name: 线程池名称
            max_concurrency: 最大并发数，None则不限制
            
        Returns:
            未来对象列表
        """
        pool = cls.get_pool(pool_name)
        futures = []
        
        # 限制最大并发数
        if max_concurrency is not None:
            import queue
            task_queue = queue.Queue()
            
            # 提交第一批任务
            for i, (func, args, kwargs) in enumerate(tasks[:max_concurrency]):
                future = pool.submit(func, *args, **kwargs)
                futures.append(future)
                task_queue.put(i)
            
            # 逐个提交剩余任务
            for i, (func, args, kwargs) in enumerate(tasks[max_concurrency:], max_concurrency):
                # 等待一个任务完成
                completed_idx = task_queue.get()
                futures.append(pool.submit(func, *args, **kwargs))
                task_queue.put(i)
        else:
            # 不限制并发数，直接提交所有任务
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
        关闭线程池
        
        Args:
            pool_name: 线程池名称，None表示关闭所有线程池
            wait: 是否等待所有任务完成
            
        Returns:
            是否成功关闭
        """
        with cls._pools_lock:
            if pool_name is None:
                # 关闭所有线程池
                for name, pool in list(cls._pools.items()):
                    pool.shutdown(wait=wait)
                    del cls._pools[name]
                
                # 重置默认线程池
                cls._default_pool = None
                return True
            else:
                # 关闭指定线程池
                if pool_name in cls._pools:
                    cls._pools[pool_name].shutdown(wait=wait)
                    del cls._pools[pool_name]
                    
                    # 如果是默认线程池，重置引用
                    if pool_name == "default":
                        cls._default_pool = None
                    
                    return True
                return False
    
    @classmethod
    def get_pool_stats(cls, pool_name: str = "default") -> Dict[str, Any]:
        """
        获取线程池统计信息
        
        Args:
            pool_name: 线程池名称
            
        Returns:
            统计信息字典
        """
        with cls._pools_lock:
            if pool_name not in cls._pools:
                raise ValueError(f"Thread pool '{pool_name}' not found")
            
            pool = cls._pools[pool_name]
            
            # 注意：ThreadPoolExecutor不提供直接访问内部状态的方法
            # 这里返回有限的信息
            return {
                "pool_name": pool_name,
                "max_workers": getattr(pool, "_max_workers", "unknown"),
                "thread_name_prefix": getattr(pool, "_thread_name_prefix", "unknown"),
                "running": not getattr(pool, "_shutdown", False)
            }
    
    @classmethod
    def list_pools(cls) -> List[str]:
        """
        列出所有可用的线程池
        
        Returns:
            线程池名称列表
        """
        with cls._pools_lock:
            return list(cls._pools.keys())


def thread_pool_decorator(pool_name: str = "default"):
    """
    将函数装饰为在线程池中执行
    
    Args:
        pool_name: 线程池名称
        
    Returns:
        装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            future = ThreadPoolManager.submit_to_pool(pool_name, func, *args, **kwargs)
            return future.result()  # 阻塞等待结果
        
        # 也提供一个非阻塞版本
        def wrapper_run_async(*args, **kwargs):
            return ThreadPoolManager.submit_to_pool(pool_name, func, *args, **kwargs)
        
        wrapper.run_async = wrapper_run_async
        return wrapper
    
    return decorator


def async_thread_pool_decorator(pool_name: str = "default"):
    """
    将函数装饰为返回Future对象的异步版本
    
    Args:
        pool_name: 线程池名称
        
    Returns:
        装饰后的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return ThreadPoolManager.submit_to_pool(pool_name, func, *args, **kwargs)
        
        return wrapper
    
    return decorator


# 便捷函数
def get_thread_pool(pool_name: str = "default", 
                   max_workers: int = None) -> concurrent.futures.ThreadPoolExecutor:
    """获取线程池的便捷函数"""
    return ThreadPoolManager.get_pool(pool_name, max_workers)


def submit_task(func: Callable, *args, **kwargs) -> concurrent.futures.Future:
    """提交任务到默认线程池的便捷函数"""
    return ThreadPoolManager.submit(func, *args, **kwargs)


def shutdown_all_pools(wait: bool = True) -> None:
    """关闭所有线程池的便捷函数"""
    ThreadPoolManager.shutdown(wait=wait)