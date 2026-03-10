"""FastSomeIp 插件"""
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QWidget
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory


class FastSomeIpPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="FastSomeIp",
            version="1.0.0",
            description="SOME/IP 协议处理工具，支持 SOME/IP 文件解析与处理",
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
        from .ui.fast_some_ip_ui import FastSomeIpToolUI
        return FastSomeIpToolUI(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: Dict[str, Any]):
        self._config.update(config)
