import sys
from enum import Enum

from PySide6.QtCore import QLocale, QStandardPaths
from qfluentwidgets import (
    BoolValidator,
    ColorConfigItem,
    ConfigItem,
    ConfigSerializer,
    FolderListValidator,
    FolderValidator,
    OptionsConfigItem,
    OptionsValidator,
    QConfig,
    RangeConfigItem,
    RangeValidator,
    Theme,
    qconfig,
)


class FileValidator:
    """File validator"""

    def validate(self, value):
        """
        Validate the value

        Args:
            value: value to validate

        Returns:
            bool: whether the value is valid
        """
        if not value:
            return True
        import os
        return os.path.isfile(value)

    def correct(self, value):
        """
        Correct the value

        Args:
            value: value to correct

        Returns:
            corrected value
        """
        return value

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
    """Language enumeration"""

    CHINESE_SIMPLIFIED = QLocale(QLocale.Chinese, QLocale.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Chinese, QLocale.HongKong)
    ENGLISH = QLocale(QLocale.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):
    """Language serializer"""

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    # 注册相关配置
    # register
    rememberMe = ConfigItem("Register", "RememberMe", True, BoolValidator())
    email = ConfigItem("Register", "Email", "")
    activationCode = ConfigItem("Register", "ActivationCode", "")

    # 项目文件夹配置
    projectFolders = ConfigItem("Project folders", "LocalProject", [], FolderListValidator())
    downloadFolder = ConfigItem("Project folders", "Download", "app/download", FolderValidator())

    # 个性化设置
    micaEnabled = ConfigItem("personalization", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem("personalization", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem("personalization", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # 背景设置
    backgroundImageEnabled = ConfigItem("Background", "ImageEnabled", False, BoolValidator())
    backgroundImagePath = ConfigItem("Background", "ImagePath", "")
    backgroundOpacity = RangeConfigItem("Background", "Opacity", 30, RangeValidator(0, 100))
    backgroundBlurRadius = RangeConfigItem("Background", "BlurRadius", 0, RangeValidator(0, 50))
    backgroundDisplayMode = OptionsConfigItem("Background", "DisplayMode", "Keep Aspect Ratio", OptionsValidator(["Stretch", "Keep Aspect Ratio", "Tile", "Original Size", "Fit Window"]))

    # 材质设置
    blurRadius = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # 应用设置
    beta = ConfigItem("Application", "beta", False, BoolValidator())
    close_window_action = OptionsConfigItem("Application", "close_window_action", "ask", OptionsValidator(["ask", "minimize", "close"]), restart=True)
    windowSizeMode = OptionsConfigItem("Application", "WindowSizeMode", "fixed", OptionsValidator(["fixed", "auto"]), restart=True)
    autoRun = ConfigItem("Application", "autoRun", False, BoolValidator())
    autoHide = ConfigItem("Application", "autoHide", False, BoolValidator())
    autoHideOnStartup = ConfigItem("Application", "AutoHideOnStartup", False, BoolValidator())

    # 软件更新设置
    checkUpdateAtStartUp = ConfigItem("software update", "CheckUpdateAtStartUp", True, BoolValidator())

    # 测试版设置
    debug_card = ConfigItem("Beta", "debug_card", False, BoolValidator(), restart=True)

    # FastRte 相关配置
    fastRteToolsEngine = OptionsConfigItem("FastRte", "FastRteToolsEngine", "L2 Func", OptionsValidator(["L2 Func", "Ipc Com", "Srp Com"]))
    fastRteOutputFolder = ConfigItem("FastRte", "FastRteOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    fastRteMappingTableFile = ConfigItem("FastRte", "FastRteMappingTableFile", "", FileValidator())
    fastRteDataTypeFile = ConfigItem("FastRte", "FastRteDataTypeFile", "", FileValidator())
    fastRteInterfaceFile = ConfigItem("FastRte", "FastRteInterfaceFile", "", FileValidator())

    # 日志设置
    logLevel = OptionsConfigItem("Log", "LogLevel", "DEBUG", OptionsValidator(["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]))
    logColorTraceLight = ColorConfigItem("Log", "LogColorTraceLight", "#9400D3")
    logColorDebugLight = ColorConfigItem("Log", "LogColorDebugLight", "#00BFFF")
    logColorInfoLight = ColorConfigItem("Log", "LogColorInfoLight", "#00FF7F")
    logColorSuccessLight = ColorConfigItem("Log", "LogColorSuccessLight", "#32CD32")
    logColorWarningLight = ColorConfigItem("Log", "LogColorWarningLight", "#FFD700")
    logColorErrorLight = ColorConfigItem("Log", "LogColorErrorLight", "#FF4500")
    logColorCriticalLight = ColorConfigItem("Log", "LogColorCriticalLight", "#FF1493")
    logColorTraceDark = ColorConfigItem("Log", "LogColorTraceDark", "#DDA0DD")
    logColorDebugDark = ColorConfigItem("Log", "LogColorDebugDark", "#87CEEB")
    logColorInfoDark = ColorConfigItem("Log", "LogColorInfoDark", "#98FB98")
    logColorSuccessDark = ColorConfigItem("Log", "LogColorSuccessDark", "#90EE90")
    logColorWarningDark = ColorConfigItem("Log", "LogColorWarningDark", "#FFFF00")
    logColorErrorDark = ColorConfigItem("Log", "LogColorErrorDark", "#FF6347")
    logColorCriticalDark = ColorConfigItem("Log", "LogColorCriticalDark", "#FF69B4")

    # 工具相关配置
    # RemoveComments 工具配置
    RmCommentsInputFolder = ConfigItem("ToolsPub", "RmCommentsInputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    RmCommentsOutputFolder = ConfigItem("ToolsPub", "RmCommentsOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    RmCommentsRemoveComments = ConfigItem("ToolsPub", "RmCommentsRemoveComments", True, BoolValidator())
    RmCommentsRemoveDocstrings = ConfigItem("ToolsPub", "RmCommentsRemoveDocstrings", True, BoolValidator())
    RmCommentsRemoveEmptyLines = ConfigItem("ToolsPub", "RmCommentsRemoveEmptyLines", True, BoolValidator())
    RmCommentsKeepTripleQuotes = ConfigItem("ToolsPub", "RmCommentsKeepTripleQuotes", False, BoolValidator())
    RmCommentsOutputSuffix = ConfigItem("ToolsPub", "RmCommentsOutputSuffix", "_clean.py")
    RmCommentsRecursive = ConfigItem("ToolsPub", "RmCommentsRecursive", False, BoolValidator())
    RmCommentsExcludeFiles = ConfigItem("ToolsPub", "RmCommentsExcludeFiles", "__init__.py,config.py")
    RmCommentsExcludePatterns = ConfigItem("ToolsPub", "RmCommentsExcludePatterns", "*_test.py,test_*.py")

    # QCraft Composition 工具配置
    QcCompositionInputFolder = ConfigItem("ToolsQc", "QcCompositionInputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    QcCompositionInputFile = ConfigItem("ToolsQc", "QcCompositionInputFile", "", FileValidator())
    QcCompositionSelectedOption = ConfigItem("ToolsQc", "QcCompositionSelectedOption", 0)
    QcCompositionCoreSettings = ConfigItem("ToolsQc", "QcCompositionCoreSettings", {})
    QcCompositionTableData = ConfigItem("ToolsQc", "QcCompositionTableData", [])

    # FastDem 工具配置
    FastDemInputFolder = ConfigItem("ToolsDem", "FastDemInputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    FastDemInputFile = ConfigItem("ToolsDem", "FastDemInputFile", "", FileValidator())
    FastDemSelectedOption = ConfigItem("ToolsDem", "FastDemSelectedOption", 0)

    # FastE2E 工具配置
    FastE2EInputFolder = ConfigItem("ToolsE2E", "FastE2EInputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    FastE2EInputFile = ConfigItem("ToolsE2E", "FastE2EInputFile", "", FileValidator())
    FastE2ESelectedOption = ConfigItem("ToolsE2E", "FastE2ESelectedOption", 0)
    FastE2EDirection = OptionsConfigItem("ToolsE2E", "FastE2EDirection", "Tx", OptionsValidator(["Tx", "Rx"]))

    # 浮窗配置
    # 基础设置
    startupDisplayFloatingWindow = ConfigItem("FloatingWindow", "StartupDisplay", True, BoolValidator())
    # 透明度设置
    floatingWindowOpacity = RangeConfigItem("FloatingWindow", "Opacity", 80, RangeValidator(0, 100))
    # 置顶模式
    floatingWindowTopmostMode = OptionsConfigItem("FloatingWindow", "TopmostMode", TopmostMode.NORMAL, OptionsValidator(TopmostMode), TopmostModeSerializer())
    # 可拖动
    floatingWindowDraggable = ConfigItem("FloatingWindow", "Draggable", True, BoolValidator())
    # 长按拖动时间
    floatingWindowLongPressDuration = RangeConfigItem("FloatingWindow", "LongPressDuration", 500, RangeValidator(50, 3000))
    # 无焦点模式
    doNotStealFocus = ConfigItem("FloatingWindow", "DoNotStealFocus", True, BoolValidator())
    # 外观设置
    floatingWindowButtonControl = OptionsConfigItem("FloatingWindow", "ButtonControl", 3, OptionsValidator([0, 1, 2, 3, 4, 5, 6, 7]))
    floatingWindowPlacement = OptionsConfigItem("FloatingWindow", "Placement", 1, OptionsValidator([0, 1, 2]))
    floatingWindowDisplayStyle = OptionsConfigItem("FloatingWindow", "DisplayStyle", 0, OptionsValidator([0, 1, 2]))
    floatingWindowSize = OptionsConfigItem("FloatingWindow", "Size", 3, OptionsValidator([0, 1, 2, 3, 4, 5, 6]))
    # 贴边设置
    floatingWindowStickToEdge = ConfigItem("FloatingWindow", "StickToEdge", True, BoolValidator())
    floatingWindowStickToEdgeRecoverSeconds = RangeConfigItem("FloatingWindow", "StickToEdgeRecoverSeconds", 3, RangeValidator(1, 10))
    floatingWindowStickToEdgeDisplayStyle = OptionsConfigItem("FloatingWindow", "StickToEdgeDisplayStyle", 1, OptionsValidator([0, 1, 2]))
    # 浮窗位置设置
    floatingWindowPosX = ConfigItem("FloatingWindow", "PosX", 100)
    floatingWindowPosY = ConfigItem("FloatingWindow", "PosY", 100)


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load(str(CONFIG_FILE.absolute()), cfg)