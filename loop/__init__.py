#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loop模块 - 高性能并发编程工具集

提供高效的事件循环、线程池、进程池和混合执行器管理
为IO密集型和CPU密集型任务提供统一的并发处理方案
"""

# 导出核心组件
from .loop_manager import (
    LoopManager,
    get_event_loop,
    run_coroutine,
    create_task
)

from .thread_pool import (
    ThreadPoolManager,
    thread_pool_decorator,
    async_thread_pool_decorator,
    get_thread_pool,
    submit_task,
    shutdown_all_pools
)

from .process_pool import (
    ProcessPoolManager,
    process_pool_decorator,
    async_process_pool_decorator,
    get_process_pool,
    submit_process_task,
    shutdown_all_process_pools,
    set_process_start_method
)

from .hybrid_executor import (
    HybridExecutor,
    HybridBatchProcessor,
    create_hybrid_executor,
    create_hybrid_batch_processor
)

# 版本信息
__version__ = "1.0.0"
__all__ = [
    # Loop Manager
    "LoopManager",
    "get_event_loop",
    "run_coroutine",
    "create_task",
    
    # Thread Pool
    "ThreadPoolManager",
    "thread_pool_decorator",
    "async_thread_pool_decorator",
    "get_thread_pool",
    "submit_task",
    "shutdown_all_pools",
    
    # Process Pool
    "ProcessPoolManager",
    "process_pool_decorator",
    "async_process_pool_decorator",
    "get_process_pool",
    "submit_process_task",
    "shutdown_all_process_pools",
    "set_process_start_method",
    
    # Hybrid Executor
    "HybridExecutor",
    "HybridBatchProcessor",
    "create_hybrid_executor",
    "create_hybrid_batch_processor"
]