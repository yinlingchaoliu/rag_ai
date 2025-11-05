#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
loop模块功能测试脚本
"""

# 测试线程池功能
from loop import ThreadPoolManager
import time

def test_func(x):
    time.sleep(0.1)
    return x * x

if __name__ == "__main__":
    print("开始测试线程池功能...")
    results = ThreadPoolManager.map(test_func, range(10))
    print('线程池测试成功！结果:', results)
    
    # 清理
    ThreadPoolManager.shutdown()
    print("测试完成！")