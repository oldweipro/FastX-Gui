"""Fast QC Composition Plugin"""
from typing import Any

from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo
from app.common.icon import UIcon


class FastQcCompositionPlugin(PluginBase):
    """Fast QC Composition Plugin - QC composition signal processing tool"""

    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_qc_composition",
            version="1.0.0",
            description="QC composition signal processing tool, supports signal composition and verification",
            author="FastXTeam",
            category=PluginCategory.COMMUNICATION,
            icon_path=UIcon.get("ic_fluent_data_usage_20_regular"),  # ✅ 使用 UIcon.get() 方法，可追溯
            builtin=True,
        )

    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent: QWidget | None = None) -> QWidget:
        from .ui.qc_composition_card import FastQcCompositionCard
        return FastQcCompositionCard(parent=parent)

    def cleanup(self):
        pass

    def get_config(self) -> dict[str, Any]:
        return self._config.copy()

    def set_config(self, config: dict[str, Any]):
        self._config.update(config)
