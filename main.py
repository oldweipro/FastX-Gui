# coding:utf-8
import os
import sys
from loguru import logger

from PyQt5.QtCore import Qt, QUrl, QSize, QEventLoop, QTimer, QTranslator
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QSplashScreen
from qfluentwidgets import isDarkTheme, FluentTranslator
from app.view.main_window import MainWindow
from app.view.register_window import RegisterWindow
from app.common.config import cfg, Language

# Using global variables to prevent the interface from being destructed
mainWindow = None
def showMainWindow():
    global mainWindow
    try:
        mainWindow = MainWindow()
        mainWindow.show()
    except Exception as e:
        logger.error(e)

def main():
    # enable dpi scale
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))
    else:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)

    # internationalization
    locale = cfg.get(cfg.language).value
    translator = FluentTranslator(locale)
    galleryTranslator = QTranslator()
    galleryTranslator.load(locale, "app", ".", ":/app/i18n")

    app.installTranslator(translator)
    app.installTranslator(galleryTranslator)

    # create main window
    # w = RegisterWindow()
    # w.loginSignal.connect(showMainWindow)
    # w.show()
    showMainWindow()
    app.exec()

if __name__ == '__main__':
    main()
