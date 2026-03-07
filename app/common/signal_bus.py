from PySide6.QtCore import QObject, Signal
from qfluentwidgets import ExpandSettingCard, SettingCardGroup


class SignalBus(QObject):
    """Signal bus"""

    switchToSampleCard = Signal(str, int)
    switchToSettingGroup = Signal(SettingCardGroup)
    switchToExpandGroup = Signal(ExpandSettingCard)
    supportSignal = Signal()
    checkUpdateSig = Signal()
    micaEnableChanged = Signal(bool)
    showMainWindow = Signal()  # 显示主窗口信号

    # ── AppInterface signals ──
    dataChanged = Signal()         # After any CRUD, triggers tree refresh
    workspaceSelected = Signal(str)  # workspace_id
    projectSelected = Signal(str)    # project_id


signalBus = SignalBus()
