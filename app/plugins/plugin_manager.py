"""
插件管理器
负责插件的生命周期管理、配置管理和状态跟踪
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

from .plugin_base import PluginBase, PluginInfo, PluginCategory
from .plugin_registry import PluginRegistry
from app.common.config import cfg


class PluginManager:
    """插件管理器 - 负责插件的完整生命周期管理"""
    
    def __init__(self, plugins_directory: Optional[Path] = None):
        """
        初始化插件管理器
        
        Args:
            plugins_directory: 插件目录路径
        """
        self.registry = PluginRegistry()
        self.plugins_directory = plugins_directory or Path(__file__).parent
        self._loaded_plugins: Dict[str, PluginBase] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        # 加载已保存的插件配置
        self._load_plugin_configs()
    
    def load_plugins(self) -> int:
        """
        加载所有可用插件
        
        Returns:
            int: 成功加载的插件数量
        """
        logger.info("开始加载插件...")
        
        # 发现并注册插件
        registered_count = self.registry.discover_plugins(self.plugins_directory)
        if registered_count == 0:
            logger.warning("未发现任何插件")
            return 0
            
        loaded_count = 0
        
        # 初始化每个插件
        for plugin_name in self.registry.get_all_plugins():
            if self.load_plugin(plugin_name):
                loaded_count += 1
                
        logger.info(f"插件加载完成: {loaded_count}/{registered_count} 个插件")
        return loaded_count
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        加载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 加载是否成功
        """
        if plugin_name in self._loaded_plugins:
            logger.debug(f"插件 '{plugin_name}' 已加载")
            return True
            
        # 获取插件实例
        plugin_instance = self.registry.get_plugin_instance(plugin_name)
        if not plugin_instance:
            logger.error(f"无法获取插件实例: {plugin_name}")
            return False
            
        # 检查依赖
        missing_deps = plugin_instance.validate_dependencies()
        if missing_deps:
            logger.error(f"插件 '{plugin_name}' 缺少依赖: {missing_deps}")
            return False
            
        # 应用配置
        plugin_config = self._plugin_configs.get(plugin_name, {})
        if plugin_config:
            plugin_instance.set_config(plugin_config)
            
        # 添加到已加载列表
        self._loaded_plugins[plugin_name] = plugin_instance
        logger.info(f"成功加载插件: {plugin_name}")
        return True
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载指定插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        if plugin_name not in self._loaded_plugins:
            logger.warning(f"插件 '{plugin_name}' 未加载")
            return False
            
        try:
            # 清理插件资源
            plugin_instance = self._loaded_plugins[plugin_name]
            plugin_instance.cleanup()
            
            # 保存配置
            self._save_plugin_config(plugin_name, plugin_instance.get_config())
            
            # 从加载列表中移除
            del self._loaded_plugins[plugin_name]
            
            logger.info(f"成功卸载插件: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件 '{plugin_name}' 时出错: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """
        获取已加载的插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            PluginBase: 插件实例，如果未加载返回None
        """
        return self._loaded_plugins.get(plugin_name)
    
    def get_all_loaded_plugins(self) -> List[str]:
        """
        获取所有已加载的插件名称
        
        Returns:
            List[str]: 已加载的插件名称列表
        """
        return list(self._loaded_plugins.keys())
    
    def get_plugins_by_category(self, category: PluginCategory) -> List[str]:
        """
        根据分类获取已加载的插件
        
        Args:
            category: 插件分类
            
        Returns:
            List[str]: 该分类下已加载的插件名称列表
        """
        all_plugins_in_category = self.registry.get_plugins_by_category(category)
        return [name for name in all_plugins_in_category if name in self._loaded_plugins]
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """
        检查插件是否已加载
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否已加载
        """
        return plugin_name in self._loaded_plugins
    
    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            PluginInfo: 插件信息
        """
        return self.registry.get_plugin_info(plugin_name)
    
    def save_all_configs(self):
        """保存所有插件的配置"""
        for plugin_name, plugin_instance in self._loaded_plugins.items():
            config = plugin_instance.get_config()
            self._save_plugin_config(plugin_name, config)
        logger.info("所有插件配置已保存")
    
    def _load_plugin_configs(self):
        """从配置文件加载插件配置"""
        try:
            # 这里可以从配置文件或数据库加载插件配置
            # 暂时使用内存存储
            pass
        except Exception as e:
            logger.error(f"加载插件配置时出错: {e}")
    
    def _save_plugin_config(self, plugin_name: str, config: Dict[str, Any]):
        """
        保存单个插件的配置
        
        Args:
            plugin_name: 插件名称
            config: 配置字典
        """
        try:
            # 这里可以保存到配置文件或数据库
            self._plugin_configs[plugin_name] = config
            # 示例：保存到应用配置
            config_key = f"plugin_{plugin_name}_config"
            cfg.set(config_key, config)
        except Exception as e:
            logger.error(f"保存插件 '{plugin_name}' 配置时出错: {e}")
    
    def shutdown(self):
        """关闭插件管理器，清理所有资源"""
        logger.info("正在关闭插件管理器...")
        
        # 保存所有配置
        self.save_all_configs()
        
        # 卸载所有插件
        for plugin_name in list(self._loaded_plugins.keys()):
            self.unload_plugin(plugin_name)
            
        logger.info("插件管理器已关闭")