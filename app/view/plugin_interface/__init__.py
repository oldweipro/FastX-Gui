"""
插件管理界面模块
包含插件卡片、列表、详情页等组件
"""

from .plugin_interface import PluginInterface
from .plugin_card import PluginCard
from .plugin_list_card import PluginListCard
from .plugin_detail_dialog import PluginDetailDialog

__all__ = [
    'PluginInterface',
    'PluginCard',
    'PluginListCard',
    'PluginDetailDialog',
]
