"""
插件系统模块
提供插件化架构支持，允许动态加载和管理各种工具插件
"""

from .plugin_base import PluginBase, PluginInfo, PluginCategory
from .plugin_manager import PluginManager
from .plugin_registry import PluginRegistry

__all__ = [
    'PluginBase',
    'PluginInfo', 
    'PluginCategory',
    'PluginManager',
    'PluginRegistry'
]