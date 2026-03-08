"""
插件注册中心
负责插件的注册、发现和管理
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type
from loguru import logger

from .plugin_base import PluginBase, PluginInfo, PluginCategory


class PluginRegistry:
    """插件注册中心 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._plugins: Dict[str, Type[PluginBase]] = {}  # 插件类注册表
            self._plugin_instances: Dict[str, PluginBase] = {}  # 插件实例缓存
            self._plugin_infos: Dict[str, PluginInfo] = {}  # 插件信息缓存
            self._categories: Dict[PluginCategory, List[str]] = {}  # 分类索引
            self._initialized = True
    
    def register_plugin(self, plugin_class: Type[PluginBase]) -> bool:
        """
        注册插件类
        
        Args:
            plugin_class: 插件类
            
        Returns:
            bool: 注册是否成功
        """
        try:
            # 获取插件信息
            plugin_info = plugin_class.get_plugin_info()
            
            # 检查插件名称是否已存在
            if plugin_info.name in self._plugins:
                logger.warning(f"插件 '{plugin_info.name}' 已存在，跳过注册")
                return False
                
            # 注册插件
            self._plugins[plugin_info.name] = plugin_class
            self._plugin_infos[plugin_info.name] = plugin_info
            
            # 更新分类索引
            category = plugin_info.category
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(plugin_info.name)
            
            logger.info(f"成功注册插件: {plugin_info.name} (v{plugin_info.version})")
            return True
            
        except Exception as e:
            logger.error(f"注册插件失败: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 注销是否成功
        """
        if plugin_name not in self._plugins:
            return False
            
        # 从各注册表中移除
        del self._plugins[plugin_name]
        
        if plugin_name in self._plugin_instances:
            del self._plugin_instances[plugin_name]
            
        if plugin_name in self._plugin_infos:
            plugin_info = self._plugin_infos[plugin_name]
            del self._plugin_infos[plugin_name]
            
            # 更新分类索引
            category_plugins = self._categories.get(plugin_info.category, [])
            if plugin_name in category_plugins:
                category_plugins.remove(plugin_name)
                
        logger.info(f"成功注销插件: {plugin_name}")
        return True
    
    def get_plugin_class(self, plugin_name: str) -> Optional[Type[PluginBase]]:
        """
        获取插件类
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Type[PluginBase]: 插件类，如果未找到返回None
        """
        return self._plugins.get(plugin_name)
    
    def get_plugin_instance(self, plugin_name: str) -> Optional[PluginBase]:
        """
        获取插件实例（懒加载）
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            PluginBase: 插件实例，如果未找到或初始化失败返回None
        """
        # 如果已有实例，直接返回
        if plugin_name in self._plugin_instances:
            return self._plugin_instances[plugin_name]
            
        # 获取插件类并创建实例
        plugin_class = self.get_plugin_class(plugin_name)
        if not plugin_class:
            return None
            
        try:
            plugin_instance = plugin_class()
            if plugin_instance.initialize():
                self._plugin_instances[plugin_name] = plugin_instance
                plugin_instance._is_initialized = True
                return plugin_instance
            else:
                logger.error(f"插件 '{plugin_name}' 初始化失败")
                return None
        except Exception as e:
            logger.error(f"创建插件实例失败 '{plugin_name}': {e}")
            return None
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            PluginInfo: 插件信息，如果未找到返回None
        """
        return self._plugin_infos.get(plugin_name)
    
    def get_all_plugins(self) -> List[str]:
        """
        获取所有已注册的插件名称
        
        Returns:
            List[str]: 插件名称列表
        """
        return list(self._plugins.keys())
    
    def get_plugins_by_category(self, category: PluginCategory) -> List[str]:
        """
        根据分类获取插件
        
        Args:
            category: 插件分类
            
        Returns:
            List[str]: 该分类下的插件名称列表
        """
        return self._categories.get(category, []).copy()
    
    def get_all_categories(self) -> List[PluginCategory]:
        """
        获取所有存在的插件分类
        
        Returns:
            List[PluginCategory]: 分类列表
        """
        return list(self._categories.keys())
    
    def is_plugin_registered(self, plugin_name: str) -> bool:
        """
        检查插件是否已注册
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否已注册
        """
        return plugin_name in self._plugins
    
    def discover_plugins(self, plugins_path: Path) -> int:
        """
        自动发现并注册插件
        
        Args:
            plugins_path: 插件目录路径
            
        Returns:
            int: 成功注册的插件数量
        """
        registered_count = 0
        
        if not plugins_path.exists():
            logger.warning(f"插件目录不存在: {plugins_path}")
            return registered_count
            
        # 遍历插件目录
        for item in plugins_path.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                try:
                    # 导入插件模块
                    module_name = f"app.plugins.{item.name}"
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        item / '__init__.py'
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # 查找插件类
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and 
                                issubclass(attr, PluginBase) and 
                                attr != PluginBase):
                                
                                if self.register_plugin(attr):
                                    registered_count += 1
                                    
                except Exception as e:
                    logger.error(f"发现插件 '{item.name}' 时出错: {e}")
                    
        logger.info(f"成功发现并注册 {registered_count} 个插件")
        return registered_count
    
    def clear(self):
        """清空所有注册信息"""
        # 清理所有插件实例
        for plugin_instance in self._plugin_instances.values():
            try:
                plugin_instance.cleanup()
            except Exception as e:
                logger.error(f"清理插件实例时出错: {e}")
        
        self._plugins.clear()
        self._plugin_instances.clear()
        self._plugin_infos.clear()
        self._categories.clear()
        
        logger.info("插件注册中心已清空")