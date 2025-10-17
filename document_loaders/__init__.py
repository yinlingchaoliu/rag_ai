from typing import Dict, Type, Optional
from .base import BaseDocumentLoader, Document
import os
import importlib
import glob

# 文档加载器工厂类
class DocumentLoaderFactory:
    """
    文档加载器工厂类，用于管理和创建不同类型的文档加载器
    """
    
    def __init__(self):
        """
        初始化加载器工厂
        """
        self._loaders: Dict[str, Type[BaseDocumentLoader]] = {}
        self._extension_map: Dict[str, Type[BaseDocumentLoader]] = {}
    
    def register_loader(self, loader_class: Type[BaseDocumentLoader]) -> "DocumentLoaderFactory":
        """
        注册一个文档加载器
        
        Args:
            loader_class: 加载器类
            
        Returns:
            工厂实例，支持链式调用
        """
        if not issubclass(loader_class, BaseDocumentLoader):
            raise TypeError(f"加载器必须是BaseDocumentLoader的子类: {loader_class.__name__}")
        
        loader_name = loader_class.__name__
        self._loaders[loader_name] = loader_class
        
        # 注册支持的扩展名
        loader_info = loader_class.get_loader_info()
        for extension in loader_info.get("supported_extensions", []):
            # 确保扩展名以点开头
            if extension.startswith(('.', 'http', 'https', 'www', 'feishu')):
                key = extension.lower()
                self._extension_map[key] = loader_class
            else:
                key = f".{extension.lower()}"
                self._extension_map[key] = loader_class
        
        return self
    
    def get_loader(self, source: str) -> Optional[Type[BaseDocumentLoader]]:
        """
        根据源路径或URL获取适合的加载器
        
        Args:
            source: 文件路径或URL
            
        Returns:
            匹配的加载器类，如果没有找到则返回None
        """
        # 检查是否为URL
        if source.startswith(('http://', 'https://')):
            # 检查是否为飞书文档
            if 'feishu.cn' in source:
                for loader_class in self._loaders.values():
                    loader_info = loader_class.get_loader_info()
                    if 'feishu' in loader_info.get("supported_extensions", []):
                        return loader_class
            # 否则使用URL加载器
            for loader_class in self._loaders.values():
                loader_info = loader_class.get_loader_info()
                if 'http' in loader_info.get("supported_extensions", []):
                    return loader_class
        
        # 检查文件扩展名
        _, extension = os.path.splitext(source.lower())
        if extension in self._extension_map:
            return self._extension_map[extension]
        
        # 默认返回文本加载器（如果存在）
        for loader_class in self._loaders.values():
            if loader_class.__name__ == "TextFileLoader":
                return loader_class
        
        return None
    
    def create_loader(self, source: str, **kwargs) -> Optional[BaseDocumentLoader]:
        """
        创建适合指定源的加载器实例
        
        Args:
            source: 文件路径或URL
            **kwargs: 加载器初始化参数
            
        Returns:
            加载器实例，如果没有找到适合的加载器则返回None
        """
        loader_class = self.get_loader(source)
        if loader_class:
            return loader_class(**kwargs)
        return None
    
    def get_all_loaders(self) -> Dict[str, Type[BaseDocumentLoader]]:
        """
        获取所有注册的加载器
        
        Returns:
            加载器名称到加载器类的映射
        """
        return self._loaders.copy()
    
    def get_available_extensions(self) -> Dict[str, str]:
        """
        获取所有可用的文件扩展名及其对应的加载器
        
        Returns:
            扩展名为键，加载器名称为值的字典
        """
        return {
            ext: loader_class.__name__
            for ext, loader_class in self._extension_map.items()
        }

# 创建全局工厂实例
loader_factory = DocumentLoaderFactory()

# 自动注册所有加载器
def _auto_register_loaders():
    """
    自动注册所有文档加载器
    """
    # 获取当前目录下所有以_loader.py结尾的文件
    loader_files = glob.glob(os.path.join(os.path.dirname(__file__), "*_loader.py"))
    
    for loader_file in loader_files:
        # 提取模块名
        module_name = os.path.basename(loader_file).replace('.py', '')
        
        try:
            # 导入模块
            module = importlib.import_module(f".{module_name}", package=__name__)
            
            # 获取所有类并注册
            for name, obj in module.__dict__.items():
                if (
                    isinstance(obj, type) and 
                    issubclass(obj, BaseDocumentLoader) and 
                    obj != BaseDocumentLoader
                ):
                    loader_factory.register_loader(obj)
                    print(f"已注册文档加载器: {name}")
        
        except Exception as e:
            print(f"注册加载器 {module_name} 失败: {str(e)}")

# 自动注册加载器
_auto_register_loaders()

# 导出主要类和实例
__all__ = [
    "BaseDocumentLoader",
    "Document",
    "DocumentLoaderFactory",
    "loader_factory"
]