# coding:utf-8
import sys
from .setting import CONFIG_FILE, EXE_SUFFIX
from pathlib import Path
from enum import Enum

from PyQt5.QtCore import QLocale, QStandardPaths
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, __version__)


class Language(Enum):
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == 'win32' and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """ Config of application """

    # folders
    projectFolders   = ConfigItem("Folders", "LocalProject", [], FolderListValidator())
    downloadFolder = ConfigItem( "Folders", "Download", "app/download", FolderValidator())

    # main window
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem("MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem("MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # Material
    blurRadius  = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())

    # FastRte
    fastRteToolsEngine = OptionsConfigItem("FastRte", "FastRteToolsEngine", "L2 Func", OptionsValidator(["L2 Func", "Ipc Com", "Srp Com"]))
    fastRteOutputFolder = ConfigItem("FastRte", "FastRteOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),FolderValidator())
    fastRteMappingTableFolder = ConfigItem("FastRte", "FastRteMappingTableFolder", str(Path(f"tools/ffmpeg{EXE_SUFFIX}").absolute()))
    fastRteDataTypeFolder = ConfigItem("FastRte", "FastRteDataTypeFolder", str(Path(f"tools/ffmpeg{EXE_SUFFIX}").absolute()))
    fastRteInterfaceFolder = ConfigItem("FastRte", "FastRteInterfaceFolder", str(Path(f"tools/ffmpeg{EXE_SUFFIX}").absolute()))


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)