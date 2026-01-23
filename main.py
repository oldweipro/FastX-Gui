# coding:utf-8
import os
import sys
from inspect import getsourcefile
from pathlib import Path

from PyQt5.QtCore import Qt, QUrl, QSize, QEventLoop, QTimer, QTranslator
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QSplashScreen

from qfluentwidgets import isDarkTheme, FluentTranslator

from app.view.main_window import MainWindow
from app.view.register_window import RegisterWindow
from app.common.config import cfg, Language

# Using global variables to prevent the interface from being destructed
mainWindow = None
def showMainWindow():
    global mainWindow
    mainWindow = MainWindow()
    mainWindow.show()

if __name__ == '__main__':
    os.chdir(Path(getsourcefile(lambda: 0)).resolve().parent)

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    # internationalization
    locale = cfg.get(cfg.language).value
    fluentTranslator = FluentTranslator(locale)
    galleryTranslator = QTranslator()
    galleryTranslator.load(locale, "app", ".", ":/app/i18n")

    app.installTranslator(fluentTranslator)
    app.installTranslator(galleryTranslator)

    w = RegisterWindow()
    w.loginSignal.connect(showMainWindow)
    w.show()

    app.exec()
