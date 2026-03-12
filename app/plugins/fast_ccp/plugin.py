"""Fast CCP Plugin"""
from typing import Any

from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo
from app.common.icon import Icon


class FastCcpPlugin(PluginBase):
    """Fast CCP Plugin - CCP calibration protocol tool"""

    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_ccp",
            version="1.0.0",
            description="CCP calibration protocol tool, supports A2L file parsing and calibration data management",
            author="FastXTeam",
            category=PluginCategory.DIAGNOSTIC,
            icon_path=Icon.CCP,  # ✅ 直接使用 Icon 枚举，可追溯、有提示
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: QWidget | None = None) -> QWidget:
        from .ui.ccp_card import FastCcpCard
        return FastCcpCard(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: dict[str, Any]):
        self._config.update(config)
