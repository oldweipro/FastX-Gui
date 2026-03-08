"""
插件加载器
负责插件的动态加载和热重载功能
"""

import importlib
import sys
from pathlib import Path
from typing import Optional, Type
from loguru import logger

from .plugin_base import PluginBase


class PluginLoader:
    """插件加载器 - 支持动态加载和热重载"""
    
    @staticmethod
    def load_plugin_module(plugin_path: Path) -> Optional[Type[PluginBase]]:
        """
        动态加载插件模块
        
        Args:
            plugin_path: 插件目录路径
            
        Returns:
            Type[PluginBase]: 插件类，如果加载失败返回None
        """
        try:
            plugin_name = plugin_path.name
            module_name = f"app.plugins.{plugin_name}"
            
            # 如果模块已加载，先卸载
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            # 导入模块
            spec = importlib.util.spec_from_file_location(
                module_name,
                plugin_path / '__init__.py'
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"无法创建模块规范: {plugin_path}")
                return None
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, PluginBase) and 
                    attr != PluginBase):
                    plugin_class = attr
                    break
                    
            if plugin_class is None:
                logger.error(f"在模块中未找到插件类: {plugin_path}")
                return None
                
            logger.info(f"成功加载插件模块: {plugin_name}")
            return plugin_class
            
        except Exception as e:
            logger.error(f"加载插件模块失败 {plugin_path}: {e}")
            return None
    
    @staticmethod
    def reload_plugin_module(plugin_name: str) -> bool:
        """
        重新加载插件模块（热重载）
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 重载是否成功
        """
        try:
            module_name = f"app.plugins.{plugin_name}"
            
            # 如果模块存在，重新加载
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                logger.info(f"成功重新加载插件: {plugin_name}")
                return True
            else:
                logger.warning(f"插件模块未加载: {plugin_name}")
                return False
                
        except Exception as e:
            logger.error(f"重新加载插件失败 '{plugin_name}': {e}")
            return False