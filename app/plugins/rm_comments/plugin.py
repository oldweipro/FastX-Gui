"""RmComments 插件 — Python 代码注释移除工具"""
from typing import Any, Dict, Optional
from PySide6.QtWidgets import QWidget
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory


class RmCommentsPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="RmComments",
            version="1.0.0",
            description="Python 代码注释批量移除工具，支持递归处理目录",
            author="FastXTeam",
            category=PluginCategory.UTILITIES,
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
        from app.tools.ui.rm_comments_ui import RmCommentsUI
        return RmCommentsUI(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> Dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: Dict[str, Any]):
        self._config.update(config)
