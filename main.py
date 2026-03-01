import os
import sys

from PySide6.QtCore import Qt, QTranslator
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.view.main_window import MainWindow

# Using global variables to prevent the interface from being destructed
mainWindow = None


def showMainWindow(hide=False):
    global mainWindow
    mainWindow = MainWindow()
    # Always show the window first to ensure it's properly initialized
    mainWindow.show()
    # Hide it if needed
    if hide:
        mainWindow.hide()


def main():
    # enable dpi scale
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))
    else:
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

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

    # Check if application was started with "startup" argument
    hide_window = False
    if len(sys.argv) > 1 and sys.argv[1] == "startup":
        # Check if autoHide is enabled
        if cfg.get(cfg.autoHide):
            hide_window = True

    # create main window
    # w = RegisterWindow()
    # w.loginSignal.connect(showMainWindow)
    # w.show()
    showMainWindow(hide=hide_window)

    app.exec()


if __name__ == "__main__":
    main()
