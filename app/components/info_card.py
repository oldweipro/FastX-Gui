# coding:utf-8
from pathlib import Path
from typing import List
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (BodyLabel, TransparentToolButton, FluentIcon, ElevatedCardWidget,
                            ImageLabel, SimpleCardWidget, HyperlinkLabel, VerticalSeparator,
                            PrimaryPushButton, TitleLabel, PillPushButton, setFont)

from app.components.statistic_widget import StatisticsWidget


class CompactTagContainer(QWidget):
    """紧凑标签容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)  # 设置较小的间距，使标签紧凑

        # 添加弹簧，使标签靠左
        self.layout.addStretch(1)

        self.tags = []

    def add_tag(self, text: str) -> PillPushButton:
        """添加标签并返回标签按钮"""
        tag = PillPushButton(text, self)
        tag.setCheckable(False)
        setFont(tag, 12)
        tag.setFixedSize(80, 32)

        self.layout.addWidget(tag)
        self.tags.append(tag)
        return tag

    def add_tags(self, texts: List[str]):
        """批量添加标签"""
        for text in texts:
            self.add_tag(text)


class AppInfoCard(SimpleCardWidget):
    """ M3U8DL information card """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)
        self.iconLabel = ImageLabel(QIcon(":/app/images/ico/M3U8DL.ico").pixmap(120, 120), self)

        self.nameLabel = TitleLabel(self.tr('FastRte'), self)
        self.updateButton = PrimaryPushButton(self.tr("Update"), self)
        self.companyLabel = HyperlinkLabel(QUrl('https://github.com/fastxteam/FastX-Gui'), 'FastXTeam', self)
        self.versionWidget = StatisticsWidget(self.tr('Version'), 'v0.1.0', self)
        self.fileSizeWidget = StatisticsWidget(self.tr('File Size'), '19MB', self)
        self.updateTimeWidget = StatisticsWidget(self.tr('Update Time'), '2026-01-19', self)

        self.descriptionLabel = BodyLabel(
            self.tr(
                'Rte Connecter is an application tool. The current application field is AUTOSAR CP. The adaptation tool ETAS is used to connect RTE wiring between SWCs. It can generate DataType, Interface and Composition Rte wiring from the table content, which greatly improves the development speed.'),
            self)

        # 使用紧凑标签容器
        self.tag_container = CompactTagContainer(self)

        self.shareButton = TransparentToolButton(FluentIcon.SHARE, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.bottomLayout = QHBoxLayout()  # 底部布局，包含标签容器和分享按钮

        self.__initWidgets()

    def __initWidgets(self):
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(120)

        self.updateButton.setFixedWidth(160)

        self.descriptionLabel.setWordWrap(True)
        # self.shareButton.clicked.connect(lambda: openUrl(DEPLOY_URL))

        self.shareButton.setFixedSize(32, 32)
        self.shareButton.setIconSize(QSize(14, 14))

        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")

        # 初始化标签
        self.tag_container.add_tags(['FUNC', 'IPC', 'SRP'])

        self.initLayout()

    def initLayout(self):
        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # name label and install button
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.updateButton, 0, Qt.AlignRight)

        # company label
        self.vBoxLayout.addSpacing(3)
        self.vBoxLayout.addWidget(self.companyLabel)

        # statistics widgets
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.statisticsLayout)
        self.statisticsLayout.setContentsMargins(0, 0, 0, 0)
        self.statisticsLayout.setSpacing(10)
        self.statisticsLayout.addWidget(self.versionWidget)
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.fileSizeWidget)
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.updateTimeWidget)
        self.statisticsLayout.setAlignment(Qt.AlignLeft)

        # description label
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # 底部布局：标签容器 + 分享按钮
        self.vBoxLayout.addSpacing(12)
        self.bottomLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.bottomLayout)
        # 添加标签容器
        self.bottomLayout.addWidget(self.tag_container)
        # 添加弹簧使分享按钮靠右
        self.bottomLayout.addStretch(1)
        # 分享按钮靠右
        self.bottomLayout.addWidget(self.shareButton, 0, Qt.AlignRight)

    def setVersion(self, version: str):
        text = version or '0.1.0'
        self.versionWidget.valueLabel.setText(text)
        self.versionWidget.valueLabel.setTextColor(QColor(0, 0, 0), QColor(255, 255, 255))