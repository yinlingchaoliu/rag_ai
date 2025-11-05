#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loop模块使用示例
演示如何使用loop模块中的各个组件
"""

import asyncio
import time
import random
from typing import List

# 导入loop模块组件
from loop import (
    # Loop Manager
    LoopManager, run_coroutine, create_task,
    
    # Thread Pool
    ThreadPoolManager, thread_pool_decorator, submit_task,
    
    # Process Pool
    ProcessPoolManager, process_pool_decorator, submit_process_task,
    
    # Hybrid Executor
    HybridExecutor, HybridBatchProcessor, create_hybrid_executor
)


# 示例函数
def cpu_intensive_task(task_id: int, sleep_time: float) -> str:
    """CPU密集型任务示例"""
    print(f"CPU任务 {task_id} 开始执行，将睡眠 {sleep_time:.2f}秒")
    time.sleep(sleep_time)  # 模拟CPU密集型操作
    result = f"CPU任务 {task_id} 完成"
    print(result)
    return result


async def io_intensive_task(task_id: int, sleep_time: float) -> str:
    """IO密集型任务示例"""
    print(f"IO任务 {task_id} 开始执行，将睡眠 {sleep_time:.2f}秒")
    await asyncio.sleep(sleep_time)  # 模拟IO操作
    result = f"IO任务 {task_id} 完成"
    print(result)
    return result


# 装饰器示例
@thread_pool_decorator()
def decorated_thread_task(n: int) -> int:
    """使用线程池装饰器的任务"""
    time.sleep(0.5)
    return n * 2


@process_pool_decorator()
def decorated_process_task(n: int) -> int:
    """使用进程池装饰器的任务"""
    time.sleep(0.5)
    return n * 3


async def demonstrate_loop_manager():
    """演示LoopManager的使用"""
    print("\n" + "="*60)
    print("演示LoopManager")
    print("="*60)
    
    # 运行异步任务
    result = run_coroutine(io_intensive_task(1, 0.5))
    print(f"同步获取异步任务结果: {result}")
    
    # 创建后台循环
    loop_name = LoopManager.start_background_loop("my_background_loop")
    print(f"创建后台循环: {loop_name}")
    
    # 在后台循环中运行任务
    future = LoopManager.run_in_background_loop(
        loop_name,
        io_intensive_task(2, 0.3)
    )
    
    # 等待结果
    result = future.result()
    print(f"后台循环任务结果: {result}")
    
    # 停止后台循环
    LoopManager.stop_background_loop(loop_name)
    print("后台循环已停止")


async def demonstrate_thread_pool():
    """演示ThreadPoolManager的使用"""
    print("\n" + "="*60)
    print("演示ThreadPoolManager")
    print("="*60)
    
    # 获取线程池
    pool = ThreadPoolManager.get_pool(max_workers=4)
    print(f"线程池最大工作线程数: {getattr(pool, '_max_workers', 'unknown')}")
    
    # 提交单个任务
    future = submit_task(cpu_intensive_task, 1, 0.5)
    result = future.result()
    print(f"单个任务结果: {result}")
    
    # 批量提交任务
    tasks = [(cpu_intensive_task, (i, 0.3 + random.random() * 0.2), {}) for i in range(2, 6)]
    futures = ThreadPoolManager.submit_batch(tasks)
    results = ThreadPoolManager.wait_for_all(futures)
    print(f"批量任务结果: {results}")
    
    # 使用map
    numbers = list(range(10))
    results = ThreadPoolManager.map(lambda x: x * x, numbers)
    print(f"Map结果: {results}")
    
    # 使用装饰器
    result = decorated_thread_task(10)
    print(f"装饰器任务结果: {result}")
    
    # 异步装饰器
    future = decorated_thread_task.run_async(20)
    result = future.result()
    print(f"异步装饰器任务结果: {result}")


async def demonstrate_process_pool():
    """演示ProcessPoolManager的使用"""
    print("\n" + "="*60)
    print("演示ProcessPoolManager")
    print("="*60)
    
    # 设置启动方法
    try:
        ProcessPoolManager.set_start_method('fork')
        print("进程启动方法设置为: fork")
    except Exception as e:
        print(f"设置进程启动方法失败: {e}")
    
    # 获取进程池
    pool = ProcessPoolManager.get_pool(max_workers=2)
    print(f"进程池最大工作进程数: {getattr(pool, '_max_workers', 'unknown')}")
    
    # 提交CPU密集型任务
    future = submit_process_task(cpu_intensive_task, 100, 0.8)
    result = future.result()
    print(f"进程池任务结果: {result}")
    
    # 使用装饰器
    result = decorated_process_task(10)
    print(f"进程装饰器任务结果: {result}")
    
    # 计算最佳chunksize
    chunksize = ProcessPoolManager.calculate_optimal_chunksize(1000)
    print(f"最佳chunksize值: {chunksize}")


async def demonstrate_hybrid_executor():
    """演示HybridExecutor的使用"""
    print("\n" + "="*60)
    print("演示HybridExecutor")
    print("="*60)
    
    # 创建混合执行器
    executor = HybridExecutor(max_workers=4)
    
    # 在线程中运行同步任务
    result = await executor.run_in_thread(cpu_intensive_task, 200, 0.4)
    print(f"线程任务结果: {result}")
    
    # 运行异步任务
    result = await executor.run_async(io_intensive_task(201, 0.5))
    print(f"异步任务结果: {result}")
    
    # 运行混合任务
    result = await executor.run_hybrid_task(
        io_bound_func=lambda: "IO任务完成",
        cpu_bound_func=lambda: "CPU任务完成"
    )
    print(f"混合任务结果: {result}")
    
    # 并行映射
    numbers = list(range(5))
    results = await executor.map_in_threads(
        lambda x: (x, x * x), 
        numbers
    )
    print(f"并行映射结果: {results}")
    
    # 管道处理
    items = [1, 2, 3, 4, 5]
    stages = [
        lambda x: x + 10,  # 第一阶段
        lambda x: x * 2,   # 第二阶段
        lambda x: x - 5    # 第三阶段
    ]
    results = await executor.process_batch_with_pipeline(items, stages)
    print(f"管道处理结果: {results}")
    
    # 关闭执行器
    executor.shutdown()


async def demonstrate_hybrid_batch_processor():
    """演示HybridBatchProcessor的使用"""
    print("\n" + "="*60)
    print("演示HybridBatchProcessor")
    print("="*60)
    
    # 创建批处理器
    processor = HybridBatchProcessor(batch_size=5, max_concurrency=3)
    
    # 生成测试数据
    test_items = list(range(20))
    
    # 进度回调
    def progress_callback(processed, total, elapsed):
        rate = processed / elapsed if elapsed > 0 else 0
        print(f"  进度更新: {processed}/{total} ({processed/total*100:.1f}%) - 速度: {rate:.1f}项/秒")
    
    # 批量处理
    results = await processor.process_batch(
        test_items,
        lambda x: (x, x * x),
        progress_callback=progress_callback
    )
    
    print(f"\n批处理完成，处理了 {len(results)} 项")
    print(f"前5个结果: {results[:5]}")
    
    # 关闭批处理器
    processor.shutdown()


async def main():
    """主函数，运行所有演示"""
    print("开始演示loop模块的各个组件...")
    
    # 演示各个组件
    await demonstrate_loop_manager()
    await demonstrate_thread_pool()
    await demonstrate_process_pool()
    await demonstrate_hybrid_executor()
    await demonstrate_hybrid_batch_processor()
    
    # 清理资源
    ThreadPoolManager.shutdown()
    ProcessPoolManager.shutdown()
    LoopManager.close_all_background_loops()
    
    print("\n" + "="*60)
    print("所有演示完成！")
    print("="*60)


if __name__ == "__main__":
    # 运行主函数
    run_coroutine(main())