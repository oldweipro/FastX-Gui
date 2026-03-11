"""FastFaultManager 插件"""
from typing import Any

from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo


class FastFaultManagerPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_fault_manager",
            version="1.0.0",
            description="Fault code management tool, supports DTC creation, editing, template management and export",
            author="FastXTeam",
            category=PluginCategory.DIAGNOSTIC,
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: QWidget | None = None) -> QWidget:
        from .ui.fast_fault_manager_ui import FastFaultManagerToolUI
        return FastFaultManagerToolUI(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: dict[str, Any]):
        self._config.update(config)
