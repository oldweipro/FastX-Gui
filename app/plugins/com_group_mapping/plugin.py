"""ComGroupMapping 插件"""
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QWidget
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory


class ComGroupMappingPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="ComGroupMapping",
            version="1.0.0",
            description="Com 组映射工具，用于处理 Com 文件的组映射关系",
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
        from app.tools.ui.ComGroupMapping_ui import ComGroupMappingToolUI
        return ComGroupMappingToolUI(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: Dict[str, Any]):
        self._config.update(config)
