"""FastSomeIp 插件"""
from typing import Any

from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo


class FastSomeIpPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_some_ip",
            version="1.0.0",
            description="SOME/IP protocol processing tool, supports SOME/IP file parsing and processing",
            author="FastXTeam",
            category=PluginCategory.COMMUNICATION,
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: QWidget | None = None) -> QWidget:
        from .ui.fast_some_ip_ui import FastSomeIpToolUI
        return FastSomeIpToolUI(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: dict[str, Any]):
        self._config.update(config)
