# coding:utf-8
from typing import Union

from PyQt5.QtCore import Qt, QEasingCurve
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QSizePolicy, QSpacerItem, \
    QScroller, QScrollerProperties
from qfluentwidgets import (Pivot, qrouter, SegmentedWidget, TabBar, CheckBox, ComboBox,
                            TabCloseButtonDisplayMode, BodyLabel, SpinBox, BreadcrumbBar,
                            SegmentedToggleToolWidget, ScrollArea, SettingCardGroup, SwitchSettingCard,
                            SegmentedToolWidget, FluentIconBase)
from qfluentwidgets import FluentIcon as FIF

from app.common.config import cfg
from app.common.translator import Translator
from app.common.style_sheet import StyleSheet
from app.components.pivot import SettingPivot

class ToolsInterface(ScrollArea):
    """ Navigation view interface """
    def __init__(self, parent=None):
        """
        初始化工具界面

        Args:
            parent: 父级窗口，默认为None
        """
        super().__init__(parent)
        self.view = QWidget(self)
        self.platformToolsLabel = QLabel(self.tr("PlatformTools"), self)
        self.platformToolsLabel.setObjectName('platformToolsLabel')

        self.DemGroup = SettingCardGroup(self.tr("Dem"), self.view)
        self.micaCard1 = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.DemGroup
        )

        self.DcmGroup = SettingCardGroup(self.tr("Dcm"), self.view)
        self.micaCard2 = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.DcmGroup
        )

        self.E2EGroup = SettingCardGroup(self.tr("E2E"), self.view)
        self.micaCard3 = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.E2EGroup
        )

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        # 设置对象名称用于样式表
        self.setObjectName("toolInterface")
        # 创建视图容器
        self.view.setObjectName('view')
        # 设置滚动区域属性  | 顶部留出空间给头部卡片 （顺时针-左上右下）
        self.setViewportMargins(0, 146, 0, 0)
        self.setWidget(self.view)
        # 允许widget调整大小
        self.setWidgetResizable(True)
        # 设置纵向滚动条政策
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__setupSmoothScroll()
        # 应用样式表
        StyleSheet.TOOLS_INTERFACE.apply(self)

    def __setupSmoothScroll(self):
        QScroller.grabGesture(self.viewport(), QScroller.ScrollerGestureType.LeftMouseButtonGesture)
        scroller = QScroller.scroller(self.viewport())
        scroller_props = scroller.scrollerProperties()
        scroller_props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootDragDistanceFactor, 0.05)
        scroller_props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootScrollDistanceFactor, 0.05)
        scroller_props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.5)
        scroller.setScrollerProperties(scroller_props)

    def __initLayout(self):
        self.pivot = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(36, 0, 36, 0)
        self.platformToolsLabel.move(36, 48)
        self.pivot.move(40, 98)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName('mainLayout')
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.Layout.addLayout(self.main_layout)
        self.main_layout.addWidget(self.stackedWidget)

        self.DemGroup.addSettingCard(self.micaCard1)
        self.DcmGroup.addSettingCard(self.micaCard2)
        self.E2EGroup.addSettingCard(self.micaCard3)

        # 添加标签页
        self.addSubInterface(self.DemGroup, 'DemInterface', self.tr('Dem'))
        self.addSubInterface(self.DcmGroup, 'DcmInterface', self.tr('Dcm'))
        self.addSubInterface(self.E2EGroup, 'E2EInterface', self.tr('E2E'))

    def __connectSignalToSlot(self):
        # 连接信号并初始化当前标签页
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.pivot.setCurrentItem(self.stackedWidget.currentWidget().objectName())
        self.stackedWidget.setFixedHeight(self.stackedWidget.currentWidget().sizeHint().height())

    def addSubInterface(self, widget: QLabel, objectName: str, text: str, icon: Union[str, QIcon, FluentIconBase]=None):
        """
        添加子界面到标签页系统

        Args:
            :param widget:
            :param objectName:
            :param text:
            :param icon:
        """
        def remove_spacing(layout):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if isinstance(item, QSpacerItem):
                    layout.removeItem(item)
                    break
        # 优化组件布局，移除多余间距
        remove_spacing(widget.vBoxLayout)
        # 隐藏组标题，使用标签页标题
        widget.titleLabel.setHidden(True)
        # 设置组件属性
        widget.setObjectName(objectName)
        # 添加到堆叠窗口
        self.stackedWidget.addWidget(widget)
        # 添加到导航栏 | 使用全局唯一的 objectName 作为路由键
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            icon = icon,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        """
        当前页面变化事件处理

        Args:
            index: 新页面的索引
        """
        # 更新导航栏状态
        widget = self.stackedWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())
        # 滚动到顶部
        self.verticalScrollBar().setValue(0)
        # 更新堆叠窗口高度 | 使用sizeHint获取建议高度
        self.stackedWidget.setFixedHeight(self.stackedWidget.currentWidget().sizeHint().height())