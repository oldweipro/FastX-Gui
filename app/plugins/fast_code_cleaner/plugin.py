"""Fast Code Cleaner Plugin"""
from typing import Any

from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo
from app.common.icon import Icon


class FastCodeCleanerPlugin(PluginBase):
    """Fast Code Cleaner Plugin - Python code comment removal tool"""

    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_code_cleaner",
            version="1.0.0",
            description="Python code comment batch removal tool, supports recursive directory processing",
            author="FastXTeam",
            category=PluginCategory.UTILITIES,
            icon_path=Icon.CODE,  # ✅ 使用已存在的图标
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: QWidget | None = None) -> QWidget:
        from .ui.code_cleaner_card import FastCodeCleanerCard
        return FastCodeCleanerCard(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: dict[str, Any]):
        self._config.update(config)
