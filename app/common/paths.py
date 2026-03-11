"""
FastX-Gui 统一路径配置
======================

所有用户数据文件统一存储在用户目录下的 .fastxgui 文件夹中。

目录结构：
~/.fastxgui/
├── config.json           # 应用配置
├── fastx.db              # 数据库文件
├── .license.dat          # 授权信息
├── .time_anchor.dat      # 时间锚点
├── .admin.dat            # 管理员数据
├── .audit.dat            # 审计日志
├── logs/                 # 日志目录
├── cache/                # 缓存目录
└── exports/              # 导出文件目录
"""

import sys
from pathlib import Path
from typing import Optional


class AppPaths:
    """应用程序路径配置类"""
    
    # ==================== 核心路径 ====================
    
    # 用户数据根目录 (~/.fastxgui)
    USER_DATA_DIR: Path = Path.home() / ".fastxgui"
    
    # 应用根目录（项目目录）
    APP_ROOT: Path = Path(__file__).parent.parent.parent
    
    # ==================== 配置文件 ====================
    
    # 主配置文件
    CONFIG_FILE: Path = USER_DATA_DIR / "config.json"
    
    # ==================== 数据库 ====================
    
    # 数据库文件
    DATABASE_FILE: Path = USER_DATA_DIR / "fastx.db"
    
    # 数据库连接字符串
    @classmethod
    @property
    def DATABASE_URL(cls) -> str:
        return f"sqlite:///{cls.DATABASE_FILE}"
    
    # ==================== 授权相关 ====================
    
    # 授权信息文件
    LICENSE_FILE: Path = USER_DATA_DIR / ".license.dat"
    
    # 时间锚点文件
    TIME_ANCHOR_FILE: Path = USER_DATA_DIR / ".time_anchor.dat"
    
    # 管理员数据文件
    ADMIN_DATA_FILE: Path = USER_DATA_DIR / ".admin.dat"
    
    # 审计日志文件
    AUDIT_LOG_FILE: Path = USER_DATA_DIR / ".audit.dat"
    
    # ==================== 日志目录 ====================
    
    # 日志目录
    LOG_DIR: Path = USER_DATA_DIR / "logs"
    
    # ==================== 缓存目录 ====================
    
    # 缓存目录
    CACHE_DIR: Path = USER_DATA_DIR / "cache"
    
    # 背景图片缓存
    BACKGROUND_CACHE_DIR: Path = CACHE_DIR / "backgrounds"
    
    # ==================== 导出目录 ====================
    
    # 导出文件默认目录
    EXPORT_DIR: Path = USER_DATA_DIR / "exports"
    
    # ==================== 资源目录（只读） ====================
    
    # 资源目录（项目内）
    RESOURCE_DIR: Path = APP_ROOT / "app" / "resource"
    
    # 图片资源
    IMAGES_DIR: Path = RESOURCE_DIR / "images"
    
    # 样式表
    STYLES_DIR: Path = RESOURCE_DIR / "qss"
    
    # 翻译文件
    I18N_DIR: Path = RESOURCE_DIR / "i18n"
    
    # ==================== 插件目录 ====================
    
    # 插件目录
    PLUGINS_DIR: Path = APP_ROOT / "app" / "plugins"
    
    # ==================== 方法 ====================
    
    @classmethod
    def ensure_directories(cls) -> None:
        """确保所有必要的目录都存在"""
        directories = [
            cls.USER_DATA_DIR,
            cls.LOG_DIR,
            cls.CACHE_DIR,
            cls.BACKGROUND_CACHE_DIR,
            cls.EXPORT_DIR,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Windows 平台设置隐藏属性
        if sys.platform == "win32":
            try:
                import subprocess
                subprocess.run(
                    ["attrib", "+H", str(cls.USER_DATA_DIR)],
                    check=False, capture_output=True, timeout=5
                )
            except Exception:
                pass
    
    @classmethod
    def get_user_data_dir(cls) -> Path:
        """获取用户数据目录"""
        return cls.USER_DATA_DIR
    
    @classmethod
    def get_config_file(cls) -> Path:
        """获取配置文件路径"""
        return cls.CONFIG_FILE
    
    @classmethod
    def get_database_file(cls) -> Path:
        """获取数据库文件路径"""
        return cls.DATABASE_FILE
    
    @classmethod
    def reset_to_default(cls) -> None:
        """重置所有路径为默认值（用于测试）"""
        cls.USER_DATA_DIR = Path.home() / ".fastxgui"
        cls.CONFIG_FILE = cls.USER_DATA_DIR / "config.json"
        cls.DATABASE_FILE = cls.USER_DATA_DIR / "fastx.db"
        cls.LICENSE_FILE = cls.USER_DATA_DIR / ".license.dat"
        cls.TIME_ANCHOR_FILE = cls.USER_DATA_DIR / ".time_anchor.dat"
        cls.ADMIN_DATA_FILE = cls.USER_DATA_DIR / ".admin.dat"
        cls.AUDIT_LOG_FILE = cls.USER_DATA_DIR / ".audit.dat"


# 便捷访问
PATHS = AppPaths


def get_user_data_dir() -> Path:
    """获取用户数据目录"""
    return AppPaths.USER_DATA_DIR


def ensure_data_dir() -> Path:
    """确保数据目录存在并返回路径"""
    AppPaths.ensure_directories()
    return AppPaths.USER_DATA_DIR
