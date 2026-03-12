"""FastDem 插件 — 包装 tools/ui/FastDem_ui.py"""
from typing import Any

from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo
from app.common.icon import Icon


class FastDemPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_dem",
            version="1.0.0",
            description="DEM diagnostic file processing tool, supports DEM file parsing and generation",
            author="FastXTeam",
            category=PluginCategory.DIAGNOSTIC,
            icon_path=Icon.E2E,  # ✅ 直接使用 Icon 枚举（与 UI 一致）
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: QWidget | None = None) -> QWidget:
        from .ui.fast_dem_ui import FastDemToolUI
        w = FastDemToolUI(parent=parent)
        return w

    def cleanup(self):
        pass

    def get_config(self) -> dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: dict[str, Any]):
        self._config.update(config)
