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

if sys.platform == "win32" and not DEBUG:
    CONFIG_FOLDER = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)) / APP_NAME


CONFIG_FILE = CONFIG_FOLDER / "config.json"
DB_PATH = CONFIG_FOLDER / "database.db"

COVER_FOLDER = CONFIG_FOLDER / "Cover"
COVER_FOLDER.mkdir(exist_ok=True, parents=True)

if sys.platform == "win32":
    EXE_SUFFIX = ".exe"
else:
    EXE_SUFFIX = ""
