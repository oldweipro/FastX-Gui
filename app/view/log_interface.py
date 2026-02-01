from collections import deque
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QSize
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor, QFont
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame
from loguru import logger
from qfluentwidgets import ScrollArea, StrongBodyLabel, CaptionLabel, PlainTextEdit, \
    FluentIcon as FIF, TransparentToolButton, TransparentToggleToolButton, SwitchButton, \
    VerticalSeparator, SearchLineEdit, ComboBox, PushButton, isDarkTheme, ToolButton, setTheme, Theme, ToggleToolButton

from app.common.icon import UnicodeIcon
from app.common.style_sheet import StyleSheet
from app.common.config import cfg

class LogLevel(Enum):
    """日志级别枚举"""
    TRACE = 0
    DEBUG = 1
    INFO = 2
    SUCCESS = 3
    WARNING = 4
    ERROR = 5
    CRITICAL = 6

class LogConfig:
    """日志配置管理类"""

    # 级别名称映射
    LEVEL_NAME_MAP = {
        LogLevel.TRACE: "TRACE",
        LogLevel.DEBUG: "DEBUG",
        LogLevel.INFO: "INFO",
        LogLevel.SUCCESS: "SUCCESS",
        LogLevel.WARNING: "WARNING",
        LogLevel.ERROR: "ERROR",
        LogLevel.CRITICAL: "CRITICAL"
    }

    # 反向级别映射
    NAME_LEVEL_MAP = {
        "TRACE": LogLevel.TRACE,
        "DEBUG": LogLevel.DEBUG,
        "INFO": LogLevel.INFO,
        "SUCCESS": LogLevel.SUCCESS,
        "WARNING": LogLevel.WARNING,
        "ERROR": LogLevel.ERROR,
        "CRITICAL": LogLevel.CRITICAL
    }

    # 级别配置
    LEVEL_CONFIG = {
        LogLevel.TRACE: {
            'name': '追踪',
            'icon': 'ic_fluent_number_circle_0_32_regular',
            'fif_icon': FIF.CODE,
            'bg_color': '#f3e6ff'
        },
        LogLevel.DEBUG: {
            'name': '调试',
            'icon': 'ic_fluent_bug_arrow_counterclockwise_20_regular',
            'fif_icon': FIF.CODE,
            'bg_color': '#e6f7ff'
        },
        LogLevel.INFO: {
            'name': '信息',
            'icon': 'ic_fluent_info_24_regular',
            'fif_icon': FIF.INFO,
            'bg_color': '#e6ffe6'
        },
        LogLevel.SUCCESS: {
            'name': '成功',
            'icon': 'ic_fluent_flash_checkmark_16_regular',
            'fif_icon': FIF.COMPLETED,
            'bg_color': '#e6ffe6'
        },
        LogLevel.WARNING: {
            'name': '警告',
            'icon': 'ic_fluent_warning_12_regular',
            'fif_icon': FIF.QUESTION,
            'bg_color': '#fff7e6'
        },
        LogLevel.ERROR: {
            'name': '错误',
            'icon': 'ic_fluent_warning_shield_20_regular',
            'fif_icon': FIF.CLOSE,
            'bg_color': '#ffe6e6'
        },
        LogLevel.CRITICAL: {
            'name': '严重',
            'icon': 'ic_fluent_share_screen_stop_24_regular',
            'fif_icon': FIF.EDUCATION,
            'bg_color': '#ffe6f0'
        }
    }

    @classmethod
    def get_level_name(cls, level):
        """获取级别的中文名称"""
        if isinstance(level, LogLevel):
            return cls.LEVEL_CONFIG.get(level, {}).get('name', '未知')
        return '未知'

    @classmethod
    def get_level_color(cls, level):
        """获取级别的颜色（字符串形式）"""
        if isinstance(level, LogLevel):
            if level == LogLevel.TRACE:
                return cfg.get(cfg.logColorTrace)
            elif level == LogLevel.DEBUG:
                return cfg.get(cfg.logColorDebug)
            elif level == LogLevel.INFO:
                return cfg.get(cfg.logColorInfo)
            elif level == LogLevel.SUCCESS:
                return cfg.get(cfg.logColorSuccess)
            elif level == LogLevel.WARNING:
                return cfg.get(cfg.logColorWarning)
            elif level == LogLevel.ERROR:
                return cfg.get(cfg.logColorError)
            elif level == LogLevel.CRITICAL:
                return cfg.get(cfg.logColorCritical)
        return '#FFFFFF'

    @classmethod
    def get_level_qcolor(cls, level):
        """获取级别的QColor对象"""
        color_str = cls.get_level_color(level)
        return QColor(color_str)

    @classmethod
    def get_level_icon(cls, level, use_unicode=True):
        """获取级别的图标

        Args:
            level: LogLevel枚举值
            use_unicode: 是否使用UnicodeIcon，否则使用FIF图标
        """
        if isinstance(level, LogLevel):
            config = cls.LEVEL_CONFIG.get(level, {})
            if use_unicode:
                icon_name = config.get('icon')
                if icon_name:
                    try:
                        return UnicodeIcon.get_icon_by_name(icon_name)
                    except Exception:
                        # 如果UnicodeIcon加载失败，回退到使用FIF图标
                        pass
            return config.get('fif_icon')
        return None

    @classmethod
    def get_level_bg_color(cls, level):
        """获取级别的背景颜色"""
        if isinstance(level, LogLevel):
            return cls.LEVEL_CONFIG.get(level, {}).get('bg_color', '#FFFFFF')
        return '#FFFFFF'

    @classmethod
    def get_level_by_name(cls, name):
        """通过名称获取LogLevel枚举值"""
        return cls.NAME_LEVEL_MAP.get(name.upper())

    @classmethod
    def get_name_by_level(cls, level):
        """通过LogLevel枚举值获取名称"""
        if isinstance(level, LogLevel):
            return cls.LEVEL_NAME_MAP.get(level, "INFO")
        return "INFO"

    @classmethod
    def get_all_levels(cls):
        """获取所有日志级别"""
        return list(LogLevel)

    @classmethod
    def get_colors_dict(cls):
        """获取所有级别的颜色字典"""
        return {
            cls.LEVEL_NAME_MAP[LogLevel.TRACE]: cls.get_level_qcolor(LogLevel.TRACE),
            cls.LEVEL_NAME_MAP[LogLevel.DEBUG]: cls.get_level_qcolor(LogLevel.DEBUG),
            cls.LEVEL_NAME_MAP[LogLevel.INFO]: cls.get_level_qcolor(LogLevel.INFO),
            cls.LEVEL_NAME_MAP[LogLevel.SUCCESS]: cls.get_level_qcolor(LogLevel.SUCCESS),
            cls.LEVEL_NAME_MAP[LogLevel.WARNING]: cls.get_level_qcolor(LogLevel.WARNING),
            cls.LEVEL_NAME_MAP[LogLevel.ERROR]: cls.get_level_qcolor(LogLevel.ERROR),
            cls.LEVEL_NAME_MAP[LogLevel.CRITICAL]: cls.get_level_qcolor(LogLevel.CRITICAL)
        }

    @classmethod
    def get_min_log_level(cls):
        """获取最小日志级别"""
        level_name = cfg.get(cfg.logLevel)
        return cls.get_level_by_name(level_name) or LogLevel.DEBUG

class QTextEditLogger(QObject):
    """线程安全的日志记录器，专为Qt应用设计（无空白行版）"""

    log_signal = pyqtSignal(str, str)  # (level, message)
    new_log_signal = pyqtSignal(str, str)  # (level, message) 用于通知LoguruInterface

    def __init__(self, text_edit, max_lines=1000):
        super().__init__()
        self.text_edit = text_edit
        self.buffer = deque(maxlen=max_lines)
        self.is_scrolling = True  # 跟踪用户是否手动滚动

        # 级别对应颜色
        self.colors = LogConfig.get_colors_dict()

        # 连接信号到安全处理槽
        self.log_signal.connect(self._safe_append_line, Qt.QueuedConnection)

        # 连接滚动条信号
        self.text_edit.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)

        # 监听日志配置变化
        cfg.logColorTrace.valueChanged.connect(self.update_colors)
        cfg.logColorDebug.valueChanged.connect(self.update_colors)
        cfg.logColorInfo.valueChanged.connect(self.update_colors)
        cfg.logColorSuccess.valueChanged.connect(self.update_colors)
        cfg.logColorWarning.valueChanged.connect(self.update_colors)
        cfg.logColorError.valueChanged.connect(self.update_colors)
        cfg.logColorCritical.valueChanged.connect(self.update_colors)

    def update_colors(self):
        """更新颜色配置"""
        self.colors = LogConfig.get_colors_dict()

    def write(self, message):
        """安全写入日志（可被任何线程调用）"""
        try:
            # 处理message对象或字符串
            if hasattr(message, 'record'):
                # 处理loguru的Message对象
                # 获取完整的格式化文本
                text = str(message).strip()
                level = message.record["level"].name
            else:
                # 处理字符串
                text = str(message).strip()
                if not text:
                    return

                # 提取日志级别
                level = "INFO"
                for lvl in self.colors:
                    if f"| {lvl} |" in text:
                        level = lvl
                        break

            # 缓存到内存
            self.buffer.append((level, text))

            # 直接调用安全处理方法
            self._safe_append_line(level, text)
        except Exception as e:
            logger.error(f"写入日志错误: {e}")

    def _on_scroll_value_changed(self, value):
        """当用户滚动时更新状态"""
        max_value = self.text_edit.verticalScrollBar().maximum()
        self.is_scrolling = (value >= max_value - 2)

    def _safe_text_cursor(self) -> QTextCursor:
        """安全获取文本游标"""
        if not self._is_widget_valid():
            return None
        try:
            return self.text_edit.textCursor()
        except RuntimeError:
            return None

    def _safe_append_line(self, level: str, line: str):
        """主线程执行的日志追加（正确处理换行和空白）"""
        # 1. 检查UI对象是否有效
        if not self._is_widget_valid():
            return

        # 2. 发送信号通知有新日志
        self.new_log_signal.emit(level, line)

        # 3. 清理底部空白（关键：在滚动前清理）
        self._clean_trailing_empty_lines()

        # 4. 滚动到底部（使用更可靠的方法）
        self._safe_scroll_to_bottom()

    def _clean_trailing_empty_lines(self):
        """清理文档末尾的额外空白行（只清理QPlainTextEdit自动添加的）"""
        if not self._is_widget_valid():
            return

        doc = self.text_edit.document()
        if not doc or doc.blockCount() <= 1:
            return

        # 保存当前滚动位置
        scroll_pos = self.text_edit.verticalScrollBar().value()
        max_scroll = self.text_edit.verticalScrollBar().maximum()

        # 如果当前在底部附近，标记为自动滚动
        at_bottom = (scroll_pos >= max_scroll - 2)

        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.End)

        # 检查最后一行是否为空（由QPlainTextEdit自动添加的）
        last_block = doc.lastBlock()
        if last_block.text().endswith("\n\n"):
            # 移除空行
            cursor.setPosition(last_block.position())
            cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # 删除段落结束符

        # 恢复滚动位置（如果之前在底部）
        if at_bottom:
            self.text_edit.verticalScrollBar().setValue(
                self.text_edit.verticalScrollBar().maximum()
            )

    def _safe_scroll_to_bottom(self):
        """安全滚动到底部（确保保留正常换行）"""
        if not self._is_widget_valid() or not self.is_scrolling:
            return

        try:
            # 方法1：直接滚动到文档末尾（最可靠）
            self.text_edit.verticalScrollBar().setValue(
                self.text_edit.verticalScrollBar().maximum()
            )
        except RuntimeError:
            pass

    def scroll_to_bottom(self, force=False):
        """
        滚动到底部（公共方法）
        :param force: 是否强制滚动（忽略 is_scrolling 状态）
        """
        if not self._is_widget_valid():
            return

        try:
            scroll_bar = self.text_edit.verticalScrollBar()
            if scroll_bar:
                if force:
                    # 强制滚动到底部
                    scroll_bar.setValue(scroll_bar.maximum())
                else:
                    # 只有在自动滚动模式下才滚动
                    if self.is_scrolling:
                        scroll_bar.setValue(scroll_bar.maximum())
        except RuntimeError:
            pass

    def _is_widget_valid(self) -> bool:
        """检查文本编辑控件是否有效"""
        if not hasattr(self, 'text_edit') or self.text_edit is None:
            return False
        try:
            self.text_edit.isVisible()
            return True
        except RuntimeError:
            return False

    def flush(self):
        """标准流接口"""
        pass

    def close(self):
        """安全关闭（清理资源）"""
        try:
            self.log_signal.disconnect()
            self.text_edit.verticalScrollBar().valueChanged.disconnect(self._on_scroll_value_changed)
        except:
            pass
        self.text_edit = None
        self.buffer.clear()

class LoguruInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.log_count = 0
        self.filter_level = None  # 当前过滤级别
        self.original_logs = []  # 保存原始日志内容

        self.log_viewer = PlainTextEdit(self)
        self.log_viewer.document().setDocumentMargin(0)
        self.log_viewer.setObjectName('log_viewer')
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFont(QFont("Consolas", 11))

        self.title_label = StrongBodyLabel(self.view)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.setObjectName('title_label')
        self.title_label.setText(self.tr("Log Center"))

        self.subtitle_label = CaptionLabel(self.view)
        self.subtitle_label.setTextColor("#666666")
        self.subtitle_label.setObjectName('subtitle_label')
        self.subtitle_label.setText(self.tr("Real-time system status monitoring"))


        """初始化界面"""
        self.__initWidget()
        self.__initLayout()
        self.create_tool_bar()  # 创建工具栏
        self.create_search_box()  # 创建搜索框
        self.setup_connections()
        StyleSheet.LOG_INTERFACE.apply(self)
        # 初始化完成后立即过滤并显示日志
        self.filter_logs()

    def __initLayout(self):
        # 顶层布局
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 48, 0, 0)
        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 0, 20, 20)
        self.main_layout.setSpacing(10)
        self.Layout.addLayout(self.main_layout)

        # 创建标题栏
        self.title_layout = QHBoxLayout()
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.addSpacing(10)
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addWidget(self.subtitle_label)
        self.title_layout.addStretch()

        self.main_layout.addLayout(self.title_layout)

    def __initWidget(self):
        self.setObjectName("loguruInterface")
        self.view.setObjectName('view')
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

    def create_tool_bar(self):
        """创建工具栏"""
        from qfluentwidgets import InfoBadge, InfoBadgePosition
        # 创建菜单栏
        self.toolbar = QHBoxLayout()
        self.toolbar.setSpacing(10)
        # 清空按钮
        self.clear_btn = ToolButton(FIF.DELETE, self)
        self.clear_btn.setToolTip(self.tr("Clear logs"))
        # 复制按钮
        self.copy_all_btn = ToolButton(FIF.COPY, self)
        self.copy_all_btn.setToolTip(self.tr("Copy all logs"))
        # 保存按钮
        self.save_all_btn = ToolButton(FIF.SAVE, self)
        self.save_all_btn.setToolTip(self.tr("Save all logs"))
        # 切换主题按钮
        self.themeButton = ToolButton(FIF.CONSTRACT, self)
        self.themeButton.setToolTip(self.tr("Switch theme"))
        # 设置按钮
        self.settingsButton = ToolButton(FIF.SETTING, self)
        self.settingsButton.setToolTip(self.tr("Log settings"))
        # 分隔符
        self.separator1 = VerticalSeparator()
        # 级别过滤按钮组
        self.filter_buttons = {}
        self.badge_labels = {}  # 用于存储每个级别的计数

        # 添加"所有日志"按钮
        self.all_logs_btn = ToggleToolButton(UnicodeIcon.get_icon_by_name('ic_fluent_channel_28_regular'))
        self.all_logs_btn.setToolTip(self.tr("Show all logs"))
        self.all_logs_btn.setFixedSize(36, 36)
        self.all_logs_btn.setProperty('level', -1)  # -1表示所有日志
        self.filter_buttons["ALL"] = self.all_logs_btn

        # 添加其他级别按钮
        for level in LogLevel:
            btn = ToggleToolButton()
            # 使用LogConfig获取图标
            icon = LogConfig.get_level_icon(level, use_unicode=True)
            btn.setIcon(icon)
            btn.setToolTip(self.tr(f"Show only {LogConfig.get_level_name(level)}"))
            btn.setFixedSize(36, 36)
            btn.setProperty('level', level.value)
            self.filter_buttons[level] = btn

        # 分隔符
        self.separator2 = VerticalSeparator()

        # 添加按钮到工具栏 - 左侧：清空、复制全部、保存全部、切换主题、设置、筛选按钮
        self.toolbar.addWidget(self.clear_btn)
        self.toolbar.addWidget(self.copy_all_btn)
        self.toolbar.addWidget(self.save_all_btn)
        self.toolbar.addWidget(self.themeButton)
        self.toolbar.addWidget(self.settingsButton)
        self.toolbar.addWidget(self.separator1)
        # 筛选按钮（靠左，跟分隔符挨着）
        self.toolbar.addWidget(self.all_logs_btn)
        for level in LogLevel:
            self.toolbar.addWidget(self.filter_buttons[level])
        self.toolbar.addStretch()
        self.main_layout.addLayout(self.toolbar)

        # 默认选中"所有日志"按钮
        self.all_logs_btn.setChecked(True)

    def create_search_box(self):
        """创建搜索框"""
        # 创建搜索栏
        self.search_layout = QHBoxLayout()
        self.search_layout.setSpacing(10)
        # 搜索框
        self.search_box = SearchLineEdit()
        self.search_box.setPlaceholderText(self.tr("Search log content..."))
        self.search_box.setFixedHeight(32)
        # 时间范围选择
        self.time_filter = ComboBox()
        self.time_filter.setFixedWidth(150)
        self.time_filter.addItems([self.tr("All time"), self.tr("Last 1 hour"), self.tr("Last 24 hours"), self.tr("Last 7 days")])
        self.search_layout.addWidget(self.search_box)
        self.search_layout.addWidget(self.time_filter)
        self.main_layout.addLayout(self.search_layout)

        # 直接添加日志查看器
        self.main_layout.addWidget(self.log_viewer)

    def setup_connections(self):
        """设置信号连接"""
        self.clear_btn.clicked.connect(self.clear_logs)
        self.copy_all_btn.clicked.connect(self.copy_all_logs)
        self.save_all_btn.clicked.connect(self.save_all_logs)
        self.themeButton.clicked.connect(self.toggle_theme)
        self.search_box.textChanged.connect(self.filter_logs)
        self.time_filter.currentTextChanged.connect(self.filter_logs)

        for btn in self.filter_buttons.values():
            btn.clicked.connect(self.on_filter_clicked)

        # 监听日志配置变化
        cfg.logColorTrace.valueChanged.connect(self.on_log_config_changed)
        cfg.logColorDebug.valueChanged.connect(self.on_log_config_changed)
        cfg.logColorInfo.valueChanged.connect(self.on_log_config_changed)
        cfg.logColorSuccess.valueChanged.connect(self.on_log_config_changed)
        cfg.logColorWarning.valueChanged.connect(self.on_log_config_changed)
        cfg.logColorError.valueChanged.connect(self.on_log_config_changed)
        cfg.logColorCritical.valueChanged.connect(self.on_log_config_changed)
        cfg.logLevel.valueChanged.connect(self.on_log_config_changed)

        # 确保"所有日志"按钮默认选中
        self.all_logs_btn.setChecked(True)

    def on_log_config_changed(self):
        """处理日志配置变化"""
        # 重新过滤日志，以应用新的配置
        self.filter_logs()

    def on_new_log(self, level: str, line: str):
        """处理新日志"""
        # 保存到原始日志列表
        self.original_logs.append((level, line))
        # 更新日志计数
        self.log_count += 1
        # 立即过滤并显示日志
        self.filter_logs()

    def clear_logs(self):
        """清空所有日志"""
        self.log_viewer.clear()
        # 清空原始日志列表
        self.original_logs.clear()
        # 重置统计
        if hasattr(self, 'badge_labels'):
            delattr(self, 'badge_labels')
        # 重置日志计数
        self.log_count = 0

    def filter_logs(self):
        """过滤日志"""
        try:
            # 获取搜索关键词和时间范围
            search_text = self.search_box.text().lower()
            time_filter = self.time_filter.currentText()

            # 清空当前显示
            self.log_viewer.clear()

            # 检查original_logs是否为空
            if not self.original_logs:
                return

            # 过滤并显示日志
            filtered_count = 0
            for level, text in self.original_logs:
                # 检查搜索关键词
                if search_text and search_text not in text.lower():
                    continue

                # 检查级别过滤
                if self.filter_level:
                    # 使用LogConfig获取级别名称
                    target_level = LogConfig.get_name_by_level(self.filter_level)
                    if target_level != level:
                        continue

                # 显示过滤后的日志（使用带有颜色格式化的方式）
                color = LogConfig.get_colors_dict().get(level, QColor("#FFFFFF"))
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                cursor = QTextCursor(self.log_viewer.document())
                cursor.movePosition(QTextCursor.End)
                cursor.insertText(text + "\n", fmt)
                filtered_count += 1
            # 滚动到底部
            self.log_viewer.verticalScrollBar().setValue(self.log_viewer.verticalScrollBar().maximum())

        except Exception as e:
            # 防止筛选功能崩溃
            logger.error(f"Filter function error: {e}")

    def on_filter_clicked(self):
        """处理过滤器点击"""
        try:
            sender = self.sender()

            # 确保筛选按钮是互斥的（单选逻辑）
            for btn in self.filter_buttons.values():
                if btn != sender:
                    btn.setChecked(False)

            if sender.isChecked():
                level_value = sender.property('level')
                if isinstance(level_value, int):
                    if level_value == -1:
                        # 所有日志
                        self.filter_level = None
                    else:
                        # 特定级别日志
                        try:
                            self.filter_level = LogLevel(level_value)
                        except ValueError:
                            # 如果level_value不在LogLevel的范围内，设置为None
                            self.filter_level = None
                else:
                    self.filter_level = None
            else:
                # 如果取消选中，默认显示所有日志
                self.filter_level = None
                self.all_logs_btn.setChecked(True)

            self.filter_logs()
        except Exception as e:
            # 防止筛选功能崩溃
            logger.error(f"Filter function error: {e}")
            self.filter_level = None
            self.filter_logs()

    def export_logs(self):
        """导出日志"""
        # 实现导出逻辑
        pass

    def copy_all_logs(self):
        """复制全部日志"""
        try:
            import PyQt5.QtWidgets as QtWidgets
            text = self.log_viewer.toPlainText()
            if text:
                QtWidgets.QApplication.clipboard().setText(text)
        except Exception as e:
            logger.error(f"复制全部日志错误: {e}")

    def save_all_logs(self):
        """保存全部日志"""
        try:
            import PyQt5.QtWidgets as QtWidgets
            import datetime

            # 获取当前时间作为文件名的一部分
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs_{current_time}.txt"

            # 打开文件保存对话框
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                self.tr("Save logs"),
                filename,
                self.tr("Text files (*.txt);;All files (*)")
            )

            if file_path:
                # 写入日志内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_viewer.toPlainText())
        except Exception as e:
            logger.error(f"Save all logs error: {e}")

    def toggle_theme(self):
        """切换应用主题"""
        # 切换当前主题
        current_theme = Theme.DARK if isDarkTheme() else Theme.LIGHT
        new_theme = Theme.LIGHT if current_theme == Theme.DARK else Theme.DARK
        setTheme(new_theme)

    def cleanup(self):
        """清理资源"""
        # 实现清理逻辑
        pass

    def showEvent(self, event):
        """界面显示事件"""
        # 刷新日志
        self.filter_logs()
        # 调用父类的 showEvent 方法
        super().showEvent(event)