# coding:utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QLabel
from qfluentwidgets import TabWidget, SubtitleLabel, setFont, IconWidget
from qfluentwidgets import FluentIcon as FIF


class TabContent(QWidget):
    """ 标签页内容部件 """

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        setFont(self.label, 24)
        self.setObjectName(text.replace(' ', '-'))


class AppInterface(QWidget):
    """ 应用界面，包含标签页功能 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tabWidget = TabWidget(self)
        self.vBoxLayout = QVBoxLayout(self)
        
        self.__initWidget()
        self.__initLayout()
        self.__initTabs()

    def __initWidget(self):
        """ 初始化小部件 """
        self.setObjectName('appInterface')
        
        # 设置标签页属性
        self.tabWidget.setMovable(True)  # 允许标签页拖动
        self.tabWidget.setTabsClosable(True)  # 允许关闭标签页
        # 注意：tabAddRequested信号默认是可用的，不需要额外设置

    def __initLayout(self):
        """ 初始化布局 """
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.tabWidget)

    def __initTabs(self):
        """ 初始化标签页 """
        # 添加默认主页标签页
        self.addHomeTab()
        
        # 连接信号和槽
        self.tabWidget.tabAddRequested.connect(self.addNewTab)
        self.tabWidget.tabCloseRequested.connect(self.tabWidget.removeTab)

    def addHomeTab(self):
        """ 添加默认主页标签页 """
        homeContent = TabContent('默认主页', self)
        self.tabWidget.addTab(
            homeContent,
            '默认主页', 
            icon=FIF.HOME
        )

    def addNewTab(self):
        """ 添加新标签页 """
        tabCount = self.tabWidget.count()
        if tabCount == 0:
            self.addHomeTab()
            return
        text = f'新标签页 {tabCount}'
        content = TabContent(text, self)
        
        self.tabWidget.addTab(
            content, 
            text, 
            icon=FIF.BRIGHTNESS
        )
