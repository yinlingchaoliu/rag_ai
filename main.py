#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG项目主入口
"""

import os
import sys
import logging
from webui import webui

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        logger.info("启动RAG聊天应用...")
        
        # 确保必要的目录存在
        os.makedirs("upload", exist_ok=True)
        os.makedirs("db/sqlite", exist_ok=True)
        
        # 启动WebUI
        logger.info("正在启动WebUI界面...")
        webui.launch()
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        raise
    finally:
        logger.info("程序已关闭")


if __name__ == "__main__":
    main()