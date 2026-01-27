# coding:utf-8
import sys
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
    # register
    rememberMe = ConfigItem("Register", "RememberMe", True)
    email = ConfigItem("Register", "Email", "")
    activationCode = ConfigItem("Register", "ActivationCode", "")

    # Settings/Project folders
    projectFolders   = ConfigItem("Project folders", "LocalProject", [], FolderListValidator())
    downloadFolder = ConfigItem( "Project folders", "Download", "app/download", FolderValidator())
    # Settings/personalization
    micaEnabled = ConfigItem("personalization", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem("personalization", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem("personalization", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)
    # Settings/background settings
    backgroundImageEnabled = ConfigItem("Background", "ImageEnabled", False, BoolValidator())
    backgroundImagePath = ConfigItem("Background", "ImagePath", "")
    backgroundOpacity = RangeConfigItem("Background", "Opacity", 30, RangeValidator(0, 100))
    backgroundBlurRadius = RangeConfigItem("Background", "BlurRadius", 0, RangeValidator(0, 50))
    backgroundDisplayMode = OptionsConfigItem(
        "Background", "DisplayMode", "Keep Aspect Ratio",
        OptionsValidator(["Stretch", "Keep Aspect Ratio", "Tile", "Original Size", "Fit Window"])
    )
    # Settings/Material
    blurRadius  = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))
    # Settings/Application
    beta = ConfigItem("Application", "beta", False, BoolValidator())
    close_window_action = OptionsConfigItem("Application", "close_window_action", 'ask', OptionsValidator(['ask', 'minimize', "close"]), restart=True)
    # Settings/software update
    checkUpdateAtStartUp = ConfigItem("software update", "CheckUpdateAtStartUp", True, BoolValidator())
    # Settings/Beta
    debug_card = ConfigItem("Beta", "debug_card", False, BoolValidator(), restart=True)

    # FastRte
    fastRteToolsEngine = OptionsConfigItem("FastRte", "FastRteToolsEngine", "L2 Func", OptionsValidator(["L2 Func", "Ipc Com", "Srp Com"]))
    fastRteOutputFolder = ConfigItem("FastRte", "FastRteOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),FolderValidator())
    fastRteMappingTableFolder = ConfigItem("FastRte", "FastRteMappingTableFolder", '')
    fastRteDataTypeFolder = ConfigItem("FastRte", "FastRteDataTypeFolder", '')
    fastRteInterfaceFolder = ConfigItem("FastRte", "FastRteInterfaceFolder", '')


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load('app/config/config.json', cfg)