# coding: utf-8
import sys
from pathlib import Path
from PyQt5.QtCore import QStandardPaths

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


YEAR = 2026
AUTHOR = "wanqiang.liu"
VERSION = "v0.1.0"
HELP_URL = "https://qfluentwidgets.com"
REPO_URL = "https://github.com/fastxteam/FastX-Gui.git"
EXAMPLE_URL = "https://github.com/fastxteam/FastX-Gui.git"
FEEDBACK_URL = "https://github.com/fastxteam/FastX-Gui/issues"
RELEASE_URL = "https://github.com/fastxteam/FastX-Gui/releases/latest"
ZH_SUPPORT_URL = "https://github.com/fastxteam/FastX-Gui.git"
EN_SUPPORT_URL = "https://github.com/fastxteam/FastX-Gui.git"

CONFIG_FOLDER = Path('AppData').absolute()
CONFIG_FILE = CONFIG_FOLDER / "config.json"