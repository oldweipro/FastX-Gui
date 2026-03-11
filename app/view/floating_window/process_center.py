"""
ProgressCenter - 任务中心
简洁的任务管理组件，支持普通任务和下载任务
"""

import time
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    FlyoutViewBase, StrongBodyLabel, BodyLabel, ToolButton, FluentIcon as FIF, 
    CardWidget, CaptionLabel, InfoBadge
)

from app.common.web import download_file
from app.common.utils import startFile as start_file, showFile as show_file
from app.common.icon import UIcon
from app.components.common_widgets import (
    BetterScrollArea, CardGroup, CustomProgressBar, WebImage,
    NewInfoBadgePosition, NewFlyoutAnimationType
)

THREAD_POOL = ThreadPoolExecutor(max_workers=4)


class TaskCard(CardWidget):
    """任务卡片 - 支持进度显示和控制"""
    
    startSignal = Signal()
    pauseSignal = Signal()
    resumeSignal = Signal()
    finishSignal = Signal(bool)
    cancelSignal = Signal()

    def __init__(
        self,
        parent=None,
        progress_center=None,
        card_group: CardGroup = None,
        indeterminate: bool = True,
        can_pause: bool = True,
    ):
        super().__init__(parent)
        
        self.stat = "init"  # init, running, paused, finished, cancelled
        self.wid = str(self)
        self.indeterminate = indeterminate
        self.cardGroup = card_group
        self.progressCenter = progress_center
        self.can_pause = can_pause
        
        self.setFixedWidth(372)
        self.setFixedHeight(56)
        
        # UI
        self.titleLabel = BodyLabel(self)
        self.titleLabel.setSelectable()
        
        self.contentLabel = CaptionLabel(self)
        self.contentLabel.setTextColor("#606060", "#d2d2d2")
        self.contentLabel.setAlignment(Qt.AlignLeft)
        
        self.startButton = ToolButton(FIF.PLAY, self)
        self.pauseButton = ToolButton(FIF.PAUSE, self)
        self.resumeButton = ToolButton(FIF.PAUSE_BOLD, self)
        self.stopButton = ToolButton(FIF.CLOSE, self)
        
        self.startButton.clicked.connect(self.start)
        self.pauseButton.clicked.connect(self.pause)
        self.resumeButton.clicked.connect(self.resume)
        self.stopButton.clicked.connect(self.stop)
        
        self.pauseButton.hide()
        self.resumeButton.hide()
        self.stopButton.hide()
        
        self.progressBar = CustomProgressBar(self, useAni=False, indeterminate=indeterminate)
        self.progressLabel = BodyLabel("0%", self)
        self.progressLabel.setTextColor("#606060", "#d2d2d2")
        self.progressLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.progressLabel.setHidden(indeterminate)
        
        # Layout
        centerLayout = QVBoxLayout()
        centerLayout.setSpacing(6)
        centerLayout.addWidget(self.contentLabel)
        
        progressLayout = QHBoxLayout()
        progressLayout.setSpacing(8)
        progressLayout.addWidget(self.progressBar)
        progressLayout.addWidget(self.progressLabel, 0)
        centerLayout.addLayout(progressLayout)
        
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(16, 11, 11, 11)
        self.hBoxLayout.setSpacing(6)
        self.hBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignVCenter)
        self.hBoxLayout.addLayout(centerLayout, 1)
        self.hBoxLayout.addStretch(0)
        self.hBoxLayout.addWidget(self.startButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.pauseButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.resumeButton, 0, Qt.AlignRight)
        self.hBoxLayout.addWidget(self.stopButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(8)

    def start(self):
        self.stat = "running"
        self.startButton.hide()
        if self.can_pause:
            self.pauseButton.show()
        self.stopButton.show()
        self.startSignal.emit()

    def pause(self):
        self.stat = "paused"
        self.pauseButton.hide()
        self.resumeButton.show()
        self.pauseSignal.emit()

    def resume(self):
        self.stat = "running"
        self.resumeButton.hide()
        self.pauseButton.show()
        self.resumeSignal.emit()

    def finish(self, success: bool = True):
        self.stat = "finished"
        self.startButton.hide()
        self.pauseButton.hide()
        self.resumeButton.hide()
        self.stopButton.show()
        if success:
            self.setValue(100)
        self.finishSignal.emit(success)

    def cancel(self):
        self.stat = "cancelled"
        self.startButton.hide()
        self.pauseButton.hide()
        self.resumeButton.hide()
        self.stopButton.show()
        self.setValue(0)
        self.cancelSignal.emit()

    def stop(self):
        if self.stat in ["finished", "cancelled"]:
            self.cardGroup.removeCard(self.wid)
            self.progressCenter.count()
        else:
            self.cancel()

    def setTitle(self, text: str):
        self.titleLabel.setText(text)

    def setContent(self, text: str):
        self.contentLabel.setText(text)

    def setValue(self, val: int):
        self.progressBar.setValue(int(val))
        self.progressLabel.setText(f"{int(val)}%")

    def setIndeterminate(self, flag: bool):
        self.indeterminate = flag
        self.progressBar.setIndeterminate(flag)
        self.progressLabel.setHidden(flag)


class DownloadTaskCard(TaskCard):
    """下载任务卡片"""
    downloadFinishedSignal = Signal(bool, str)

    def __init__(
        self,
        parent=None,
        progress_center=None,
        card_group: CardGroup = None,
        url: str = None,
        path: str = None,
    ):
        super().__init__(parent, progress_center, card_group, False, True)
        self.url = url
        self.path = path
        self._cancelled = False
        self._paused = False
        
        self.setTitle(self.tr("Download"))
        self.setContent(self.tr("Downloading..."))
        self.setToolTip(f"链接：{self.url}\n保存至：{self.path}")
        
        self.openFileButton = ToolButton(FIF.PLAY, self)
        self.openFileButton.setToolTip(self.tr("Open File"))
        self.openFileButton.hide()
        self.hBoxLayout.insertWidget(5, self.openFileButton, Qt.AlignRight)
        
        self.showFileButton = ToolButton(FIF.FOLDER, self)
        self.showFileButton.setToolTip(self.tr("Open File Location"))
        self.showFileButton.hide()
        self.hBoxLayout.insertWidget(6, self.showFileButton, Qt.AlignRight)
        
        self.startSignal.connect(self._start_download)
        self.pauseSignal.connect(self._pause_download)
        self.resumeSignal.connect(self._resume_download)
        self.cancelSignal.connect(self._cancel_download)
        self.downloadFinishedSignal.connect(self._on_download_finished)
        
        self.start()

    def _start_download(self):
        THREAD_POOL.submit(self._download_worker)

    def _download_worker(self):
        result = download_file(self.url, self.path, self._progress_callback, self._is_cancelled)
        if result:
            self.setContent(self.tr("Download completed!"))
            self.finish(True)
            self.downloadFinishedSignal.emit(True, result)
        else:
            self.setContent(self.tr("Download failed!"))
            self.finish(False)
            self.downloadFinishedSignal.emit(False, "")

    def _progress_callback(self, progress: int):
        self.setValue(progress)

    def _is_cancelled(self) -> bool:
        while self._paused:
            time.sleep(0.1)
        return self._cancelled

    def _pause_download(self):
        self._paused = True

    def _resume_download(self):
        self._paused = False

    def _cancel_download(self):
        self._cancelled = True

    def _on_download_finished(self, success: bool, path: str):
        if success and path:
            self.openFileButton.clicked.connect(lambda: start_file(path))
            self.openFileButton.show()
            self.showFileButton.clicked.connect(lambda: show_file(path))
            self.showFileButton.show()


class ProgressCenter(FlyoutViewBase):
    """任务中心 - 管理所有任务卡片"""
    
    def __init__(self, window=None):
        super().__init__()
        self.window = window
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        self.vBoxLayout.setSpacing(8)
        self.vBoxLayout.setContentsMargins(14, 12, 14, 8)
        
        # Title
        titleLayout = QHBoxLayout()
        self.titleLabel = StrongBodyLabel(self.tr("Task Center"), self)
        self.emptyLabel = BodyLabel(self.tr("No tasks currently"), self)
        self.emptyLabel.setTextColor("#909090", "#707070")
        self.emptyLabel.setAlignment(Qt.AlignCenter)
        
        self.clearButton = ToolButton(FIF.BROOM, self)
        self.clearButton.setToolTip(self.tr("Clear Completed Tasks"))
        self.clearButton.setFixedSize(28, 28)
        self.clearButton.clicked.connect(self.clear)
        
        titleLayout.addWidget(self.titleLabel, 0)
        titleLayout.addWidget(self.clearButton, 0)
        
        # Scroll area
        self.scrollArea = BetterScrollArea(self)
        self.scrollArea.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea.vBoxLayout.setSpacing(0)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.hide()
        
        self.cardGroup = CardGroup(self, show_title=False)
        self.cardGroup.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollArea.vBoxLayout.addWidget(self.cardGroup, 1)
        
        self.vBoxLayout.addLayout(titleLayout)
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addWidget(self.emptyLabel, 1)
        
        self.setMinimumSize(400, 100)
        self.setMaximumSize(400, 500)
        
        self.infoBadge = None

    def clear(self):
        """清空已完成任务"""
        import copy
        for wid, widget in copy.copy(self.cardGroup._cardMap).items():
            if widget.stat in ["finished", "cancelled"]:
                self.cardGroup.removeCard(wid)
        self.count()

    def add_task(self, indeterminate: bool = True, can_pause: bool = True) -> TaskCard:
        """
        添加普通任务
        
        Args:
            indeterminate: 是否使用不确定进度条
            can_pause: 是否可以暂停
            
        Returns:
            TaskCard: 任务卡片实例
        """
        card = TaskCard(
            self.cardGroup,
            self,
            self.cardGroup,
            indeterminate,
            can_pause,
        )
        self.cardGroup.addCard(card, card.wid)
        self.count()
        return card

    def add_download_task(self, url: str, path: str) -> DownloadTaskCard:
        """
        添加下载任务
        
        Args:
            url: 下载链接
            path: 保存路径
            
        Returns:
            DownloadTaskCard: 下载任务卡片实例
        """
        card = DownloadTaskCard(self.cardGroup, self, self.cardGroup, url, path)
        self.cardGroup.addCard(card, card.wid)
        self.count()
        return card

    def count(self):
        """更新任务计数和UI状态"""
        count = self.cardGroup.count()
        
        if not self.infoBadge:
            self.infoBadge = InfoBadge.attension(
                count,
                self.window.titleBar,
                self.window.progressCenterButton,
                position=NewInfoBadgePosition.CENTER,
            )
        self.infoBadge.setText(str(count))
        self.infoBadge.setVisible(bool(count))
        
        self.emptyLabel.setHidden(bool(count))
        self.scrollArea.setVisible(bool(count))
        
        if count:
            self.window.progressCenterButton.setIcon(None)
        else:
            self.window.progressCenterButton.setIcon(UIcon.get('ic_fluent_list_20_regular'))
        
        self.cardGroup.adjustSize()
        self._adjust_size()

    def _adjust_size(self):
        """调整大小"""
        content_height = self.cardGroup.height()
        new_height = min(max(content_height + 60, 100), 500)
        self.setFixedHeight(new_height)
        if self.window.progressCenterFlyout:
            self.window.progressCenterFlyout.setFixedHeight(new_height)
