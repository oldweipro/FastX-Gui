"""
插件基类定义
定义插件的标准接口和基本结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import QWidget


class PluginCategory(Enum):
    """插件分类枚举"""
    DIAGNOSTIC = "diagnostic"      # 诊断工具
    COMMUNICATION = "communication"  # 通信工具
    SERIAL = "serial"              # 串口工具
    UTILITIES = "utilities"        # 实用工具
    CUSTOM = "custom"              # 自定义工具


@dataclass
class PluginInfo:
    """插件信息数据类"""
    name: str                    # 插件名称
    version: str                 # 版本号
    description: str             # 描述
    author: str                  # 作者
    category: PluginCategory     # 分类
    icon_path: Optional[str] = None  # 图标路径
    dependencies: List[str] = None   # 依赖项
    enabled: bool = True         # 是否启用
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PluginBase(ABC):
    """插件基类 - 定义插件的标准接口"""
    
    def __init__(self, plugin_info: PluginInfo):
        """
        初始化插件
        
        Args:
            plugin_info: 插件信息对象
        """
        self.info = plugin_info
        self._is_initialized = False
        self._main_widget = None  # 缓存主界面widget
        
    @classmethod
    @abstractmethod
    def get_plugin_info(cls) -> PluginInfo:
        """
        获取插件信息（类方法）
        
        Returns:
            PluginInfo: 插件信息对象
        """
        pass
        
    @property
    def name(self) -> str:
        """获取插件名称"""
        return self.info.name
        
    @property
    def category(self) -> PluginCategory:
        """获取插件分类"""
        return self.info.category
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化插件
        
        Returns:
            bool: 初始化是否成功
        """
        pass
        
    @abstractmethod
    def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        获取插件的主界面组件
        
        注意：每次调用都会创建新的widget，以避免widget被删除后的问题
        
        Args:
            parent: 父级窗口
            
        Returns:
            QWidget: 主界面组件
        """
        pass
        
    @abstractmethod
    def cleanup(self):
        """清理插件资源"""
        # 清理缓存的widget
        if self._main_widget:
            try:
                self._main_widget.deleteLater()
            except:
                pass
            self._main_widget = None
        
    def is_initialized(self) -> bool:
        """检查插件是否已初始化"""
        return self._is_initialized
        
    def get_config(self) -> Dict[str, Any]:
        """
        获取插件配置
        
        Returns:
            Dict: 配置字典
        """
        return {}
        
    def set_config(self, config: Dict[str, Any]):
        """
        设置插件配置
        
        Args:
            config: 配置字典
        """
        pass
        
    def is_widget_valid(self) -> bool:
        """检查缓存的widget是否有效"""
        if self._main_widget is None:
            return False
        try:
            # 尝试访问widget的属性，如果已删除会抛出异常
            _ = self._main_widget.objectName()
            return True
        except RuntimeError:
            # widget已被删除
            self._main_widget = None
            return False
    
    def validate_dependencies(self) -> List[str]:
        """
        验证依赖项
        
        Returns:
            List[str]: 缺失的依赖项列表
        """
        missing_deps = []
        # 这里可以实现具体的依赖检查逻辑
        return missing_deps