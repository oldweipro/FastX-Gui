from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    CheckBox,
    ExpandSettingCard,
    FluentIconBase,
    IndicatorPosition,
    SwitchButton,
)


class AutoPlotSettingCard(ExpandSettingCard):
    """Setting card for auto plot with switch and expandable options"""

    switchChanged = pyqtSignal(bool)
    optionsChanged = pyqtSignal(dict)

    def __init__(
        self,
        icon: str | QIcon | FluentIconBase,
        title,
        content=None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        # Switch button
        self.switchButton = SwitchButton("关", self, IndicatorPosition.RIGHT)
        # Add switch button to card layout using addWidget method
        self.card.addWidget(self.switchButton)
        # Configuration options
        self._init_options()
        # Connect signals
        self.switchButton.checkedChanged.connect(self.__onSwitchChanged)

    def _init_options(self):
        """Initialize configuration options in the expandable view"""
        # Create widgets container
        self.viewLayout.setSpacing(19)
        self.viewLayout.setContentsMargins(5, 18, 5, 18)

        # 添加选择Combox
        # 创建主widget
        self.comboxCard = QWidget(self)
        self.comboxCard.setObjectName("widget")

        # 主水平布局
        self.horizontalLayout = QHBoxLayout(self.comboxCard)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        # 用于存储所有CheckBox的列表
        self.checkboxes = []
        # 创建6列，每列8个CheckBox（总共48个）
        for col in range(6):  # 6列
            verticalLayout = QVBoxLayout()
            verticalLayout.setObjectName(f"verticalLayout_col_{col}")
            for row in range(8):  # 每列8个
                checkbox_num = col * 8 + row  # 从0开始编号
                checkbox = CheckBox(self.comboxCard)
                checkbox.setText("")
                checkbox.setChecked(False)
                checkbox.setObjectName(f"CheckBox_{checkbox_num}")
                # 添加到垂直布局
                verticalLayout.addWidget(checkbox)
                # 存储到列表中以便后续访问
                self.checkboxes.append(checkbox)
            # 添加到水平布局
            self.horizontalLayout.addLayout(verticalLayout)
        self.viewLayout.addWidget(self.comboxCard)

        # Adjust view size
        self._adjustViewSize()

    def __onSwitchChanged(self, isChecked: bool):
        """Switch button checked state changed slot"""
        self.setValue(isChecked)
        self.switchChanged.emit(isChecked)

    def setValue(self, isChecked: bool):
        """Set switch button state"""
        self.switchButton.setChecked(isChecked)
        self.switchButton.setText("开" if isChecked else "关")

    def getSwitchState(self) -> bool:
        """Get current switch state"""
        return self.switchButton.isChecked()
