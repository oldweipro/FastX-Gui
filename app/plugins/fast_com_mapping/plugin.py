"""Fast COM Mapping Plugin"""
from typing import Any

from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo
from app.common.icon import Icon


class FastComMappingPlugin(PluginBase):
    """Fast COM Mapping Plugin - COM group mapping tool"""

    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_com_mapping",
            version="1.0.0",
            description="Com group mapping tool, used to handle group mapping relationships in Com files",
            author="FastXTeam",
            category=PluginCategory.COMMUNICATION,
            icon_path=Icon.COM,  # ✅ 直接使用 Icon 枚举
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: QWidget | None = None) -> QWidget:
        from .ui.com_mapping_card import FastComMappingCard
        return FastComMappingCard(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: dict[str, Any]):
        self._config.update(config)
