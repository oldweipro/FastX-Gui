# coding: utf-8
from enum import Enum
import json
from typing import Dict, Optional
from qfluentwidgets import FluentIconBase, getIconColor, Theme, FluentFontIconBase
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QFile, QIODevice
from loguru import logger

class UnicodeIcon:
    """图标管理器类

    提供基于图标名称的图标获取功能，支持缓存机制
    底层使用 Fluent System Icons 字体图标
    """
    # 图标配置
    DEFAULT_ICON_CODEPOINT = 62634  # 默认图标码点(info图标)
    FONT_PATH = ":/app/images/unicodeIcon/FluentSystemIcons-Regular.ttf"
    ICON_MAP_PATH = ":/app/images/unicodeIcon/FluentSystemIcons-Regular.json"

    # 缓存
    _icon_cache: Dict[str, QIcon] = {}
    _icon_map_cache: Optional[Dict[str, int]] = None

    class FluentSystemIcon(FluentFontIconBase):
        """Fluent System Icons 字体图标类"""

        def __init__(self, char: str):
            """初始化字体图标

            Args:
                char: 图标字符
            """
            super().__init__(char)

        def path(self, theme=Theme.AUTO) -> str:
            """返回字体文件路径（Qt 资源路径）"""
            return UnicodeIcon.FONT_PATH

    @classmethod
    def _get_icon_map(cls) -> Dict[str, int]:
        """获取图标映射表，使用缓存避免重复读取JSON

        Returns:
            Dict[str, int]: 图标名称到码点的映射表
        """
        if cls._icon_map_cache is None:
            try:
                file = QFile(cls.ICON_MAP_PATH)
                if file.exists():
                    if file.open(QIODevice.ReadOnly | QIODevice.Text):
                        content = str(file.readAll(), encoding="utf-8")
                        file.close()
                        if not content or not content.strip():
                            logger.warning(f"图标映射表文件为空: {cls.ICON_MAP_PATH}")
                            cls._icon_map_cache = {}
                        else:
                            cls._icon_map_cache = json.loads(content)
                    else:
                        logger.error(f"无法打开图标映射表文件: {cls.ICON_MAP_PATH}")
                        cls._icon_map_cache = {}
                else:
                    logger.warning(f"图标映射表文件不存在: {cls.ICON_MAP_PATH}")
                    cls._icon_map_cache = {}
            except Exception as e:
                logger.exception(f"加载图标映射表失败: {e}")
                cls._icon_map_cache = {}
        return cls._icon_map_cache

    @classmethod
    def _create_icon_from_name(cls, icon_name) -> Optional[QIcon]:
        """根据图标名称或码点创建图标

        Args:
            icon_name: 图标名称或码点

        Returns:
            Optional[QIcon]: 创建的图标对象，失败则返回 None
        """
        if isinstance(icon_name, str) and not icon_name.startswith("\\u"):
            icon_map = cls._get_icon_map()
            if icon_name in icon_map:
                code_point = icon_map[icon_name]
                char = chr(code_point)
                return cls.FluentSystemIcon(char)
            else:
                raise ValueError(f"图标名称 '{icon_name}' 未在图标映射表中找到")
        else:
            char = cls._convert_icon_name_to_char(icon_name)
            return cls.FluentSystemIcon(char)

    @classmethod
    def _get_default_icon(cls, icon_name) -> QIcon:
        """获取默认图标

        Args:
            icon_name: 原始图标名称（用于缓存）

        Returns:
            QIcon: 默认图标对象
        """
        try:
            default_char = chr(cls.DEFAULT_ICON_CODEPOINT)
            default_icon = cls.FluentSystemIcon(default_char)
            cls._icon_cache[icon_name] = default_icon
            return default_icon
        except Exception as default_error:
            logger.exception(f"加载默认图标也失败: {default_error}")
            return QIcon()

    @classmethod
    def _convert_icon_name_to_char(cls, icon_name) -> str:
        """将图标名称或码点转换为字符

        Args:
            icon_name: 图标名称或码点

        Returns:
            str: 图标字符
        """
        if isinstance(icon_name, str) and icon_name.startswith("\\u"):
            code_point = int(icon_name[2:], 16)
            return chr(code_point)
        elif isinstance(icon_name, int):
            return chr(icon_name)
        else:
            return icon_name

    @classmethod
    def get_icon_by_name(cls, icon_name: str) -> QIcon:
        """根据图标名称获取 QIcon

        Args:
            icon_name: 图标名称（如 "ic_fluent_settings_20_filled"）

        Returns:
            QIcon: 图标对象

        Example:
            from app.common.xicon import UnicodeIcon
            icon = UnicodeIcon.get_icon_by_name("ic_fluent_settings_20_filled")
        """
        if icon_name in cls._icon_cache:
            return cls._icon_cache[icon_name]

        try:
            icon = cls._create_icon_from_name(icon_name)
            if icon:
                cls._icon_cache[icon_name] = icon
            return icon
        except Exception as e:
            logger.exception(f"加载图标{icon_name}出错: {e}")
            return cls._get_default_icon(icon_name)


class Icon(FluentIconBase, Enum):

    SELECT = "Select"
    SETTINGS = "Settings"
    SETTINGS_FILLED = "SettingsFilled"
    CLOUD_DOWNLOAD = "CloudDownload"
    CLOUD_DOWNLOAD_FILLED = "CloudDownloadFilled"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/icons/{self.value}_{getIconColor(theme)}.svg"


class Ico(FluentIconBase, Enum):

    M3U8DL = "M3U8DL"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/icos/{self.value}.ico"


class PNG(FluentIconBase, Enum):

    SHAKA_PACKAGER = "ShakaPackager"
    STEP_1 = "1"
    STEP_2 = "2"
    STEP_3 = "3"

    def path(self, theme=Theme.AUTO):
        return f":/app/images/png/{self.value}.png"


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
