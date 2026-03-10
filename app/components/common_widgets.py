"""
通用UI组件 - 不依赖zbWidgetLib
"""

import functools
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, QPoint, QSize, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QPen, QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from qfluentwidgets import (
    SmoothScrollArea, CardWidget, InfoBadge, InfoBadgeManager,
    FlyoutAnimationManager, FluentIconBase, isDarkTheme, themeColor
)
from qfluentwidgets.common.icon import toQIcon


class BetterScrollArea(SmoothScrollArea):
    """优化样式的滚动区域"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea {background-color: rgba(0,0,0,0); border: none}")

        self.setScrollAnimation(Qt.Vertical, 500, QEasingCurve.OutQuint)
        self.setScrollAnimation(Qt.Horizontal, 500, QEasingCurve.OutQuint)

        self.view = QWidget(self)
        self.view.setStyleSheet("QWidget {background-color: rgba(0,0,0,0); border: none}")
        self.setWidget(self.view)

        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setSpacing(30)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)


class CardGroup(QWidget):
    """卡片组 - 管理多个卡片组件"""

    def __init__(self, parent=None, show_title: bool = False, is_vertical: bool = True):
        super().__init__(parent=parent)
        self._cards = []
        self._cardMap = {}

        if is_vertical:
            self.boxLayout = QVBoxLayout(self)
        else:
            self.boxLayout = QHBoxLayout(self)
        
        self.boxLayout.setSpacing(5)
        self.boxLayout.setContentsMargins(0, 0, 0, 0)
        self.boxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.vBoxLayout = self.boxLayout
        self.hBoxLayout = self.boxLayout

    def addCard(self, card, wid: str = None, pos: int = -1):
        """添加卡片"""
        if not wid:
            wid = hex(id(card))
        if wid in self._cardMap:
            raise KeyError(f"Card id {wid} already exists")
        if pos >= 0:
            pos += 1
        self.boxLayout.insertWidget(pos, card, 0, Qt.AlignmentFlag.AlignTop)
        self._cards.append(card)
        self._cardMap[wid] = card
        return wid

    def removeCard(self, wid: str):
        """移除卡片"""
        if wid not in self._cardMap:
            return
        card = self._cardMap.pop(wid)
        self._cards.remove(card)
        self.boxLayout.removeWidget(card)
        card.hide()
        card.deleteLater()

    def getCard(self, wid: str):
        """获取卡片"""
        return self._cardMap.get(wid)

    def count(self):
        """卡片数量"""
        return len(self._cards)


class CustomProgressBar(QProgressBar):
    """自定义进度条 - 支持确定/不确定模式"""

    def __init__(self, parent=None, useAni=True, indeterminate=False, height=4):
        super().__init__(parent)
        
        self._indeterminate = indeterminate
        self._useAni = useAni
        self._val = 0
        
        # 动画相关
        self._shortPos = 0
        self._longPos = 0
        self._animationGroup = None
        
        self.setFixedHeight(height)
        self.setValue(0)
        
        if indeterminate:
            self._initAnimations()
            self._animationGroup.start()

    def _initAnimations(self):
        """初始化不确定模式动画"""
        self.shortBarAni = QPropertyAnimation(self, b'shortPos', self)
        self.longBarAni = QPropertyAnimation(self, b'longPos', self)
        
        self.shortBarAni.setDuration(833)
        self.longBarAni.setDuration(1167)
        self.shortBarAni.setStartValue(0)
        self.longBarAni.setStartValue(0)
        self.shortBarAni.setEndValue(1.45)
        self.longBarAni.setEndValue(1.75)
        self.longBarAni.setEasingCurve(QEasingCurve.OutQuad)
        
        from PySide6.QtCore import QParallelAnimationGroup, QSequentialAnimationGroup
        self.longBarAniGroup = QSequentialAnimationGroup(self)
        self.longBarAniGroup.addPause(785)
        self.longBarAniGroup.addAnimation(self.longBarAni)
        
        self._animationGroup = QParallelAnimationGroup(self)
        self._animationGroup.addAnimation(self.shortBarAni)
        self._animationGroup.addAnimation(self.longBarAniGroup)
        self._animationGroup.setLoopCount(-1)

    @Property(float)
    def shortPos(self):
        return self._shortPos

    @shortPos.setter
    def shortPos(self, p):
        self._shortPos = p
        if self._indeterminate:
            self.update()

    @Property(float)
    def longPos(self):
        return self._longPos

    @longPos.setter
    def longPos(self, p):
        self._longPos = p
        if self._indeterminate:
            self.update()

    def isIndeterminate(self):
        return self._indeterminate

    def setIndeterminate(self, indeterminate: bool):
        if self._indeterminate != indeterminate:
            self._indeterminate = indeterminate
            if indeterminate:
                if not self._animationGroup:
                    self._initAnimations()
                self._animationGroup.start()
            else:
                if self._animationGroup:
                    self._animationGroup.stop()
            self.update()

    def setValue(self, value: int):
        self._val = value
        super().setValue(value)
        if not self._indeterminate:
            self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        
        # 背景色
        bgColor = QColor(255, 255, 255, 155) if isDarkTheme() else QColor(0, 0, 0, 155)
        painter.setPen(bgColor)
        from math import floor
        y = floor(self.height() / 2)
        painter.drawLine(0, y, self.width(), y)
        
        # 进度条颜色
        barColor = themeColor()
        
        if self._indeterminate:
            painter.setPen(Qt.NoPen)
            painter.setBrush(barColor)
            
            x = int((self._shortPos - 0.4) * self.width())
            w = int(0.4 * self.width())
            radius = self.height() / 2
            painter.drawRoundedRect(x, 0, w, self.height(), radius, radius)
            
            x = int((self._longPos - 0.6) * self.width())
            w = int(0.6 * self.width())
            painter.drawRoundedRect(x, 0, w, self.height(), radius, radius)
        else:
            if self.minimum() >= self.maximum():
                return
            painter.setPen(Qt.NoPen)
            painter.setBrush(barColor)
            w = int(self._val / (self.maximum() - self.minimum()) * self.width())
            radius = self.height() / 2
            painter.drawRoundedRect(0, 0, w, self.height(), radius, radius)


class WebImage(QLabel):
    """支持网络图片的图片组件"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(48, 48)
        self.setScaledContents(True)
        self.loading = False

    def setImg(self, img: str | FluentIconBase, url: str = None, thread_pool: ThreadPoolExecutor = None):
        """设置图片"""
        if url and thread_pool:
            self.loading = True
            self.path = img
            self.url = url
            thread_pool.submit(self._download)
        else:
            self.loading = False
            if isinstance(img, str):
                self.setPixmap(QPixmap(img))
            elif isinstance(img, FluentIconBase):
                self.setPixmap(toQIcon(img).pixmap(QSize(100, 100)))

    def _download(self):
        """下载网络图片"""
        import os
        import requests
        try:
            if os.path.exists(self.path):
                self.setPixmap(QPixmap(self.path))
                return
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            response = requests.get(self.url, stream=True, verify=False)
            with open(self.path, "wb") as f:
                for chunk in response.iter_content(8192):
                    if chunk:
                        f.write(chunk)
            self.setPixmap(QPixmap(self.path))
        except Exception:
            pass


# InfoBadge位置枚举
class NewInfoBadgePosition(Enum):
    CENTER = 7


@InfoBadgeManager.register(NewInfoBadgePosition.CENTER)
class CenterInfoBadgeManager(InfoBadgeManager):
    """居中位置的InfoBadge管理器"""

    def position(self):
        x = self.target.geometry().center().x() - self.badge.width() // 2
        y = self.target.geometry().center().y() - self.badge.height() // 2
        return QPoint(x, y)


# Flyout动画类型枚举
class NewFlyoutAnimationType(Enum):
    FADE_IN = 4
    NONE = 6


@FlyoutAnimationManager.register(NewFlyoutAnimationType.FADE_IN)
class FadeInFlyoutAnimationManager(FlyoutAnimationManager):
    """淡入动画管理器"""

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint(0, target.height()))
        x = pos.x() + target.width() // 2 - w.sizeHint().width() // 2
        y = pos.y() - w.layout().contentsMargins().top() + 8
        return QPoint(x, y)

    def exec(self, pos: QPoint):
        self.flyout.move(self._adjustPosition(pos))
        self.aniGroup.removeAnimation(self.slideAni)
        self.aniGroup.start()


@FlyoutAnimationManager.register(NewFlyoutAnimationType.NONE)
class DummyFlyoutAnimationManager(FlyoutAnimationManager):
    """无动画管理器"""

    def exec(self, pos: QPoint):
        self.flyout.move(self._adjustPosition(pos))

    def position(self, target: QWidget):
        w = self.flyout
        pos = target.mapToGlobal(QPoint(0, target.height()))
        x = pos.x() + target.width() // 2 - w.sizeHint().width() // 2
        y = pos.y() - w.layout().contentsMargins().top() + 8
        return QPoint(x, y)
