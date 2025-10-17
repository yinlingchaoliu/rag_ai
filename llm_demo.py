#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型使用示例
"""

from models.model_manager import ModelManager

def example_basic_usage():
    """
    基本使用示例
    """
    print("=== 基本使用示例 ===")
    
    # 创建模型管理器
    manager = ModelManager()
    
    # 注册默认模型
    manager.register_default_models()
    
    # 获取可用模型列表
    available_models = manager.get_available_models()
    print(f"可用模型: {available_models}")

def example_chat_usage():
    """
    对话功能使用示例
    """
    print("\n=== 对话功能使用示例 ===")
    
    # 创建模型管理器
    manager = ModelManager()
    
    # 注册默认模型
    manager.register_default_models()
    
    # 准备对话消息
    messages = [
        {"role": "system", "content": "你是一个有帮助的AI助手，回答问题要简洁明了。"},
        {"role": "user", "content": "什么是机器学习？"},
        {"role": "assistant", "content": "机器学习是人工智能的一个分支，让计算机通过数据学习而不是显式编程。"},
        {"role": "user", "content": "那深度学习又是什么？"}
    ]
    
    # 进行对话
    try:
        response = manager.chat(messages, temperature=0.3, max_tokens=300)
        print(f"\n对话响应:")
        print(response)
    except Exception as e:
        print(f"对话失败: {str(e)}")

def example_model_switching():
    """
    模型切换示例
    """
    print("\n=== 模型切换示例 ===")
    
    # 创建模型管理器
    manager = ModelManager()
    
    # 手动注册各个模型
    try:
        manager.register_model("ollama", models.OllamaModel())
        print("Ollama模型注册成功")
    except Exception as e:
        print(f"Ollama模型注册失败: {str(e)}")
    
    # 尝试在不同模型之间切换（如果可用）
    available_models = manager.get_available_models()
    if available_models:
        prompt = "请解释什么是自然语言处理？"
        
        for model_name in available_models:
            try:
                print(f"\n切换到模型: {model_name}")
                manager.set_current_model(model_name)
                response = manager.generate(prompt, temperature=0.5)
                print(f"{model_name} 响应: {response[:100]}...")
            except Exception as e:
                print(f"使用 {model_name} 失败: {str(e)}")

def example_custom_model_params():
    """
    自定义模型参数示例
    """
    print("\n=== 自定义模型参数示例 ===")
    
    # 创建模型管理器
    manager = ModelManager()
    
    # 注册默认模型
    manager.register_default_models()
    
    # 使用不同的参数生成文本
    try:
        # 使用高创造性参数
        prompt = "写一首短诗，关于人工智能"
        print("\n高创造性参数(temperature=0.9):")
        response1 = manager.generate(prompt, temperature=0.9, max_tokens=200)
        print(response1)
        
        # 使用低创造性参数
        print("\n低创造性参数(temperature=0.1):")
        response2 = manager.generate(prompt, temperature=0.1, max_tokens=200)
        print(response2)
    except Exception as e:
        print(f"生成失败: {str(e)}")

if __name__ == "__main__":
    # 导入models模块
    import models
    # 创建模型管理器
    manager = ModelManager()
    
    # 注册默认模型
    manager.register_default_models()
    
    # 获取可用模型列表
    available_models = manager.get_available_models()
    print(f"可用模型: {available_models}")

            # 使用高创造性参数
    prompt = "写一首短诗，关于人工智能"
    print("\n高创造性参数(temperature=0.9):")
    response1 = manager.generate(prompt, temperature=0.9, max_tokens=200)
    print(response1)

    # 运行各个示例
    # example_basic_usage()
    # example_model_switching()

    # example_chat_usage()
    # example_model_switching()
    # example_custom_model_params()