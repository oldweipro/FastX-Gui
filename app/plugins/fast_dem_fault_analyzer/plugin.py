"""DEM Fault Analyzer Plugin - 基于 AUTOSAR CP DEM 的故障状态分析工具"""

from typing import Any, Optional
from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginCategory, PluginInfo
from app.common.icon import Icon, FIcon


class DEMFaultAnalyzerPlugin(PluginBase):
    """DEM 故障分析器插件"""
    
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="DEM 故障分析器",
            version="0.1.11",
            description="基于 AUTOSAR CP DEM 的 DTC 故障状态分析工具，支持故障状态位解析和分析",
            author="FastX Team",
            category=PluginCategory.DIAGNOSTIC,
            icon_path=Icon.DEM2,
            builtin=False,
        )
    
    def __init__(self):
        super().__init__()
        self._config: dict[str, Any] = {}
        self._business = None
    
    def initialize(self) -> bool:
        """初始化插件"""
        try:
            # 初始化业务逻辑
            from .core.dem_fault_analyzer import DEMFaultAnalyzer
            self._business = DEMFaultAnalyzer()
            self._is_initialized = True
            return True
        except Exception as e:
            print(f"DEM 故障分析器插件初始化失败：{e}")
            return False
    
    def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """获取主界面组件"""
        from .ui.dem_fault_card import DEMFaultCard
        widget = DEMFaultCard(parent=parent)
        return widget
    
    def cleanup(self):
        """清理插件资源"""
        self._business = None
    
    def get_config(self) -> dict[str, Any]:
        """读取插件配置"""
        return self._config.copy()
    
    def set_config(self, config: dict[str, Any]):
        """写入插件配置"""
        self._config.update(config)
