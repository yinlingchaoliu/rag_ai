import asyncio

def get_event_loop():
    """
    获取事件循环，如果不存在则创建新的
    
    Returns:
        asyncio事件循环
    """
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        # 在Python 3.10+中，需要使用新的API
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def run_async(coro):
    """
    运行异步协程
    
    Args:
        coro: 异步协程
        
    Returns:
        协程执行结果
    """
    loop = get_event_loop()
    return loop.run_until_complete(coro)