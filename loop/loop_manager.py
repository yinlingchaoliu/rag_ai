#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loop高效管理类
提供事件循环的创建、管理、优化和生命周期控制
"""

import asyncio
import os
import threading
import time
from typing import Optional, Callable, Any, Dict


class LoopManager:
    """
    高效的事件循环管理器
    提供统一的事件循环创建、获取、管理和销毁接口
    """
    
    # 线程本地存储，用于存储每个线程的事件循环
    _thread_local = threading.local()
    
    # 全局循环池（用于长时间运行的循环）
    _loop_pool: Dict[str, asyncio.AbstractEventLoop] = {}
    _loop_lock = threading.RLock()
    
    @classmethod
    def get_loop(cls) -> asyncio.AbstractEventLoop:
        """
        获取当前线程的事件循环，如果不存在则创建
        
        Returns:
            asyncio事件循环
        """
        try:
            # 尝试获取线程本地存储的循环
            if hasattr(cls._thread_local, 'loop'):
                loop = cls._thread_local.loop
                if not loop.is_closed():
                    return loop
        except (AttributeError, RuntimeError):
            pass
        
        # 创建新的事件循环
        return cls._create_and_store_loop()
    
    @classmethod
    def _create_and_store_loop(cls) -> asyncio.AbstractEventLoop:
        """
        创建并存储新的事件循环
        
        Returns:
            新创建的事件循环
        """
        try:
            # 尝试使用get_event_loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("Event loop is closed")
        except RuntimeError:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 存储到线程本地
        cls._thread_local.loop = loop
        return loop
    
    @classmethod
    def run_coroutine(cls, coro) -> Any:
        """
        运行异步协程并返回结果
        
        Args:
            coro: 异步协程对象
            
        Returns:
            协程执行结果
        """
        loop = cls.get_loop()
        return loop.run_until_complete(coro)
    
    @classmethod
    def create_task(cls, coro) -> asyncio.Task:
        """
        创建异步任务
        
        Args:
            coro: 异步协程对象
            
        Returns:
            异步任务对象
        """
        loop = cls.get_loop()
        return loop.create_task(coro)
    
    @classmethod
    def run_in_executor(cls, func: Callable, *args, **kwargs) -> asyncio.Future:
        """
        在执行器中运行同步函数
        
        Args:
            func: 要执行的同步函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            异步Future对象
        """
        loop = cls.get_loop()
        return loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    @classmethod
    def start_background_loop(cls, loop_name: str = None) -> str:
        """
        启动一个在后台运行的事件循环
        
        Args:
            loop_name: 循环名称，如果不提供则自动生成
            
        Returns:
            循环的唯一标识符
        """
        if loop_name is None:
            loop_name = f"bg_loop_{int(time.time())}_{os.getpid()}"
        
        with cls._loop_lock:
            # 检查名称是否已存在
            if loop_name in cls._loop_pool:
                raise ValueError(f"Loop with name '{loop_name}' already exists")
            
            # 创建新线程和循环
            loop = asyncio.new_event_loop()
            
            def _loop_runner():
                asyncio.set_event_loop(loop)
                try:
                    loop.run_forever()
                except KeyboardInterrupt:
                    pass
                finally:
                    loop.close()
            
            # 启动线程运行循环
            thread = threading.Thread(target=_loop_runner, daemon=True)
            thread.start()
            
            # 存储循环和线程信息
            cls._loop_pool[loop_name] = loop
            setattr(cls._loop_pool, f"_{loop_name}_thread", thread)
        
        return loop_name
    
    @classmethod
    def stop_background_loop(cls, loop_name: str) -> bool:
        """
        停止后台运行的事件循环
        
        Args:
            loop_name: 循环名称
            
        Returns:
            是否成功停止
        """
        with cls._loop_lock:
            if loop_name not in cls._loop_pool:
                return False
            
            loop = cls._loop_pool[loop_name]
            if not loop.is_closed():
                loop.call_soon_threadsafe(loop.stop)
                
            # 移除循环
            del cls._loop_pool[loop_name]
            if hasattr(cls._loop_pool, f"_{loop_name}_thread"):
                delattr(cls._loop_pool, f"_{loop_name}_thread")
            
        return True
    
    @classmethod
    def get_background_loop(cls, loop_name: str) -> Optional[asyncio.AbstractEventLoop]:
        """
        获取后台事件循环
        
        Args:
            loop_name: 循环名称
            
        Returns:
            事件循环对象，如果不存在则返回None
        """
        with cls._loop_lock:
            return cls._loop_pool.get(loop_name)
    
    @classmethod
    def run_in_background_loop(cls, loop_name: str, coro) -> asyncio.Future:
        """
        在指定的后台循环中运行协程
        
        Args:
            loop_name: 循环名称
            coro: 异步协程对象
            
        Returns:
            异步Future对象
            
        Raises:
            ValueError: 如果循环不存在
        """
        loop = cls.get_background_loop(loop_name)
        if loop is None:
            raise ValueError(f"Background loop '{loop_name}' not found")
        
        return asyncio.run_coroutine_threadsafe(coro, loop)
    
    @classmethod
    def close_loop(cls) -> None:
        """
        关闭当前线程的事件循环
        """
        try:
            if hasattr(cls._thread_local, 'loop'):
                loop = cls._thread_local.loop
                if not loop.is_closed():
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()
                delattr(cls._thread_local, 'loop')
        except Exception:
            pass
    
    @classmethod
    def close_all_background_loops(cls) -> None:
        """
        关闭所有后台事件循环
        """
        with cls._loop_lock:
            for loop_name in list(cls._loop_pool.keys()):
                cls.stop_background_loop(loop_name)


# 便捷函数
def get_event_loop() -> asyncio.AbstractEventLoop:
    """获取事件循环的便捷函数"""
    return LoopManager.get_loop()


def run_coroutine(coro) -> Any:
    """运行协程的便捷函数"""
    return LoopManager.run_coroutine(coro)


def create_task(coro) -> asyncio.Task:
    """创建任务的便捷函数"""
    return LoopManager.create_task(coro)