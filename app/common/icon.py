import json
from enum import Enum

from loguru import logger
from PySide6.QtCore import QFile, QIODevice, QSize
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    FluentFontIconBase,
    FluentIconBase,
    Theme,
    getIconColor,
)


class UIcon:
    """Fluent System Icons 图标管理器 (Resizable版本)

    简化的API，支持通过名称快速获取图标
    """

    # 使用 Resizable 字体（支持任意大小缩放）
    FONT_PATH = ":/app/images/unicodeIcon/FluentSystemIcons-Resizable.ttf"
    ICON_MAP_PATH = ":/app/images/unicodeIcon/FluentSystemIcons-Resizable.json"
    DEFAULT_CODEPOINT = 57344  # 默认图标 (access_time_20_filled)

    _cache: dict[str, QIcon] = {}
    _map: dict[str, int] | None = None

    class _Icon(FluentFontIconBase):
        def __init__(self, char: str):
            super().__init__(char)

        def path(self, theme=Theme.AUTO) -> str:
            return UIcon.FONT_PATH

    @classmethod
    def _load_map(cls) -> dict[str, int]:
        if cls._map is None:
            try:
                file = QFile(cls.ICON_MAP_PATH)
                if file.exists() and file.open(QIODevice.ReadOnly | QIODevice.Text):
                    cls._map = json.loads(str(file.readAll(), encoding="utf-8"))
                    file.close()
                else:
                    cls._map = {}
            except Exception as e:
                logger.error(f"加载图标映射失败: {e}")
                cls._map = {}
        return cls._map

    @classmethod
    def get(cls, name: str, size: int = None) -> QIcon:
        """通过图标名称获取图标

        Args:
            name: 图标名称，如 "settings_20_filled"
                 或完整名称 "ic_fluent_settings_20_filled"
            size: 图标显示尺寸（像素），如 24, 32, 48
                  为 None 时返回原始图标，需自行 setIconSize

        Returns:
            QIcon: 图标对象

        Examples:
            # 只获取图标，自行设置大小
            icon = UIcon.get("settings_20_filled")
            btn.setIcon(icon)
            btn.setIconSize(QSize(32, 32))

            # 直接获取指定尺寸的图标（自动缩放）
            icon = UIcon.get("settings", size=32)
            btn.setIcon(icon)  # 已经是 32x32
        """
        cache_key = f"{name}_{size}" if size else name
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        try:
            icon_map = cls._load_map()
            # 支持简写和完整名称
            key = name if name in icon_map else f"ic_fluent_{name}"

            if key in icon_map:
                char = chr(icon_map[key])
                icon = cls._Icon(char)
                
                # 如果需要特定尺寸，创建缩放后的图标
                if size and size > 0:
                    icon = cls._scale_icon(icon, size)
                
                cls._cache[cache_key] = icon
                return icon
            else:
                logger.warning(f"图标未找到: {name}")
                return cls._default(name)
        except Exception as e:
            logger.error(f"加载图标失败 {name}: {e}")
            return cls._default(name)

    @classmethod
    def _scale_icon(cls, icon: QIcon, size: int) -> QIcon:
        """缩放图标到指定尺寸"""
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import Qt
        
        pixmap = icon.pixmap(QSize(size, size))
        scaled_pixmap = pixmap.scaled(QSize(size, size), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        scaled_icon = QIcon(scaled_pixmap)
        return scaled_icon


    @classmethod
    def _default(cls, name: str) -> QIcon:
        """返回默认图标"""
        if "_default" not in cls._cache:
            cls._cache["_default"] = cls._Icon(chr(cls.DEFAULT_CODEPOINT))
        return cls._cache["_default"]

    @classmethod
    def clear_cache(cls):
        """清除图标缓存"""
        cls._cache.clear()

class FIcon(FluentIconBase, Enum):
    # 基础图标
    APP_STORE = "app_store_regular"
    APP_TORE_FILLED = "app_store_filled"
    LOGS = "logs_regular"
    COFFEE = "coffee"
    INTERFACE = "interface"
    LIST = "list"
    PLUGIN = "tab-plugin"
    TASK = "task"
    DEMO = "demo"
    EXCHANGE_1 = "exchange-1"
    EXCHANGE_2 = "exchange-2"
    EXCHANGE_3 = "exchange-3"
    EXCHANGE_4 = "exchange-4"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/fluentIcon/{self.value}_{getIconColor(theme)}.svg"


class Icon(FluentIconBase, Enum):
    # FM
    WORKSPACE = "workspace"
    WORKSPACE_ADD = "workspace-add"
    PROJECT = "project"
    TEMPLATE = "template"
    ITEM = "item"
    ITEM1 = "items-1"
    ITEM2 = "items-2"
    ITEM3 = "items-3"
    ITEM4 = "items-4"
    SNAPSHOT = "snapshot"
    COLLAPSE = "collapse"
    COLLAPSE_ALL = "collapse-all"
    COLLAPSE_L = "collapse-l"
    COLLAPSE_R = "collapse-r"
    COLLAPSE_UP = "collapse-up"

    # 基础图标
    SELECT = "Select"
    SETTINGS = "Settings"
    SETTINGS_FILLED = "SettingsFilled"
    CLOUD_DOWNLOAD = "CloudDownload"
    CLOUD_DOWNLOAD_FILLED = "CloudDownloadFilled"
    
    # 文件类型图标
    EDIT_FILE = "EditFile"
    CODE_FILE = "CodeFile"
    TEXT_FILE = "TextFile"
    GIF_FILE = "GifFile"
    JPG_FILE = "JpgFile"
    WORD_FILE = "WordFile"
    ZIP_FILE = "ZipFile"
    MUSIC_FILE = "MusicFile"
    DATA_FILE = "DataFile"
    EXCEL = "Excel"
    PDF_FILE = "PdfFile"
    PPT_FILE = "PptFile"
    TXT_FILE = "TxtFile"
    
    # 方向图标
    UP = "Up"
    GO_START = "GoStart"
    DOWN = "Down"
    GO_END = "GoEnd"
    RIGHT = "Right"
    LEFT = "Left"
    DOUBLE_UP = "DoubleUp"
    DOUBLE_DOWN = "DoubleDown"
    DOUBLE_RIGHT = "DoubleRight"
    DOUBLE_LEFT = "DoubleLeft"
    TO_BOTTOM = "ToBottom"
    TO_TOP = "ToTop"
    
    # 汽车品牌图标
    BYD = "BYD"
    VW = "VW"
    DONGFENG_NISSAN = "DongfengNissan"
    GAC_HONDA = "GAC_Honda"
    GAC_TRUMPCHI = "GAC_Trumpchi"
    HUAWEI = "Huawei"
    LI_AUTO = "LiAuto"
    LEAP_MOTOR = "LeapMotor"
    SAIC = "SAIC"
    AITO = "AITO"
    X_PENG = "XPeng"
    GEELY = "Geely"
    AUDI = "Audi"
    BOSCH = "Bosch"
    BENZ = "Benz"
    TESLA = "Tesla"
    TESLA1 = "Tesla1"
    ZHIJI = "Zhiji"
    
    # 电池和MCU图标
    BATTERY = "Battery"
    MCU = "MCU"
    MCU1 = "MCU1"
    MCU2 = "MCU2"
    
    # 技术文件类型图标
    DCM = "DCM"
    ARXML = "ARXML"
    ARXML1 = "ARXML1"
    CH = "CH"
    H = "H"
    INI = "INI"
    A2L = "A2L"
    ADS = "ADS"
    ARXML_BOX = "ARXML_Box"
    ARXML_BOX1 = "ARXML_Box1"
    BSW = "BSW"
    BSW1 = "BSW1"
    BUILD = "BUILD"
    CAN = "CAN"
    CCP = "CCP"
    CCP1 = "CCP1"
    CDD = "CDD"
    CODE = "CODE"
    COM = "COM"
    COM1 = "COM1"
    CRC = "CRC"
    DBC = "DBC"
    DCM_BOX = "DCM_Box"
    DCM_BOX1 = "DCM_Box1"
    DCM_BOX2 = "DCM_Box2"
    DCM_BOX3 = "DCM_Box3"
    DEM1 = "DEM1"
    DEM2 = "DEM2"
    DOIP = "DOIP"
    E2E = "E2E"
    ETAS = "ETAS"
    FIM = "FIM"
    FUNC = "FUNC"
    FUN = "FUN"
    IMU = "IMU"
    IPC = "IPC"
    ISOLAR = "ISOLAR"
    J6M = "J6M"
    LIB = "LIB"
    LIN = "LIN"
    MCAL = "MCAL"
    MCU_BOX = "MCU_Box"
    NVM = "NVM"
    PMIC = "PMIC"
    RTE = "RTE"
    RX = "Rx"
    SDB = "SDB"
    SDB1 = "SDB1"
    SDK = "SDK"
    SOC = "SOC"
    SOMEIP_6 = "SOMEIP_6"
    SOMEIP_5 = "SOMEIP_5"
    SWC = "SWC"
    TX = "Tx"
    USS = "USS"
    XCP = "XCP"
    XML = "XML"
    XML_IN = "XML_In"
    RX_SIMPLE = "Rx_Simple"
    SDB_SIMPLE = "SDB_Simple"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/icons/{self.value}_{getIconColor(theme)}.svg"


class Ico(FluentIconBase, Enum):
    M3U8DL = "M3U8DL"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/icos/{self.value}.ico"


class PNG(FluentIconBase, Enum):
    SHAKA_PACKAGER = "ShakaPackager"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/png/{self.value}.png"


class JPG(FluentIconBase, Enum):
    BACKGROUND_1 = "background"
    BACKGROUND_2 = "background2"
    SPONSOR_WX = "sponsor"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/jpg/{self.value}.jpg"


class Logo(FluentIconBase, Enum):
    KEY = "Key"
    GEAR = "Gear"
    FILM = "Film"
    MOON = "Moon"
    KNOT = "Knot"
    LINK = "Link"
    GLOBE = "Globe"
    WHALE = "Whale"
    LABEL = "Label"
    BROOM = "Broom"
    TIMER = "Timer"
    INBOX = "Inbox"
    BENTO = "Bento"
    PIZZA = "Pizza"
    LEDGER = "Ledger"
    POSTAL = "Postal"
    PLANET = "Planet"
    SHIELD = "Shield"
    COOKIE = "Cookie"
    HAMMER = "Hammer"
    OFFICE = "Office"
    PENCIL = "Pencil"
    PUZZLE = "Puzzle"
    FFMPEG = "FFmpeg"
    MONKEY = "Monkey"
    FOLDER = "Folder"
    ROCKET = "Rocket"
    SCROLL = "Scroll"
    WINDOW = "Window"
    CONTROL = "Control"
    CYCLONE = "Cyclone"
    ALEMBIC = "Alembic"
    BANDAGE = "Bandage"
    PACKAGE = "Package"
    SYRINGE = "Syringe"
    UNLOCKED = "Unlocked"
    AIRPLANE = "Airplane"
    CALENDAR = "Calendar"
    BOOKMARK = "Bookmark"
    TERMINAL = "Terminal"
    JOYSTICK = "Joystick"
    BAR_CHART = "BarChart"
    SMILEFACE = "Smileface"
    HOURGLASS = "Hourglass"
    PROJECTOR = "Projector"
    WASTEBASKET = "Wastebasket"
    VIDEO_CAMERA = "VideoCamera"
    CARD_FILE_BOX = "CardFileBox"
    VIDEOCASSETTE = "Videocassette"

    def path(self, theme=Theme.AUTO) -> str:
        return f":/app/images/logo/{self.value}.svg"
