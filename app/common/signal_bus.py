# coding: utf-8
from PyQt5.QtCore import QObject, pyqtSignal
from qfluentwidgets import SettingCardGroup, ExpandSettingCard
from loguru import logger

class SignalBus(QObject):
    """ Signal bus """

    switchToSampleCard = pyqtSignal(str, int)
    switchToSettingGroup = pyqtSignal(SettingCardGroup)
    switchToExpandGroup = pyqtSignal(ExpandSettingCard)
    supportSignal = pyqtSignal()
    checkUpdateSig = pyqtSignal()
    micaEnableChanged = pyqtSignal(bool)

signalBus = SignalBus()