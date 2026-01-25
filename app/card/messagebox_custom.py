from PyQt5.QtCore import Qt, QUrl, QSize
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QSpinBox, QVBoxLayout, QPushButton, QToolButton, QCompleter, QCheckBox
from PyQt5.QtGui import QPixmap, QDesktopServices, QFont
from qfluentwidgets import (MessageBox, LineEdit, ComboBox, EditableComboBox, DateTimeEdit,
                            BodyLabel, FluentStyleSheet, TextEdit, Slider, FluentIcon, qconfig,
                            isDarkTheme, PrimaryPushSettingCard, InfoBar, InfoBarPosition, PushButton, SpinBox, CheckBox)
from app.common.config import cfg

def _cleanup_infobars(widget):
    """Safely hide/close/delete any InfoBar children of `widget`.

    This helps avoid QPainter warnings when a parent widget is closing
    while an InfoBar is still animating/painting.
    """
    try:
        for bar in widget.findChildren(InfoBar):
            try:
                bar.hide()
            except Exception:
                pass
            try:
                bar.close()
            except Exception:
                pass
            try:
                bar.deleteLater()
            except Exception:
                pass
    except Exception:
        pass


def setup_completer(combo_box, items):
    """
    为 EditableComboBox 设置自动补全器
    :param combo_box: EditableComboBox 实例
    :param items: 选项列表
    """
    completer = QCompleter(items)
    completer.setCaseSensitivity(Qt.CaseInsensitive)  # 设置大小写不敏感
    completer.setFilterMode(Qt.MatchContains)  # 设置匹配模式为包含（支持部分匹配）
    combo_box.setCompleter(completer)

class MessageBoxCloseWindow(MessageBox):
    """关闭窗口询问对话框"""

    def __init__(self, parent=None):
        super().__init__(
            '关闭确认',
            '您希望如何处理程序?',
            parent
        )

        # 修改按钮文本
        self.yesButton.setText('最小化到托盘')
        self.cancelButton.setText('关闭程序')

        # 添加记住选择的复选框ComboBoxSettingCard2
        self.rememberCheckBox = CheckBox('记住我的选择,下次不再询问', self)
        self.textLayout.addWidget(self.rememberCheckBox)

        # 存储用户的选择
        self.action = None  # 'minimize' 或 'close'

    def accept(self):
        """用户选择最小化到托盘"""
        self.action = 'minimize'
        if self.rememberCheckBox.isChecked():
            cfg.set(cfg.close_window_action, 'minimize')
            pass
        _cleanup_infobars(self)
        super().accept()

    def reject(self):
        """用户选择关闭程序"""
        self.action = 'close'
        if self.rememberCheckBox.isChecked():
            cfg.set(cfg.close_window_action, 'close')
            pass
        _cleanup_infobars(self)
        super().reject()
