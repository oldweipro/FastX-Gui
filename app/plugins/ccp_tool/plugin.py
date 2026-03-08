"""
CCP工具插件主入口
实现插件基类的具体功能
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory
from .ui.main_widget import CCPMainWidget


class CCPToolPlugin(PluginBase):
    """CCP工具插件实现"""
    
    def __init__(self):
        """初始化插件"""
        plugin_info = PluginInfo(
            name="CCP Tool",
            version="1.0.0",
            description="CCP协议诊断和分析工具",
            author="FastXTeam",
            category=PluginCategory.DIAGNOSTIC,
            icon_path="CCP"  # 使用 Icon.CCP
        )
        super().__init__(plugin_info)
        self._main_widget: Optional[CCPMainWidget] = None
        self._config: Dict[str, Any] = {}
    
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        """获取插件信息"""
        return PluginInfo(
            name="CCP Tool",
            version="1.0.0",
            description="CCP协议诊断和分析工具",
            author="FastXTeam",
            category=PluginCategory.DIAGNOSTIC,
            icon_path="CCP"  # 使用 Icon.CCP
        )
    
    def initialize(self) -> bool:
        """
        初始化插件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化配置
            self._config = {
                "input_file": "",
                "output_folder": "",
                "selected_option": 0
            }
            
            # 可以在这里进行其他初始化工作
            # 如数据库连接、资源配置等
            
            self._is_initialized = True
            return True
            
        except Exception as e:
            print(f"CCP插件初始化失败: {e}")
            return False
    
    def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        获取插件的主界面组件
        
        注意：每次调用都创建新的widget，避免widget被删除后的问题
        
        Args:
            parent: 父级窗口
            
        Returns:
            QWidget: 主界面组件
        """
        # 每次都创建新的widget，避免生命周期问题
        widget = CCPMainWidget(parent)
        # 应用当前配置
        widget.set_config(self._config)
        # 保存引用用于配置同步
        self._main_widget = widget
        
        return widget
    
    def cleanup(self):
        """清理插件资源"""
        if self._main_widget:
            self._main_widget.cleanup()
            self._main_widget = None
        
        # 清理其他资源
        self._config.clear()
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取插件配置
        
        Returns:
            Dict: 配置字典
        """
        if self._main_widget:
            # 从UI获取最新配置
            self._config.update(self._main_widget.get_config())
        return self._config.copy()
    
    def set_config(self, config: Dict[str, Any]):
        """
        设置插件配置
        
        Args:
            config: 配置字典
        """
        self._config.update(config)
        if self._main_widget:
            self._main_widget.set_config(config)