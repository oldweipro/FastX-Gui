from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QScroller,
    QScrollerProperties,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import (
    FluentIconBase,
    ScrollArea,
    SegmentedWidget,
    SettingCardGroup,
    SwitchSettingCard,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon
from app.common.style_sheet import StyleSheet
from app.components.main_layout_card import ToolBar
from app.tools.ui.qc_composition_ui import QcCompositionUI
from app.tools.ui.rm_comments_ui import RmCommentsUI
from app.tools.ui.FastDem_ui import FastDemToolUI
from app.tools.ui.FastE2E_ui import FastE2EToolUI


class ToolsInterface(ScrollArea):
    """Navigation view interface"""

    def __init__(self, parent=None):
        """
        初始化工具界面

        Args:
            parent: 父级窗口，默认为None
        """
        super().__init__(parent)
        self.view = QWidget(self)
        self.headCard = ToolBar(
            title=self.tr("PlatformTools"),
            subtitle="qfluentwidgets.components.navigation",
            parent=self.view,
        )
        self.headCard.vBoxLayout.setContentsMargins(0,0,0,0)
        self.headCard.setFixedHeight(100)

        self.DemGroup = SettingCardGroup(self.tr("Dem"), self.view)
        self.DcmGroup = SettingCardGroup(self.tr("Dcm"), self.view)
        self.E2EGroup = SettingCardGroup(self.tr("E2E"), self.view)
        self.ComGroup = SettingCardGroup(self.tr("Com"), self.view)
        self.SomeIpGroup = SettingCardGroup(self.tr("SomeIp"), self.view)
        self.SerialGroup = SettingCardGroup(self.tr("Serial"), self.view)
        self.PubGroup = SettingCardGroup(self.tr("Pub"), self.view)
        self.IfGroup = SettingCardGroup(self.tr("IF"), self.view)

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        # 设置对象名称用于样式表
        self.setObjectName("toolInterface")
        # 创建视图容器
        self.view.setObjectName("view")
        # 设置滚动区域属性  | 顶部留出空间给头部卡片 （顺时针-左上右下）
        self.setViewportMargins(0, 48, 0, 0)
        self.setWidget(self.view)
        # 允许widget调整大小
        self.setWidgetResizable(True)
        # 设置纵向滚动条政策
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__setupSmoothScroll()
        # 应用样式表
        StyleSheet.TOOLS_INTERFACE.apply(self)

    def __setupSmoothScroll(self):
        QScroller.grabGesture(
            self.viewport(),
            QScroller.ScrollerGestureType.LeftMouseButtonGesture,
        )
        scroller = QScroller.scroller(self.viewport())
        scroller_props = scroller.scrollerProperties()
        scroller_props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootDragDistanceFactor, 0.05)
        scroller_props.setScrollMetric(
            QScrollerProperties.ScrollMetric.OvershootScrollDistanceFactor,
            0.05,
        )
        scroller_props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.5)
        scroller.setScrollerProperties(scroller_props)

    def __initLayout(self):
        self.pivot = SegmentedWidget(self.view)
        self.stackedWidget = QStackedWidget(self.view)

        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName("mainLayout")
        self.main_layout.setContentsMargins(36, 0, 36, 0)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.Layout.addLayout(self.main_layout)
        self.main_layout.addWidget(self.headCard)
        self.main_layout.addWidget(self.pivot)
        self.main_layout.addWidget(self.stackedWidget)

        # Add Remove Comments tool card
        self.IfGroup.addSettingCard(QcCompositionUI(parent=self.view))
        self.PubGroup.addSettingCard(RmCommentsUI(parent=self.view))
        self.DemGroup.addSettingCard(FastDemToolUI(parent=self.view))
        self.E2EGroup.addSettingCard(FastE2EToolUI(parent=self.view))

        # 添加标签页
        self.addSubInterface(self.DemGroup, "TabDemInterface", self.tr("Dem"))
        self.addSubInterface(self.DcmGroup, "TabDcmInterface", self.tr("Dcm"))
        self.addSubInterface(self.E2EGroup, "TabE2EInterface", self.tr("E2E"))
        self.addSubInterface(self.ComGroup, "TabComInterface", self.tr("Com"))
        self.addSubInterface(self.SomeIpGroup, "TabSomeIpInterface", self.tr("SomeIp"))
        self.addSubInterface(self.SerialGroup, "TabSerialInterface", self.tr("Serial"))
        self.addSubInterface(self.PubGroup, "TabPubInterface", self.tr("Pub"))
        self.addSubInterface(self.IfGroup, "TabIFInterface", self.tr("IF"))

    def __connectSignalToSlot(self):
        # 连接信号并初始化当前标签页
        self.stackedWidget.currentChanged.connect(self.onCurrentIndexChanged)
        self.pivot.setCurrentItem(self.stackedWidget.currentWidget().objectName())
        # self.stackedWidget.setFixedHeight(self.stackedWidget.currentWidget().sizeHint().height())

    def addSubInterface(
        self,
        widget: QWidget,
        objectName: str,
        text: str,
        icon: str | QIcon | FluentIconBase = None,
    ):
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
            icon=icon,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
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
        # 更新堆叠窗口高度 | 使用sizeHint获取建议高度 | 如果有ExpandSettingCard,卡片的高度会被限制在固定高度,无法展开（这里先屏蔽）
        # self.stackedWidget.setFixedHeight(self.stackedWidget.currentWidget().sizeHint().height())


