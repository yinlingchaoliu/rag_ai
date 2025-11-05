#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
线程池+Loop组合方案
提供异步事件循环和线程池的混合执行器
专为IO密集型和CPU密集型任务的混合处理优化
"""

import asyncio
import threading
import time
from typing import List, Dict, Any, Callable, Optional, Tuple, Union
from concurrent.futures import Future, ThreadPoolExecutor

from .loop_manager import LoopManager
from .thread_pool import ThreadPoolManager


class HybridExecutor:
    """
    混合执行器
    集成事件循环和线程池，提供高效的混合并发处理机制
    """
    
    def __init__(self, 
                 max_workers: int = None,
                 thread_name_prefix: str = "hybrid",
                 use_background_loop: bool = False,
                 loop_name: str = None):
        """
        初始化混合执行器
        
        Args:
            max_workers: 线程池最大工作线程数
            thread_name_prefix: 线程名称前缀
            use_background_loop: 是否使用后台事件循环
            loop_name: 后台循环名称
        """
        # 初始化线程池
        self.thread_pool = ThreadPoolManager.get_pool(
            pool_name=f"{thread_name_prefix}_pool",
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix
        )
        
        self.use_background_loop = use_background_loop
        self.loop_name = loop_name
        
        # 如果使用后台循环，启动它
        if use_background_loop:
            self.loop_name = LoopManager.start_background_loop(loop_name)
            self.loop = LoopManager.get_background_loop(self.loop_name)
        else:
            self.loop = LoopManager.get_loop()
        
        # 任务追踪
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._tasks_lock = threading.RLock()
        
        print(f"[混合执行器] 初始化完成 - 线程池: {max_workers}线程, 后台循环: {use_background_loop}")
    
    async def run_in_thread(self, func: Callable, *args, **kwargs) -> Any:
        """
        在线程池中运行同步函数（异步版本）
        
        Args:
            func: 同步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
        """
        # 创建future
        future = self.thread_pool.submit(func, *args, **kwargs)
        
        # 转换为asyncio.Future
        loop = LoopManager.get_loop()
        async_future = loop.create_future()
        
        def _on_completion(future):
            try:
                result = future.result()
                loop.call_soon_threadsafe(async_future.set_result, result)
            except Exception as e:
                loop.call_soon_threadsafe(async_future.set_exception, e)
        
        future.add_done_callback(_on_completion)
        
        return await async_future
    
    def run_in_thread_sync(self, func: Callable, *args, **kwargs) -> Any:
        """
        在线程池中运行同步函数（同步版本）
        
        Args:
            func: 同步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            函数执行结果
        """
        future = self.thread_pool.submit(func, *args, **kwargs)
        return future.result()
    
    async def run_async(self, coro) -> Any:
        """
        运行异步协程
        
        Args:
            coro: 异步协程对象
            
        Returns:
            协程执行结果
        """
        if self.use_background_loop:
            # 在后台循环中运行
            future = LoopManager.run_in_background_loop(self.loop_name, coro)
            return await self._wrap_concurrent_future(future)
        else:
            # 在当前循环中运行
            return await coro
    
    async def _wrap_concurrent_future(self, concurrent_future: Future) -> Any:
        """
        包装concurrent.futures.Future为asyncio.Future
        
        Args:
            concurrent_future: concurrent.futures.Future对象
            
        Returns:
            结果
        """
        loop = LoopManager.get_loop()
        async_future = loop.create_future()
        
        def _on_completion(future):
            try:
                result = future.result()
                loop.call_soon_threadsafe(async_future.set_result, result)
            except Exception as e:
                loop.call_soon_threadsafe(async_future.set_exception, e)
        
        concurrent_future.add_done_callback(_on_completion)
        
        return await async_future
    
    async def run_hybrid_task(self, 
                             io_bound_func: Optional[Callable] = None,
                             io_bound_args: Tuple = (),
                             io_bound_kwargs: Dict = None,
                             cpu_bound_func: Optional[Callable] = None,
                             cpu_bound_args: Tuple = (),
                             cpu_bound_kwargs: Dict = None,
                             task_id: str = None) -> Dict[str, Any]:
        """
        运行混合任务（IO密集型和CPU密集型任务的组合）
        
        Args:
            io_bound_func: IO密集型函数（可以是同步或异步）
            io_bound_args: IO函数参数
            io_bound_kwargs: IO函数关键字参数
            cpu_bound_func: CPU密集型函数
            cpu_bound_args: CPU函数参数
            cpu_bound_kwargs: CPU函数关键字参数
            task_id: 任务ID
            
        Returns:
            包含io_result和cpu_result的字典
        """
        if io_bound_kwargs is None:
            io_bound_kwargs = {}
        if cpu_bound_kwargs is None:
            cpu_bound_kwargs = {}
        
        if task_id is None:
            task_id = f"task_{int(time.time())}_{threading.get_ident()}"
        
        results = {}
        
        # 执行IO密集型任务
        if io_bound_func:
            if asyncio.iscoroutinefunction(io_bound_func):
                results['io_result'] = await self.run_async(
                    io_bound_func(*io_bound_args, **io_bound_kwargs)
                )
            else:
                results['io_result'] = await self.run_in_thread(
                    io_bound_func, *io_bound_args, **io_bound_kwargs
                )
        
        # 执行CPU密集型任务
        if cpu_bound_func:
            results['cpu_result'] = await self.run_in_thread(
                cpu_bound_func, *cpu_bound_args, **cpu_bound_kwargs
            )
        
        return results
    
    async def map_in_threads(self, func: Callable, 
                           *iterables, 
                           chunksize: int = 1) -> List[Any]:
        """
        在多个线程中并行映射函数
        
        Args:
            func: 要执行的函数
            *iterables: 可迭代对象
            chunksize: 块大小
            
        Returns:
            结果列表
        """
        # 收集所有任务
        futures = []
        args_list = list(zip(*iterables))
        
        # 分块处理
        for i in range(0, len(args_list), chunksize):
            chunk = args_list[i:i+chunksize]
            # 为每个块创建一个任务
            for args in chunk:
                future = self.run_in_thread(func, *args)
                futures.append(future)
            
            # 等待当前块完成
            if chunksize > 1:
                await asyncio.gather(*futures[-len(chunk):])
        
        # 等待所有任务完成
        return await asyncio.gather(*futures)
    
    async def process_batch_with_pipeline(self, 
                                        items: List[Any],
                                        stages: List[Callable],
                                        max_concurrency: int = None) -> List[Any]:
        """
        管道式批处理
        
        Args:
            items: 要处理的项目列表
            stages: 处理阶段函数列表
            max_concurrency: 最大并发数
            
        Returns:
            处理后的结果列表
        """
        if not stages:
            return items
        
        # 设置并发限制
        semaphore = None
        if max_concurrency:
            semaphore = asyncio.Semaphore(max_concurrency)
        
        async def _process_item(item):
            result = item
            for stage in stages:
                if semaphore:
                    async with semaphore:
                        if asyncio.iscoroutinefunction(stage):
                            result = await stage(result)
                        else:
                            result = await self.run_in_thread(stage, result)
                else:
                    if asyncio.iscoroutinefunction(stage):
                        result = await stage(result)
                    else:
                        result = await self.run_in_thread(stage, result)
            return result
        
        # 并行处理所有项目
        tasks = [_process_item(item) for item in items]
        return await asyncio.gather(*tasks)
    
    def shutdown(self, wait: bool = True) -> None:
        """
        关闭混合执行器
        
        Args:
            wait: 是否等待所有任务完成
        """
        # 关闭线程池
        pool_name = self.thread_pool._thread_name_prefix.replace("_", "") + "_pool"
        ThreadPoolManager.shutdown(pool_name, wait=wait)
        
        # 关闭后台循环
        if self.use_background_loop and self.loop_name:
            LoopManager.stop_background_loop(self.loop_name)
        
        # 清理任务
        with self._tasks_lock:
            for task in self._active_tasks.values():
                if not task.done():
                    task.cancel()
            self._active_tasks.clear()
        
        print("[混合执行器] 已关闭")


class HybridBatchProcessor:
    """
    混合批处理器
    专为大批量数据处理优化的混合执行器
    """
    
    def __init__(self, 
                 executor: HybridExecutor = None,
                 batch_size: int = 100,
                 max_concurrency: int = None):
        """
        初始化批处理器
        
        Args:
            executor: 混合执行器实例
            batch_size: 批处理大小
            max_concurrency: 最大并发数
        """
        self.executor = executor or HybridExecutor()
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
    
    async def process_batch(self, 
                           items: List[Any],
                           process_func: Callable,
                           progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        批量处理项目
        
        Args:
            items: 要处理的项目列表
            process_func: 处理函数
            progress_callback: 进度回调函数
            
        Returns:
            处理后的结果列表
        """
        if not items:
            return []
        
        total = len(items)
        all_results = []
        start_time = time.time()
        
        # 分批次处理
        for i in range(0, total, self.batch_size):
            batch = items[i:i+self.batch_size]
            current_batch = i // self.batch_size + 1
            total_batches = (total + self.batch_size - 1) // self.batch_size
            
            print(f"[混合批处理] 处理批次 {current_batch}/{total_batches} ({len(batch)} 项目)")
            
            # 并行处理当前批次
            results = await self._process_current_batch(batch, process_func)
            all_results.extend(results)
            
            # 调用进度回调
            if progress_callback:
                processed = min(i + self.batch_size, total)
                elapsed = time.time() - start_time
                progress_callback(processed, total, elapsed)
            
            # 显示进度
            processed = min(i + self.batch_size, total)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            
            print(f"  ✓ 批次完成 - 进度: {processed}/{total} ({processed/total*100:.1f}%) - "
                  f"速度: {rate:.1f}项目/秒")
        
        return all_results
    
    async def _process_current_batch(self, 
                                    batch: List[Any],
                                    process_func: Callable) -> List[Any]:
        """
        处理当前批次
        
        Args:
            batch: 批次项目
            process_func: 处理函数
            
        Returns:
            处理结果
        """
        if asyncio.iscoroutinefunction(process_func):
            # 异步函数处理
            tasks = [process_func(item) for item in batch]
        else:
            # 同步函数在线程池中处理
            tasks = [self.executor.run_in_thread(process_func, item) for item in batch]
        
        # 设置并发限制
        if self.max_concurrency and len(tasks) > self.max_concurrency:
            # 分批执行以限制并发
            results = []
            for i in range(0, len(tasks), self.max_concurrency):
                chunk = tasks[i:i+self.max_concurrency]
                results.extend(await asyncio.gather(*chunk))
            return results
        else:
            # 直接并行执行
            return await asyncio.gather(*tasks)
    
    def shutdown(self, wait: bool = True) -> None:
        """
        关闭批处理器
        
        Args:
            wait: 是否等待所有任务完成
        """
        self.executor.shutdown(wait=wait)


# 便捷函数
def create_hybrid_executor(max_workers: int = None, 
                          use_background_loop: bool = False) -> HybridExecutor:
    """
    创建混合执行器的便捷函数
    """
    return HybridExecutor(
        max_workers=max_workers,
        use_background_loop=use_background_loop
    )


def create_hybrid_batch_processor(batch_size: int = 100, 
                                 max_concurrency: int = None) -> HybridBatchProcessor:
    """
    创建混合批处理器的便捷函数
    """
    return HybridBatchProcessor(
        batch_size=batch_size,
        max_concurrency=max_concurrency
    )