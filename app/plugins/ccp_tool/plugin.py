"""
CCP Tool 插件 — 标准接口实现样板
==========================================

本文件演示了 PluginBase 所有接口的实现方式，
可作为开发新插件的参考模板。
"""

from typing import Any, Dict, List, Optional
from PySide6.QtWidgets import QWidget

from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory
from .ui.main_widget import CCPMainWidget
from .ui.settings_widget import CCPSettingsWidget


class CCPToolPlugin(PluginBase):
    """
    CCP Tool 插件 — 完整接口实现

    目录结构
    ─────────────────────────────────
    ccp_tool/
    ├── __init__.py          # 导出插件类
    ├── plugin.py            # 插件主类（本文件）
    ├── manifest.json        # 插件元数据
    ├── core/
    │   ├── processor.py     # 核心业务逻辑
    │   └── ...
    ├── models/
    │   └── ...              # 数据模型
    ├── service/
    │   └── ...              # 服务层
    ├── ui/
    │   ├── main_widget.py   # 主界面（get_main_widget 返回）
    │   ├── settings_widget.py # 设置界面（get_settings_widget 返回）
    │   └── ...
    └── resources/
        └── ...              # 图标、文档等资源
    """

    # ------------------------------------------------------------------
    # [必须实现] 插件元数据
    # ------------------------------------------------------------------

    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="CCP Tool",
            version="1.0.0",
            description="CCP 协议诊断和分析工具，支持 XCP/CCP 报文解析与生成",
            author="FastXTeam",
            category=PluginCategory.DIAGNOSTIC,
            icon_path="CCP",          # Icon 枚举名
            dependencies=[],          # 无额外 Python 依赖
            enabled=True,
            builtin=True,             # 内置插件，不可卸载
        )

    # ------------------------------------------------------------------
    # [必须实现] 生命周期
    # ------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self._config: Dict[str, Any] = {
            "input_file": "",
            "output_folder": "",
            "selected_option": 0,
        }
        self._main_widget: Optional[CCPMainWidget] = None

    def initialize(self) -> bool:
        """初始化插件，加载配置、检查环境"""
        try:
            # 此处可读取持久化配置
            self._is_initialized = True
            return True
        except Exception as e:
            print(f"[CCPTool] 初始化失败: {e}")
            return False

    def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """每次调用返回新的主界面实例"""
        widget = CCPMainWidget(parent)
        widget.set_config(self._config)
        self._main_widget = widget
        return widget

    def cleanup(self):
        """释放资源"""
        if self._main_widget:
            try:
                self._main_widget.cleanup()
            except Exception:
                pass
            self._main_widget = None
        self._config.clear()

    # ------------------------------------------------------------------
    # [推荐实现] 设置接口
    # ------------------------------------------------------------------

    def get_settings_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
        """返回插件设置面板，嵌入到框架设置对话框中"""
        return CCPSettingsWidget(self._config, parent)

    def get_config(self) -> Dict[str, Any]:
        if self._main_widget:
            try:
                self._config.update(self._main_widget.get_config())
            except Exception:
                pass
        return self._config.copy()

    def set_config(self, config: Dict[str, Any]):
        self._config.update(config)
        if self._main_widget:
            try:
                self._main_widget.set_config(config)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # [可选实现] 输入输出通道
    # ------------------------------------------------------------------

    def get_input_channels(self) -> List[str]:
        """声明支持接收的数据通道"""
        return ["can_frame", "raw_bytes"]

    def get_output_channels(self) -> List[str]:
        """声明可对外提供的数据通道"""
        return ["parsed_result", "log_entries"]

    def on_input(self, channel: str, data: Any):
        """接收外部推送的数据"""
        if channel == "can_frame" and self._main_widget:
            # 将 CAN 帧传递给主界面处理
            try:
                self._main_widget.on_can_frame_received(data)
            except Exception:
                pass

    def get_output(self, channel: str) -> Any:
        """向外部提供数据"""
        if channel == "parsed_result" and self._main_widget:
            try:
                return self._main_widget.get_last_result()
            except Exception:
                pass
        return None

    # ------------------------------------------------------------------
    # [可选实现] 文档接口
    # ------------------------------------------------------------------

    def get_doc_url(self) -> Optional[str]:
        """返回插件文档 URL"""
        return "https://docs.fastx.internal/ccp-tool"
