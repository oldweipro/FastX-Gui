"""
插件基类定义 - 插件开发规范
==============================

所有插件必须继承 PluginBase，并实现以下抽象方法：
  - get_plugin_info()  : 返回插件元数据（类方法）
  - initialize()       : 插件初始化逻辑
  - get_main_widget()  : 返回主界面 QWidget
  - cleanup()          : 释放资源

可选覆盖的接口（提供默认空实现）：
  - get_settings_widget() : 设置界面（None 表示无设置）
  - get_config()           : 读取插件配置
  - set_config()           : 写入插件配置
  - on_input()             : 接收外部输入数据
  - get_output()           : 向外部提供输出数据
  - get_log_widget()       : 插件专属日志面板（None 表示不提供）
  - get_doc_url()          : 文档链接（None 表示无文档）
  - get_doc_widget()       : 内嵌文档面板（None 表示不提供）
  - validate_dependencies(): 依赖检查
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from PySide6.QtWidgets import QWidget


# ---------------------------------------------------------------------------
# 枚举 & 元数据
# ---------------------------------------------------------------------------

class PluginCategory(Enum):
    """插件分类枚举"""
    DIAGNOSTIC    = "diagnostic"      # 诊断工具
    COMMUNICATION = "communication"   # 通信工具
    SERIAL        = "serial"          # 串口工具
    UTILITIES     = "utilities"       # 实用工具
    CUSTOM        = "custom"          # 自定义工具


@dataclass
class PluginInfo:
    """
    插件元数据
    ──────────────────────────────────────────────
    name        : 插件唯一名称（不可重复）
    version     : 语义化版本号，如 "1.2.3"
    description : 功能简述（显示在卡片上）
    author      : 作者 / 团队
    category    : PluginCategory 枚举值
    icon_path   : Icon 枚举名（字符串）或 FluentIconBase 实例
    dependencies: 依赖的 Python 包名列表
    enabled     : 运行时启用状态（可由用户切换）
    builtin     : True = 内置插件，不允许卸载、不显示卸载按钮
    """
    name:         str
    version:      str
    description:  str
    author:       str
    category:     PluginCategory
    icon_path:    Optional[str]  = None
    dependencies: List[str]      = field(default_factory=list)
    enabled:      bool           = True
    builtin:      bool           = False   # ← 内置标志


# ---------------------------------------------------------------------------
# 插件基类
# ---------------------------------------------------------------------------

class PluginBase(ABC):
    """
    插件基类 — 定义完整的插件开发规范
    ======================================================

    开发新插件步骤
    ──────────────
    1. 在 app/plugins/<plugin_folder>/ 下创建目录
    2. 编写 manifest.json（参考 ccp_tool/manifest.json）
    3. 在 __init__.py 中 import 插件主类
    4. 继承 PluginBase，实现所有 @abstractmethod
    5. 按需覆盖可选接口

    接口分类说明
    ──────────────
    [必须实现]
      get_plugin_info()   → PluginInfo
      initialize()        → bool
      get_main_widget()   → QWidget
      cleanup()

    [推荐实现]
      get_settings_widget() → QWidget | None
      get_config()          → dict
      set_config(config)

    [可选实现]
      on_input(data)        → 接收外部推送数据
      get_output()          → 向外部暴露输出
      get_log_widget()      → QWidget | None
      get_doc_url()         → str | None
      get_doc_widget()      → QWidget | None
      validate_dependencies() → List[str]
    """

    def __init__(self, plugin_info: Optional[PluginInfo] = None):
        self.info: PluginInfo = plugin_info or self.__class__.get_plugin_info()
        self._is_initialized: bool = False
        self._main_widget: Optional[QWidget] = None

    # ------------------------------------------------------------------
    # 必须实现 — 抽象方法
    # ------------------------------------------------------------------

    @classmethod
    @abstractmethod
    def get_plugin_info(cls) -> PluginInfo:
        """
        [必须实现] 返回插件元数据（类方法，注册时调用）

        Example::

            @classmethod
            def get_plugin_info(cls) -> PluginInfo:
                return PluginInfo(
                    name="My Plugin",
                    version="1.0.0",
                    description="插件功能描述",
                    author="Author",
                    category=PluginCategory.UTILITIES,
                    builtin=False,
                )
        """
        ...

    @abstractmethod
    def initialize(self) -> bool:
        """
        [必须实现] 初始化插件（在注册后、首次使用前调用一次）

        Returns:
            bool: True = 初始化成功，False = 失败（插件不会被加载）

        Note:
            - 初始化成功后应设置 self._is_initialized = True
            - 可在此处连接数据库、读取配置文件、预加载资源等
        """
        ...

    @abstractmethod
    def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        [必须实现] 返回插件主界面组件

        Note:
            - 每次调用应返回一个**新**的 QWidget 实例，避免 Qt 对象生命周期问题
            - 不要在插件生命周期内缓存并复用同一个 widget

        Args:
            parent: 父级窗口（可选）

        Returns:
            QWidget: 主界面组件
        """
        ...

    @abstractmethod
    def cleanup(self):
        """
        [必须实现] 释放插件占用的所有资源

        Note:
            - 关闭文件句柄、数据库连接、线程等
            - 不需要手动 deleteLater widget，框架会处理
        """
        ...

    # ------------------------------------------------------------------
    # 推荐实现 — 设置接口
    # ------------------------------------------------------------------

    def get_settings_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """
        [推荐实现] 返回插件设置界面

        框架会在用户点击「设置」按钮时调用此方法，将返回的 widget
        嵌入到标准设置对话框中显示。

        Returns:
            QWidget: 设置界面组件；None 表示该插件没有设置

        Example::

            def get_settings_widget(self, parent=None) -> Optional[QWidget]:
                from .ui.settings_widget import MySettingsWidget
                return MySettingsWidget(self._config, parent)
        """
        return None

    def get_config(self) -> Dict[str, Any]:
        """
        [推荐实现] 读取插件当前配置

        Returns:
            dict: 配置字典（key 为配置项名，value 为配置值）
        """
        return {}

    def set_config(self, config: Dict[str, Any]):
        """
        [推荐实现] 写入插件配置

        Args:
            config: 配置字典
        """
        pass

    # ------------------------------------------------------------------
    # 可选实现 — 输入输出接口
    # ------------------------------------------------------------------

    def on_input(self, channel: str, data: Any):
        """
        [可选实现] 接收外部推送的数据

        框架或其他插件可通过插件管理器向本插件发送数据。

        Args:
            channel : 数据通道名称，用于区分不同类型的输入
            data    : 输入数据（任意类型）

        Example::

            def on_input(self, channel: str, data: Any):
                if channel == "can_frame":
                    self._process_can_frame(data)
        """
        pass

    def get_output(self, channel: str) -> Any:
        """
        [可选实现] 向外部提供输出数据

        Args:
            channel: 数据通道名称

        Returns:
            Any: 输出数据；None 表示无数据

        Example::

            def get_output(self, channel: str) -> Any:
                if channel == "result":
                    return self._last_result
                return None
        """
        return None

    def get_input_channels(self) -> List[str]:
        """[可选实现] 返回支持的输入通道名称列表"""
        return []

    def get_output_channels(self) -> List[str]:
        """[可选实现] 返回支持的输出通道名称列表"""
        return []

    # ------------------------------------------------------------------
    # 可选实现 — 日志接口
    # ------------------------------------------------------------------

    def get_log_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """
        [可选实现] 返回插件专属日志面板

        框架会将此 widget 嵌入到「日志」区域（若插件提供）。

        Returns:
            QWidget: 日志面板；None 表示使用全局日志
        """
        return None

    # ------------------------------------------------------------------
    # 可选实现 — 文档接口
    # ------------------------------------------------------------------

    def get_doc_url(self) -> Optional[str]:
        """
        [可选实现] 返回插件文档的 URL

        Returns:
            str: 文档链接（http/https/file 均可）；None 表示无文档
        """
        return None

    def get_doc_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """
        [可选实现] 返回内嵌文档面板

        优先级高于 get_doc_url()。若两者都返回非 None，框架使用 widget。

        Returns:
            QWidget: 内嵌文档组件；None 表示无内嵌文档
        """
        return None

    # ------------------------------------------------------------------
    # 框架内部辅助方法（不建议覆盖）
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """插件名称"""
        return self.info.name

    @property
    def category(self) -> PluginCategory:
        """插件分类"""
        return self.info.category

    @property
    def is_builtin(self) -> bool:
        """是否为内置插件（内置插件不可卸载）"""
        return self.info.builtin

    def is_initialized(self) -> bool:
        """检查插件是否已完成初始化"""
        return self._is_initialized

    def is_widget_valid(self) -> bool:
        """检查缓存的 main_widget 是否仍然有效（未被 Qt 删除）"""
        if self._main_widget is None:
            return False
        try:
            _ = self._main_widget.objectName()
            return True
        except RuntimeError:
            self._main_widget = None
            return False

    def validate_dependencies(self) -> List[str]:
        """
        [可选覆盖] 验证依赖项是否满足

        Returns:
            List[str]: 缺失的依赖包名列表；空列表表示全部满足
        """
        missing: List[str] = []
        for dep in self.info.dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        return missing
