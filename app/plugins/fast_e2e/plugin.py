"""FastE2E 插件"""
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QWidget
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory


class FastE2EPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_e2e",
            version="1.0.0",
            description="E2E 通信端到端校验工具，支持 Profile 配置与校验计算",
            author="FastXTeam",
            category=PluginCategory.COMMUNICATION,
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: Dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        from .ui.fast_e2e_ui import FastE2EToolUI
        return FastE2EToolUI(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: Dict[str, Any]):
        self._config.update(config)
