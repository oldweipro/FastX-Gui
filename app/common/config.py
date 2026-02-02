# coding:utf-8
import sys
from pathlib import Path
from enum import Enum

from PyQt5.QtCore import QLocale, QStandardPaths
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, Theme, FolderValidator, ConfigSerializer, __version__,
                            ColorConfigItem)

from .setting import CONFIG_FILE

class TopmostMode(Enum):
    """置顶模式枚举"""
    DISABLED = 0
    NORMAL = 1
    UIA = 2

class TopmostModeSerializer(ConfigSerializer):
    """置顶模式序列化器"""
    def serialize(self, mode):
        return mode.value
    def deserialize(self, value):
        return TopmostMode(value)

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
    windowSizeMode = OptionsConfigItem("Application", "WindowSizeMode", "fixed", OptionsValidator(["fixed", "auto"]), restart=True)
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

    # Log
    logLevel = OptionsConfigItem("Log", "LogLevel", "DEBUG", OptionsValidator(["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]))
    logColorTrace = ColorConfigItem("Log", "LogColorTrace", "#9400D3")
    logColorDebug = ColorConfigItem("Log", "LogColorDebug", "#00BFFF")
    logColorInfo = ColorConfigItem("Log", "LogColorInfo", "#00FF7F")
    logColorSuccess = ColorConfigItem("Log", "LogColorSuccess", "#32CD32")
    logColorWarning = ColorConfigItem("Log", "LogColorWarning", "#FFD700")
    logColorError = ColorConfigItem("Log", "LogColorError", "#FF4500")
    logColorCritical = ColorConfigItem("Log", "LogColorCritical", "#FF1493")

    # Tools/Pub/RemoveComments
    RmCommentsInputFolder = ConfigItem("ToolsPub", "RmCommentsInputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),FolderValidator())
    RmCommentsOutputFolder = ConfigItem("ToolsPub", "RmCommentsOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation),FolderValidator())


    """浮窗配置类"""

    # 基础设置
    startupDisplayFloatingWindow = ConfigItem(
        "FloatingWindow", "StartupDisplay", True, BoolValidator()
    )

    # 透明度设置 (0-100)
    floatingWindowOpacity = RangeConfigItem(
        "FloatingWindow", "Opacity", 80, RangeValidator(0, 100)
    )

    # 置顶模式
    floatingWindowTopmostMode = OptionsConfigItem(
        "FloatingWindow",
        "TopmostMode",
        TopmostMode.NORMAL,
        OptionsValidator(TopmostMode),
        TopmostModeSerializer()
    )

    # 可拖动
    floatingWindowDraggable = ConfigItem(
        "FloatingWindow", "Draggable", True, BoolValidator()
    )

    # 长按拖动时间 (毫秒)
    floatingWindowLongPressDuration = RangeConfigItem(
        "FloatingWindow", "LongPressDuration", 500, RangeValidator(50, 3000)
    )

    # 无焦点模式
    doNotStealFocus = ConfigItem(
        "FloatingWindow", "DoNotStealFocus", True, BoolValidator()
    )

    # 外观设置
    floatingWindowButtonControl = OptionsConfigItem(
        "FloatingWindow",
        "ButtonControl",
        3,
        OptionsValidator([0, 1, 2, 3, 4, 5, 6, 7])
    )

    floatingWindowPlacement = OptionsConfigItem(
        "FloatingWindow",
        "Placement",
        1,
        OptionsValidator([0, 1, 2])
    )

    floatingWindowDisplayStyle = OptionsConfigItem(
        "FloatingWindow",
        "DisplayStyle",
        0,
        OptionsValidator([0, 1, 2])
    )

    floatingWindowSize = OptionsConfigItem(
        "FloatingWindow",
        "Size",
        3,
        OptionsValidator([0, 1, 2, 3, 4, 5, 6])
    )

    # 贴边设置
    floatingWindowStickToEdge = ConfigItem(
        "FloatingWindow", "StickToEdge", True, BoolValidator()
    )

    floatingWindowStickToEdgeRecoverSeconds = RangeConfigItem(
        "FloatingWindow", "StickToEdgeRecoverSeconds", 3, RangeValidator(1, 10)
    )

    floatingWindowStickToEdgeDisplayStyle = OptionsConfigItem(
        "FloatingWindow",
        "StickToEdgeDisplayStyle",
        1,
        OptionsValidator([0, 1, 2])
    )

    # 浮窗位置设置
    floatingWindowPosX = ConfigItem(
        "FloatingWindow", "PosX", 100
    )

    floatingWindowPosY = ConfigItem(
        "FloatingWindow", "PosY", 100
    )

cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load(str(CONFIG_FILE.absolute()), cfg)