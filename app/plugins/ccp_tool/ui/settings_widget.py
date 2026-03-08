"""
CCP Tool 设置界面
================================
实现 PluginBase.get_settings_widget() 接口的标准样板。

框架会将此 widget 嵌入设置对话框的右侧"插件配置"区域。
"""

from typing import Any, Dict, Optional
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    PushSettingCard, SwitchSettingCard,
    SettingCardGroup, FluentIcon as FIF
)
from PySide6.QtWidgets import QFileDialog

from app.common.config import cfg


class CCPSettingsWidget(QWidget):
    """
    CCP Tool 设置面板

    通过 get_settings_widget() 暴露给插件框架，
    嵌入到标准"插件配置"对话框中。

    规范
    ────
    - 必须接收 config dict 并在 __init__ 中初始化 UI 状态
    - 建议提供 get_config() 方法，供框架读取最新配置
    - 可以发出 configChanged 信号通知框架配置已变更
    """

    configChanged = Signal(dict)  # 配置发生变化时发出

    def __init__(self, config: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._config = dict(config)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        group = SettingCardGroup("CCP Tool 设置", self)

        # 输入文件路径
        self.input_file_card = PushSettingCard(
            "选择文件",
            FIF.DOCUMENT,
            "输入文件",
            self._config.get("input_file") or "未选择",
            group,
        )
        self.input_file_card.clicked.connect(self._on_choose_input_file)
        group.addSettingCard(self.input_file_card)

        # 输出目录
        self.output_folder_card = PushSettingCard(
            "选择目录",
            FIF.FOLDER_ADD,
            "输出目录",
            self._config.get("output_folder") or "未选择",
            group,
        )
        self.output_folder_card.clicked.connect(self._on_choose_output_folder)
        group.addSettingCard(self.output_folder_card)

        layout.addWidget(group)
        layout.addStretch(1)

    def _on_choose_input_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择输入文件",
            self._config.get("input_file") or "",
            "所有文件 (*.*);;Excel 文件 (*.xlsx);;ARXML 文件 (*.arxml)",
        )
        if path:
            self._config["input_file"] = path
            self.input_file_card.setContent(path)
            self.configChanged.emit(self._config)

    def _on_choose_output_folder(self):
        path = QFileDialog.getExistingDirectory(
            self, "选择输出目录",
            self._config.get("output_folder") or "",
        )
        if path:
            self._config["output_folder"] = path
            self.output_folder_card.setContent(path)
            self.configChanged.emit(self._config)

    def get_config(self) -> Dict[str, Any]:
        """框架调用此方法读取最新配置"""
        return self._config.copy()
