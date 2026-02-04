from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    IconWidget,
)


class GuideWidget(CardWidget):
    def __init__(self, parent, icon, title, content):
        super().__init__(parent=parent)
        self.icon_widget = IconWidget(icon)
        self.title_label = BodyLabel(title, self)
        self.content_label = CaptionLabel(content, self)

        self.h_box_layout = QHBoxLayout(self)
        self.v_box_layout = QVBoxLayout()

        self.setFixedHeight(73)
        self.icon_widget.setFixedSize(48, 48)

        self.h_box_layout.setContentsMargins(20, 11, 11, 11)
        self.h_box_layout.setSpacing(15)
        self.h_box_layout.addWidget(self.icon_widget)

        self.v_box_layout.setContentsMargins(0, 0, 0, 0)
        self.v_box_layout.setSpacing(0)
        self.v_box_layout.addWidget(self.title_label, 0, Qt.AlignVCenter)
        self.v_box_layout.addWidget(self.content_label, 0, Qt.AlignVCenter)
        self.v_box_layout.setAlignment(Qt.AlignVCenter)
        self.h_box_layout.addLayout(self.v_box_layout)
