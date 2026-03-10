"""FastFaultManager 插件"""
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QWidget
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory


class FastFaultManagerPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="FastFaultManager",
            version="1.0.0",
            description="故障码管理工具，支持 DTC 创建、编辑、模板管理与导出",
            author="FastXTeam",
            category=PluginCategory.DIAGNOSTIC,
            icon_path=None,
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: Dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        from .ui.fast_fault_manager_ui import FastFaultManagerToolUI
        return FastFaultManagerToolUI(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: Dict[str, Any]):
        self._config.update(config)
