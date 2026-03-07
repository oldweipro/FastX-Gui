# coding:utf-8
import sys
from enum import Enum
from PySide6.QtCore import Qt, Signal, QModelIndex, Property, QSize
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QStyleOptionViewItem,
    QListWidget,
    QListWidgetItem,
    QListView,
    QWidget,
    QApplication,
    QHBoxLayout,
)
from qfluentwidgets import (
    SmoothScrollBar,
    ListWidget,
    TableItemDelegate,
    TransparentToolButton,
    FluentIcon as FIF
)
from qfluentwidgets.common.overload import singledispatchmethod

from app.common.icon import Icon

class PipsScrollButtonDisplayMode(Enum):
    """Pips pager scroll button display mode"""

    ALWAYS = 0
    ON_HOVER = 1
    NEVER = 2


class PipsDelegate(TableItemDelegate):
    """List item delegate"""

    def __init__(self, parent: QListView):
        super().__init__(parent)

    def _drawBackground(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        # type: ignore[no-undef]
        painter.drawRoundedRect(option.rect, 5, 5)

    def _drawIndicator(
        self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex
    ):
        """绘制首列指示器"""
        return
        # type: ignore[no-undef]
        y, h = option.rect.y(), option.rect.height()
        ph = round(0.35 * h if self.pressedRow == index.row() else 0.257 * h)
        # type: ignore[name-defined]
        painter.setBrush(
            autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor)
        )
        painter.drawRoundedRect(0, ph + y, 3, h - 2 * ph, 1.5, 1.5)


class PipsPager(ListWidget):
    """Pips pager

    Constructors
    ------------
    * PipsPager(`parent`: QWidget = None)
    * PipsPager(`orient`: Qt.Orientation, `parent`: QWidget = None)
    """

    currentIndexChanged = Signal(int)

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.orientation = Qt.Horizontal
        self._postInit()

    @__init__.register
    def _(self, orientation: Qt.Orientation, parent=None):
        super().__init__(parent=parent)
        self.orientation = orientation
        self._postInit()

    def _postInit(self):
        #

        # 控件边距，影响按钮
        # PADDING = TransparentToolButton.sizeHint().width()
        PADDING = 66

        self.setStyleSheet(
            """
                            ListView,
                            ListWidget {
                                background: transparent;
                                outline: none;
                                border: none;
                                /* border: 2px solid red; */
                                /* font: 13px 'Segoe UI', 'Microsoft YaHei'; */
                                selection-background-color: transparent;
                                alternate-background-color: transparent;
                                padding-left: 4px;
                                padding-right: 4px;
                                /*
                                padding-left: 50 px;
                                padding-right: 50px;
                                */
                            }

                            ListView::item,
                            ListWidget::item {
                                background: transparent;
                                border: 0px;
                                /*
                                padding-left: 11px;
                                padding-right: 11px;
                                */
                                height: 35px;
                            }


                            ListView::indicator,
                            ListWidget::indicator {
                                width: 18px;
                                height: 18px;
                                border-radius: 5px;
                                border: none;
                                background-color: transparent;
                                margin-right: 4px;
                            }
                                    """
        )

        self._visibleNumber = 5
        self.isHover = False

        self.delegate = PipsDelegate(self)
        self.scrollBar = SmoothScrollBar(self.orientation, self)

        self.scrollBar.setScrollAnimation(1500)
        self.scrollBar.setForceHidden(True)

        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setGridSize(QSize(36, 36))
        self.setItemDelegate(self.delegate)
        # self.setMovement(QListWidget.Static)
        self.setVerticalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # FluentStyleSheet.PIPS_PAGER.apply(self)

        if self.isHorizontal():
            self.setFlow(QListWidget.LeftToRight)
            self.setViewportMargins(PADDING, 0, PADDING, 0)  # 影响按钮位置
            self.firstButton = TransparentToolButton(FIF.HEART, self)
            self.preButton = TransparentToolButton(FIF.HEART, self)
            self.nextButton = TransparentToolButton(FIF.HEART, self)
            self.lastButton = TransparentToolButton(FIF.HEART, self)
            self.setFixedHeight(36)

            # self.preButton.installEventFilter(ToolTipFilter(self.preButton, 1000, ToolTipPosition.LEFT))
            # self.nextButton.installEventFilter(ToolTipFilter(self.nextButton, 1000, ToolTipPosition.RIGHT))

        else:
            self.setViewportMargins(0, PADDING, 0, PADDING)
            self.firstButton = TransparentToolButton(FIF.HEART, self)
            self.preButton = TransparentToolButton(FIF.HEART, self)
            self.nextButton = TransparentToolButton(FIF.HEART, self)
            self.lastButton = TransparentToolButton(FIF.HEART, self)
            self.setFixedWidth(36)

            # self.preButton.installEventFilter(ToolTipFilter(self.preButton, 1000, ToolTipPosition.TOP))
            # self.nextButton.installEventFilter(ToolTipFilter(self.nextButton, 1000, ToolTipPosition.BOTTOM))

        # 初始化按钮显示模式
        self.firstButtonDisplayMode = PipsScrollButtonDisplayMode.NEVER
        self.previousButtonDisplayMode = PipsScrollButtonDisplayMode.NEVER
        self.nextButtonDisplayMode = PipsScrollButtonDisplayMode.NEVER
        self.lastButtonDisplayMode = PipsScrollButtonDisplayMode.NEVER

        # connect signal to slot
        self.firstButton.clicked.connect(self.scrollFirst)
        self.preButton.clicked.connect(self.scrollPrevious)
        self.nextButton.clicked.connect(self.scrollNext)
        self.lastButton.clicked.connect(self.scrollLast)
        self.itemPressed.connect(self._setPressedItem)
        self.itemEntered.connect(self._setHoveredItem)

    def _setPressedItem(self, item: QListWidgetItem):
        self.delegate.setPressedRow(self.row(item))
        self.setCurrentIndex(self.row(item))

    def _setHoveredItem(self, item: QListWidgetItem):
        # self.delegate.setHoveredRow(self.row(item))
        self.delegate.setHoverRow(self.row(item))

    def setPageNumber(self, n: int) -> None:
        """set the number of page"""
        self.clear()
        self.addItems([str(i + 1) for i in range(n)])

        for i in range(n):
            item = self.item(i)
            # type: ignore[attr-defined]
            item.setData(Qt.ItemDataRole.UserRole, i + 1)
            # type: ignore[attr-defined]
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setSizeHint(self.gridSize())

        self.setCurrentIndex(0)
        self.adjustSize()

    def getPageNumber(self) -> int:
        """get the number of page"""
        return self.count()

    def getVisibleNumber(self) -> int:
        """get the number of visible pips"""
        return self._visibleNumber

    def setVisibleNumber(self, n: int) -> None:
        self._visibleNumber = n
        self.adjustSize()

    def scrollFirst(self) -> None:
        """scroll to first page"""
        self.setCurrentIndex(0)

    def scrollLast(self) -> None:
        """scroll to last page"""
        # type: ignore[operator]
        self.setCurrentIndex(self.pageNumber - 1)

    def scrollNext(self) -> None:
        """scroll to next page"""
        self.setCurrentIndex(self.currentIndex() + 1)

    def scrollPrevious(self) -> None:
        """scroll to previous page"""
        self.setCurrentIndex(self.currentIndex() - 1)

    def scrollToItem(
        self, item: QListWidgetItem, hint: int = QListWidget.ScrollHint.PositionAtCenter
    ) -> None:
        """scroll to item"""
        # scroll to center position
        index = self.row(item)
        size = item.sizeHint()
        s = size.width() if self.isHorizontal() else size.height()
        # type: ignore[operator]
        self.scrollBar.scrollTo(s * (index - self.visibleNumber // 2))

        # clear selection
        self.clearSelection()
        item.setSelected(False)

        self.currentIndexChanged.emit(index)

    def adjustSize(self) -> None:
        """调节分页器的宽度"""
        m = self.viewportMargins()

        # 根据可见按钮盒页数的最小值+4个按钮的宽度设置分页器宽度
        if self.isHorizontal():
            # w = self.visibleNumber * self.gridSize().width() + m.left() + m.right()
            # type: ignore[operator, call-overload]
            w = (min(self.visibleNumber, self.pageNumber) + 4) * self.gridSize().width()
            self.setFixedWidth(w)
        else:
            # h = self.visibleNumber * self.gridSize().height() + m.top() + m.bottom()
            # type: ignore[operator, call-overload]
            h = (
                min(self.visibleNumber, self.pageNumber) + 4
            ) * self.gridSize().height()
            self.setFixedHeight(h)

    def isHorizontal(self) -> bool:
        # type: ignore[attr-defined]
        return self.orientation == Qt.Orientation.Horizontal

    def setCurrentIndex(self, index: int) -> None:
        """set current index"""
        if not 0 <= index < self.count():
            return

        item = self.item(index)
        self.scrollToItem(item)
        super().setCurrentItem(item)

        self._updateScrollButtonVisibility()

    def isFirstButtonVisible(self) -> bool:
        if (
            self.currentIndex() <= self._visibleNumber // 2
            or self.firstButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER
        ):
            return False

        if self.firstButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def isPreviousButtonVisible(self) -> bool:
        if (
            self.currentIndex() <= 0
            or self.previousButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER
        ):
            return False

        if self.previousButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def isNextButtonVisible(self) -> bool:
        if (
            self.currentIndex() >= self.count() - 1
            or self.nextButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER
        ):
            return False

        if self.nextButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def isLastButtonVisible(self) -> bool:
        if (
            self.currentIndex() >= self.count() - self._visibleNumber // 2 - 1
            or self.lastButtonDisplayMode == PipsScrollButtonDisplayMode.NEVER
        ):
            return False

        if self.lastButtonDisplayMode == PipsScrollButtonDisplayMode.ON_HOVER:
            return self.isHover

        return True

    def currentIndex(self) -> int:
        return super().currentIndex().row()

    def setFirstButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode) -> None:
        """set the display mode of first button"""
        self.firstButtonDisplayMode = mode
        self.firstButton.setEnabled(self.isFirstButtonVisible())

    def setPreviousButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode) -> None:
        """set the display mode of previous button"""
        self.previousButtonDisplayMode = mode
        self.preButton.setEnabled(self.isPreviousButtonVisible())

    def setNextButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode) -> None:
        """set the display mode of next button"""
        self.nextButtonDisplayMode = mode
        self.nextButton.setEnabled(self.isNextButtonVisible())

    def setLastButtonDisplayMode(self, mode: PipsScrollButtonDisplayMode) -> None:
        """set the display mode of last button"""
        self.lastButtonDisplayMode = mode
        self.lastButton.setEnabled(self.isLastButtonVisible())

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.delegate.setPressedRow(-1)

    def enterEvent(self, e):
        super().enterEvent(e)
        self.isHover = True
        self._updateScrollButtonVisibility()

    def leaveEvent(self, e):
        super().leaveEvent(e)
        self.isHover = False
        # self.delegate.setHoveredRow(-1)
        self.delegate.setHoverRow(-1)
        self._updateScrollButtonVisibility()

    def _updateScrollButtonVisibility(self):
        self.firstButton.setEnabled(self.isFirstButtonVisible())
        self.preButton.setEnabled(self.isPreviousButtonVisible())
        self.nextButton.setEnabled(self.isNextButtonVisible())
        self.lastButton.setEnabled(self.isLastButtonVisible())

    def wheelEvent(self, e):
        pass

    def resizeEvent(self, e):
        """调节4个按钮的位置"""
        w, h = self.width(), self.height()
        # bw, bh = self.preButton.width(), self.preButton.height()
        # if self.isHorizontal():
        #     self.preButton.move(0, int(h / 2 - bh / 2))
        #     self.nextButton.move(w - bw, int(h / 2 - bh / 2))
        # else:
        #     self.preButton.move(int(w / 2 - bw / 2), 0)
        #     self.nextButton.move(int(w / 2 - bw / 2), h - bh)

        pw, ph = self.gridSize().width(), self.gridSize().height()
        bw, bh = self.preButton.sizeHint().width(), self.preButton.sizeHint().height()

        if self.isHorizontal():
            self.firstButton.move(0, int(h / 2 - bh / 2))
            self.preButton.move(bw, int(h / 2 - bh / 2))
            self.nextButton.move(
                bw * 2 + pw * min(self._visibleNumber, self.count()),
                int(h / 2 - bh / 2),
            )
            self.lastButton.move(
                bw * 3 + pw * min(self._visibleNumber, self.count()),
                int(h / 2 - bh / 2),
            )
        else:
            self.firstButton.move(int(w / 2 - bw / 2), 0)
            self.preButton.move(int(w / 2 - bw / 2), bh)
            self.nextButton.move(int(w / 2 - bw / 2), bh * 2 + ph * self._visibleNumber)
            self.lastButton.move(int(w / 2 - bw / 2), bh * 3 + ph * self._visibleNumber)

    visibleNumber = Property(int, getVisibleNumber, setVisibleNumber)
    pageNumber = Property(int, getPageNumber, setPageNumber)


class HorizontalPipsPager(PipsPager):
    """Horizontal pips pager"""

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)


class VerticalPipsPager(PipsPager):
    """Vertical pips pager"""

    def __init__(self, parent=None):
        super().__init__(Qt.Vertical, parent)


class Demo(QWidget):

    def __init__(self):
        super().__init__()
        # setTheme(Theme.DARK)
        # self.setStyleSheet('Demo{background:rgb(32,32,32)}')

        self.vPager = VerticalPipsPager(self)
        self.hPager = HorizontalPipsPager(self)

        # set the number of page
        self.hPager.setPageNumber(17)
        self.vPager.setPageNumber(17)

        # set the number of displayed pips
        self.hPager.setVisibleNumber(7)
        self.hPager.setFirstButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.hPager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.hPager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.hPager.setLastButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)

        # set the display mode of scroll button
        self.vPager.setNextButtonDisplayMode(PipsScrollButtonDisplayMode.ALWAYS)
        self.vPager.setPreviousButtonDisplayMode(PipsScrollButtonDisplayMode.ON_HOVER)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.hPager)
        self.layout().addWidget(self.vPager)

        self.resize(1500, 500)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Demo()
    w.show()
    app.exec()
