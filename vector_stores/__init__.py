import os
import importlib
from .base import BaseVectorStore, VectorStoreFactory

# 创建全局向量存储工厂实例
vector_store_factory = VectorStoreFactory()

# 自动注册所有向量存储实现
def _register_vector_stores():
    """
    自动注册所有向量存储实现
    查找当前目录下所有以_store.py结尾的文件，并导入其中的BaseVectorStore子类
    """
    current_dir = os.path.dirname(__file__)
    
    # 遍历当前目录下的所有.py文件
    for filename in os.listdir(current_dir):
        if filename.endswith('_store.py') and filename != '__init__.py':
            module_name = filename[:-3]  # 移除.py后缀
            
            try:
                # 导入模块
                module = importlib.import_module(f'.{module_name}', package=__name__)
                
                # 查找BaseVectorStore的子类
                for name, obj in module.__dict__.items():
                    # 检查是否是BaseVectorStore的子类且不是BaseVectorStore本身
                    if (isinstance(obj, type) and 
                        issubclass(obj, BaseVectorStore) and 
                        obj != BaseVectorStore):
                        
                        # 获取存储类型名称（去除VectorStore后缀，如果有）
                        store_type = name.replace('VectorStore', '').lower()
                        
                        # 注册向量存储
                        vector_store_factory.register_vector_store(store_type, obj)
                        
                        print(f"已注册向量存储: {store_type} -> {name}")
            
            except Exception as e:
                print(f"导入向量存储模块 {module_name} 失败: {str(e)}")

# 自动注册向量存储实现
_register_vector_stores()

# 导出公共接口
__all__ = ['BaseVectorStore', 'VectorStoreFactory', 'vector_store_factory']