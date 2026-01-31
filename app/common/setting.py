# coding: utf-8
from datetime import datetime
import sys
import platform
from pathlib import Path

# change DEBUG to False if you want to compile the code to exe
DEBUG = "__compiled__" not in globals()


# -------------------- 软件基本信息 --------------------
YEAR = 2026
INITIAL_AUTHORING_YEAR = 2026  # 软件发布年份
CURRENT_YEAR = datetime.now().year  # 软件当前年份
APPLY_NAME = "FastXGui"
CODENAME = "Q-FLUENT-WIDGETS-GUI-PLAN"            # 软件代号
AUTHOR = "wanqiang.liu"
COPYRIGHT_HOLDER = "FastXTeam"
VERSION = "v0.1.0"              # 软件当前版本
NEXT_VERSION = "v0.1.0-beta.1"  # 软件下一个版本
SPECIAL_VERSION = VERSION if VERSION != "v0.0.0" else NEXT_VERSION
HELP_URL = "https://qfluentwidgets.com"
REPO_URL = "https://github.com/fastxteam/FastX-Gui.git"
EXAMPLE_URL = "https://github.com/fastxteam/FastX-Gui.git"
FEEDBACK_URL = "https://github.com/fastxteam/FastX-Gui/issues"
RELEASE_URL = "https://github.com/fastxteam/FastX-Gui/releases/latest"
ZH_SUPPORT_URL = "https://github.com/fastxteam/FastX-Gui.git"
EN_SUPPORT_URL = "https://github.com/fastxteam/FastX-Gui.git"
BILIBILI_WEB = "https://github.com/fastxteam/FastX-Gui.git"
DONATION_URL = "https://afdian.com/a/fastxteam"  # 捐赠链接


def _detect_system() -> str:
    platform_key = sys.platform.lower()
    if platform_key.startswith(("win", "cygwin", "msys")):
        return "windows"
    if platform_key.startswith("darwin"):
        return "macos"
    if platform_key.startswith("linux"):
        return "linux"
    value = platform.system().lower()
    return value if value else "unknown"
def _normalize_arch(machine: str) -> str:
    machine = (machine or "").lower()
    arch_map = {
        "amd64": "x64",
        "x86_64": "x64",
        "x64": "x64",
        "i386": "x86",
        "i686": "x86",
        "arm64": "arm64",
        "aarch64": "arm64",
        "armv7l": "armv7",
        "armv7": "armv7",
        "armv6l": "armv6",
        "armv6": "armv6",
        "arm": "arm",
        "ppc64le": "ppc64le",
        "s390x": "s390x",
        "riscv64": "riscv64",
    }
    if machine in arch_map:
        return arch_map[machine]
    if "arm" in machine and "64" in machine:
        return "arm64"
    if "arm" in machine:
        return "arm"
    if not machine:
        return "x64" if sys.maxsize > 2**32 else "x86"
    return machine

ARCH = _normalize_arch(platform.machine())
SYSTEM = _detect_system()
STRUCT = (
    "exe"
    if SYSTEM == "windows"
    else "dmg"
    if SYSTEM == "macos"
    else "deb"
    if SYSTEM == "linux"
    else "tar"
)


CONFIG_FOLDER = Path('AppData').absolute()
CONFIG_FILE = CONFIG_FOLDER / "config.json"