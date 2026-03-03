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
    rememberMe = ConfigItem("Register", "RememberMe", True, BoolValidator())
    email = ConfigItem("Register", "Email", "")
    activationCode = ConfigItem("Register", "ActivationCode", "")

    # 项目文件夹配置
    projectFolders = ConfigItem("Project", "Folders", [], FolderListValidator())
    downloadFolder = ConfigItem("Project", "DownloadFolder", "app/download", FolderValidator())

    # 个性化设置
    micaEnabled = ConfigItem("Personalization", "MicaEnabled", isWin11(), BoolValidator())
    dpiScale = OptionsConfigItem("Personalization", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem("Personalization", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # 背景设置
    backgroundImageEnabled = ConfigItem("Background", "ImageEnabled", False, BoolValidator())
    backgroundImagePath = ConfigItem("Background", "ImagePath", "")
    backgroundOpacity = RangeConfigItem("Background", "Opacity", 30, RangeValidator(0, 100))
    backgroundBlurRadius = RangeConfigItem("Background", "BlurRadius", 0, RangeValidator(0, 50))
    backgroundDisplayMode = OptionsConfigItem("Background", "DisplayMode", "Keep Aspect Ratio", OptionsValidator(["Stretch", "Keep Aspect Ratio", "Tile", "Original Size", "Fit Window"]))

    # 材质设置
    blurRadius = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # 应用设置
    beta = ConfigItem("Application", "Beta", False, BoolValidator())
    closeWindowAction = OptionsConfigItem("Application", "CloseWindowAction", "ask", OptionsValidator(["ask", "minimize", "close"]), restart=True)
    windowSizeMode = OptionsConfigItem("Application", "WindowSizeMode", "fixed", OptionsValidator(["fixed", "auto"]), restart=True)
    autoRun = ConfigItem("Application", "AutoRun", False, BoolValidator())
    autoHide = ConfigItem("Application", "AutoHide", False, BoolValidator())
    autoHideOnStartup = ConfigItem("Application", "AutoHideOnStartup", False, BoolValidator())

    # 软件更新设置
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())

    # 测试版设置
    debugCard = ConfigItem("Beta", "DebugCard", False, BoolValidator(), restart=True)

    # FastRte 相关配置
    fastRteToolsEngine = OptionsConfigItem("FastRte", "ToolsEngine", "L2 Func", OptionsValidator(["L2 Func", "Ipc Com", "Srp Com"]))
    fastRteOutputFolder = ConfigItem("FastRte", "OutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    fastRteMappingTableFile = ConfigItem("FastRte", "MappingTableFile", "", FileValidator())
    fastRteDataTypeFile = ConfigItem("FastRte", "DataTypeFile", "", FileValidator())
    fastRteInterfaceFile = ConfigItem("FastRte", "InterfaceFile", "", FileValidator())

    # 日志设置
    logLevel = OptionsConfigItem("Log", "Level", "DEBUG", OptionsValidator(["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]))
    logColorTraceLight = ColorConfigItem("Log", "ColorTraceLight", "#9400D3")
    logColorDebugLight = ColorConfigItem("Log", "ColorDebugLight", "#00BFFF")
    logColorInfoLight = ColorConfigItem("Log", "ColorInfoLight", "#00FF7F")
    logColorSuccessLight = ColorConfigItem("Log", "ColorSuccessLight", "#32CD32")
    logColorWarningLight = ColorConfigItem("Log", "ColorWarningLight", "#FFD700")
    logColorErrorLight = ColorConfigItem("Log", "ColorErrorLight", "#FF4500")
    logColorCriticalLight = ColorConfigItem("Log", "ColorCriticalLight", "#FF1493")
    logColorTraceDark = ColorConfigItem("Log", "ColorTraceDark", "#DDA0DD")
    logColorDebugDark = ColorConfigItem("Log", "ColorDebugDark", "#87CEEB")
    logColorInfoDark = ColorConfigItem("Log", "ColorInfoDark", "#98FB98")
    logColorSuccessDark = ColorConfigItem("Log", "ColorSuccessDark", "#90EE90")
    logColorWarningDark = ColorConfigItem("Log", "ColorWarningDark", "#FFFF00")
    logColorErrorDark = ColorConfigItem("Log", "ColorErrorDark", "#FF6347")
    logColorCriticalDark = ColorConfigItem("Log", "ColorCriticalDark", "#FF69B4")

    # 工具相关配置
    # RemoveComments 工具配置
    rmCommentsInputFolder = ConfigItem("Tools", "RmCommentsInputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    rmCommentsOutputFolder = ConfigItem("Tools", "RmCommentsOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    rmCommentsRemoveComments = ConfigItem("Tools", "RmCommentsRemoveComments", True, BoolValidator())
    rmCommentsRemoveDocstrings = ConfigItem("Tools", "RmCommentsRemoveDocstrings", True, BoolValidator())
    rmCommentsRemoveEmptyLines = ConfigItem("Tools", "RmCommentsRemoveEmptyLines", True, BoolValidator())
    rmCommentsKeepTripleQuotes = ConfigItem("Tools", "RmCommentsKeepTripleQuotes", False, BoolValidator())
    rmCommentsOutputSuffix = ConfigItem("Tools", "RmCommentsOutputSuffix", "_clean.py")
    rmCommentsRecursive = ConfigItem("Tools", "RmCommentsRecursive", False, BoolValidator())
    rmCommentsExcludeFiles = ConfigItem("Tools", "RmCommentsExcludeFiles", "__init__.py,config.py")
    rmCommentsExcludePatterns = ConfigItem("Tools", "RmCommentsExcludePatterns", "*_test.py,test_*.py")

    # QCraft Composition 工具配置
    qcCompositionInputFile = ConfigItem("Tools", "QcCompositionInputFile", "", FileValidator())
    qcCompositionOutputFolder = ConfigItem("Tools", "QcCompositionOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    qcCompositionSelectedOption = ConfigItem("Tools", "QcCompositionSelectedOption", 0)
    qcCompositionCoreSettings = ConfigItem("Tools", "QcCompositionCoreSettings", {})
    qcCompositionTableData = ConfigItem("Tools", "QcCompositionTableData", [])

    # FastDem 工具配置
    fastDemInputFile = ConfigItem("Tools", "FastDemInputFile", "", FileValidator())
    fastDemOutputFolder = ConfigItem("Tools", "FastDemOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    fastDemSelectedOption = ConfigItem("Tools", "FastDemSelectedOption", 0)

    # FastE2E 工具配置
    fastE2EInputFile = ConfigItem("Tools", "FastE2EInputFile", "", FileValidator())
    fastE2EOutputFolder = ConfigItem("Tools", "FastE2EOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    fastE2ESelectedOption = ConfigItem("Tools", "FastE2ESelectedOption", 0)
    fastE2EDirection = OptionsConfigItem("Tools", "FastE2EDirection", "Tx", OptionsValidator(["Tx", "Rx"]))

    # FastCCP 工具配置
    fastCCPInputFile = ConfigItem("Tools", "FastCCPInputFile", "", FileValidator())
    fastCCPOutputFolder = ConfigItem("Tools", "FastCCPOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    fastCCPSelectedOption = ConfigItem("Tools", "FastCCPSelectedOption", 0)

    # FastFaultManager 工具配置
    fastFaultManagerInputFile = ConfigItem("Tools", "FastFaultManagerInputFile", "", FileValidator())
    fastFaultManagerOutputFolder = ConfigItem("Tools", "FastFaultManagerOutputFolder", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation), FolderValidator())
    fastFaultManagerSelectedOption = ConfigItem("Tools", "FastFaultManagerSelectedOption", 0)

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