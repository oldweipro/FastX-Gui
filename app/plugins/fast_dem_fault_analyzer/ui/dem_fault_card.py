"""DEM Fault Analyzer Card Widget - 使用 QFluentWidgets 实现的现代化 UI"""

from typing import Dict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLabel,
    QFrame,
    QScrollArea,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
    QApplication,
    QFileDialog,
)
from PySide6.QtGui import QPixmap, QPainter, QClipboard
from loguru import logger

# 配置模块级 logger
logger = logger.bind(module="DEMFaultAnalyzer")
from qfluentwidgets import (
    CardWidget,
    TitleLabel,
    BodyLabel,
    StrongBodyLabel,
    LineEdit,
    PrimaryPushButton,
    InfoBar,
    InfoBarPosition,
    SmoothScrollArea,
    ToolTipFilter,
    FluentIcon as FIF,
    MessageBox,
)

from ..core.dem_fault_analyzer import DEMFaultAnalyzer, DTCStatusConfig


class BitStatusCard(CardWidget):
    """单个状态位卡片"""
    
    def __init__(self, bit_info, is_set, parent=None):
        super().__init__(parent)
        self.bit_info = bit_info
        self.is_set = is_set
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # 标题行
        title_layout = QHBoxLayout()
        
        # Bit 编号
        bit_label = StrongBodyLabel(f"Bit {self.bit_info.bit}", self)
        bit_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(bit_label)
        
        # 缩写
        abbr_label = BodyLabel(self.bit_info.abbr, self)
        abbr_label.setStyleSheet("color: #0078D4; font-weight: bold;")
        title_layout.addWidget(abbr_label)
        
        title_layout.addStretch()
        
        # 状态指示
        if self.is_set:
            status_label = QLabel("● SET", self)
            status_label.setStyleSheet("color: #FF4D4F; font-weight: bold; font-size: 14px;")
        else:
            status_label = QLabel("● CLR", self)
            status_label.setStyleSheet("color: #52C41A; font-weight: bold; font-size: 14px;")
        title_layout.addWidget(status_label)
        
        layout.addLayout(title_layout)
        
        # 名称
        name_label = BodyLabel(self.bit_info.name, self)
        name_label.setStyleSheet("font-style: italic; color: #666;")
        layout.addWidget(name_label)
        
        # 简介
        intro_label = BodyLabel(self.bit_info.intro, self)
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)
        
        # 分隔线
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(line)
        
        # 状态描述
        desc = self.bit_info.desc_true if self.is_set else self.bit_info.desc_false
        desc_label = BodyLabel(desc, self)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)


class DEMFaultCard(QWidget):
    """DEM 故障分析器主界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = DEMFaultAnalyzer()
        
        # 设置最小宽度
        self.setMinimumWidth(900)
        
        # 设置尺寸策略，允许扩展填充父容器
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        self.setObjectName("DEMFaultCard")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)
        
        # ========== 第一部分：头部描述 + 输入区（独立卡片） ==========
        input_card = CardWidget(self)
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)
        
        # 标题和副标题
        title = TitleLabel("DEM 故障分析器", self)
        input_layout.addWidget(title)
        
        subtitle = BodyLabel("基于 AUTOSAR CP DEM 的 DTC 故障状态分析工具", self)
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        input_layout.addWidget(subtitle)
        
        # 分隔线
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #E0E0E0;")
        input_layout.addWidget(line)
        
        # 输入区域
        input_label = StrongBodyLabel("请输入 DTC 状态码:", self)
        input_layout.addWidget(input_label)
        
        self.input_edit = LineEdit(self)
        self.input_edit.setPlaceholderText("格式：0x6C 或 6C")
        self.input_edit.setMinimumHeight(36)
        input_layout.addWidget(self.input_edit)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        analyze_btn = PrimaryPushButton("分析", self)
        analyze_btn.setIcon(FIF.SEARCH)
        analyze_btn.setMinimumHeight(36)
        analyze_btn.installEventFilter(ToolTipFilter(analyze_btn))
        analyze_btn.setToolTip("点击分析 DTC 状态码")
        btn_layout.addWidget(analyze_btn)
        
        export_btn = PrimaryPushButton("导出图片", self)
        export_btn.setIcon(FIF.SHARE)
        export_btn.setMinimumHeight(36)
        export_btn.installEventFilter(ToolTipFilter(export_btn))
        export_btn.setToolTip("导出当前分析结果为图片")
        btn_layout.addWidget(export_btn)
        
        input_layout.addLayout(btn_layout)
        
        main_layout.addWidget(input_card)
        
        # ========== 第二部分：状态位分布卡片 ==========
        self.bits_card = CardWidget(self)
        bits_layout = QVBoxLayout(self.bits_card)
        bits_layout.setContentsMargins(16, 12, 16, 12)
        bits_layout.setSpacing(16)
        
        self.bits_title = StrongBodyLabel("状态位分布", self)
        bits_layout.addWidget(self.bits_title)
        
        # 网格布局显示 8 个状态位
        self.bits_grid_layout = QGridLayout()
        self.bits_grid_layout.setSpacing(16)
        self.bits_grid_layout.setContentsMargins(8, 8, 8, 8)
        bits_layout.addLayout(self.bits_grid_layout)
        
        # 初始隐藏，分析后显示
        self.bits_card.setVisible(False)
        main_layout.addWidget(self.bits_card)
        
        # ========== 第三部分：详细解析卡片（可无限扩展） ==========
        self.detail_container = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(12)
        self.detail_layout.addStretch()
        
        main_layout.addWidget(self.detail_container, 1)
        
        # 初始提示
        self._show_initial_message()
    
    def _connect_signals(self):
        # 获取所有按钮
        buttons = self.findChildren(PrimaryPushButton)
        for btn in buttons:
            if btn.text() == "分析":
                btn.clicked.connect(self._on_analyze_clicked)
            elif btn.text() == "导出图片":
                btn.clicked.connect(self._on_export_clicked)
    
    def _show_initial_message(self):
        """显示初始提示信息"""
        self._clear_bits()
        self._clear_details()
        
        self.bits_card.setVisible(False)
        
        msg_label = BodyLabel("请输入 DTC 状态码（格式：0x6C 或 6C），然后点击分析按钮", self.detail_container)
        msg_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
        msg_label.setAlignment(Qt.AlignCenter)
        self.detail_layout.insertWidget(self.detail_layout.count() - 1, msg_label)
    
    def _clear_result(self):
        """清空结果区域（已废弃，保留用于兼容）"""
        self._clear_bits()
        self._clear_details()
    
    def _on_analyze_clicked(self):
        """点击分析按钮"""
        status_input = self.input_edit.text().strip()
        
        if not status_input:
            logger.warning("分析输入为空")
            InfoBar.warning(
                title="输入为空",
                content="请输入 DTC 状态码",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return
        
        # 执行分析
        result = self.analyzer.analyze_dtc_status(status_input)
        
        if not result['success']:
            logger.error(f"分析失败：{result.get('error', '未知错误')}")
            InfoBar.error(
                title="分析失败",
                content=result.get('error', '未知错误'),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
        
        # 显示分析结果
        try:
            self._display_analysis_result(result)
            logger.info(f"DTC 状态码 {status_input} 分析完成")
        except Exception as e:
            logger.exception(f"显示分析结果时发生异常：{e}")
            return
        
        InfoBar.success(
            title="分析完成",
            content=f"DTC 状态码 {status_input} 分析完成",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )
    
    def _on_export_clicked(self):
        """点击导出按钮"""
        # 检查是否有分析结果
        if not self.bits_card.isVisible():
            logger.warning("尝试导出但未找到分析结果")
            InfoBar.warning(
                title="没有可导出的内容",
                content="请先进行分析操作",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return
        
        try:
            self._export_to_clipboard()
            logger.info("分析结果已导出到剪贴板")
        except Exception as e:
            logger.exception(f"导出图片时发生异常：{e}")
    
    def _export_to_clipboard(self):
        """导出当前内容到剪贴板"""
        try:
            # 确保布局完成
            QApplication.processEvents()
            
            # 使用 QPixmap.grab() 方法（PySide6 推荐方式）
            pixmap = self.grab()
            
            if pixmap.isNull():
                logger.warning("grab() 返回空，使用备用渲染方案")
                # 备用方案：手动创建和渲染
                pixmap = QPixmap(self.size() * self.devicePixelRatio())
                pixmap.setDevicePixelRatio(self.devicePixelRatio())
                pixmap.fill(Qt.white)
                
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.TextAntialiasing)
                painter.setRenderHint(QPainter.SmoothPixmapTransform)
                
                self.render(pixmap, painter)
                painter.end()
            
            # 复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setImage(pixmap.toImage())
            
            logger.success(f"导出成功 - 图片尺寸：{pixmap.size().width()}x{pixmap.size().height()}")
            
            InfoBar.success(
                title="导出成功",
                content="已复制到剪贴板，可直接粘贴到其他应用",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            
            InfoBar.info(
                title="提示",
                content="使用 Ctrl+V 即可粘贴到微信、QQ、文档等应用",
                parent=self,
                position=InfoBarPosition.BOTTOM,
                duration=5000
            )
            
        except Exception as e:
            logger.exception(f"导出失败：{e}")
            InfoBar.error(
                title="导出失败",
                content=f"导出过程中发生错误：{str(e)}",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
    
    def _display_analysis_result(self, result: Dict):
        """显示分析结果"""
        # 清空所有卡片内容 - 防止重复分析时崩溃
        self._clear_bits()
        self._clear_details()
        
        basic_info = result['basic_info']
        logger.debug(f"分析结果：HEX={basic_info.get('hex')}, bits={len(basic_info.get('bits', []))}")
        
        # ========== 第二张卡片：状态位分布 ==========
        self.bits_card.setVisible(True)
        
        # 从高位到低位显示 (Bit7 到 Bit0)
        for i in range(8):
            bit = 7 - i
            is_set = basic_info['bits'][bit]
            bit_info = DTCStatusConfig.get_bit_info(bit)
            
            if bit_info:
                try:
                    bit_widget = self._create_bit_block(bit_info, is_set)
                    row = 0
                    col = i
                    self.bits_grid_layout.addWidget(bit_widget, row, col)
                except Exception as e:
                    logger.exception(f"添加 Bit {bit} 失败：{e}")
        
        # ========== 第三张卡片：详细解析（可无限扩展） ==========
        # 置位状态位详细解析
        if result['set_bits']:
            logger.debug(f"置位状态位数量：{len(result['set_bits'])}")
            set_title = StrongBodyLabel("置位状态位详细解析", self.detail_container)
            set_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 8px;")
            self.detail_layout.insertWidget(self.detail_layout.count() - 1, set_title)
            
            for idx, bit_analysis in enumerate(result['set_bits']):
                try:
                    bit_card = CardWidget(self.detail_container)
                    bit_layout = QVBoxLayout(bit_card)
                    bit_layout.setContentsMargins(16, 12, 16, 12)
                    bit_layout.setSpacing(8)
                    
                    # 标题行
                    title_layout = QHBoxLayout()
                    bit_label = StrongBodyLabel(f"Bit {bit_analysis['bit']}", self)
                    bit_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                    title_layout.addWidget(bit_label)
                    
                    abbr_label = BodyLabel(bit_analysis['abbr'], self)
                    abbr_label.setStyleSheet("color: #0078D4; font-weight: bold;")
                    title_layout.addWidget(abbr_label)
                    
                    title_layout.addStretch()
                    
                    status_label = QLabel("● SET", self)
                    status_label.setStyleSheet("color: #FF4D4F; font-weight: bold; font-size: 14px;")
                    title_layout.addWidget(status_label)
                    
                    bit_layout.addLayout(title_layout)
                    
                    # 名称
                    name_label = BodyLabel(bit_analysis['name'], self)
                    name_label.setStyleSheet("font-style: italic; color: #666;")
                    bit_layout.addWidget(name_label)
                    
                    # 简介
                    intro_label = BodyLabel(bit_analysis['intro'], self)
                    intro_label.setWordWrap(True)
                    bit_layout.addWidget(intro_label)
                    
                    # 分隔线
                    line = QFrame(self)
                    line.setFrameShape(QFrame.HLine)
                    line.setStyleSheet("background-color: #E0E0E0;")
                    bit_layout.addWidget(line)
                    
                    # 状态描述
                    desc_label = BodyLabel(bit_analysis['description'], self)
                    desc_label.setWordWrap(True)
                    bit_layout.addWidget(desc_label)
                    
                    # 清除条件
                    if bit_analysis['clear_conditions']:
                        clear_title = StrongBodyLabel("清除条件:", self)
                        clear_title.setStyleSheet("font-weight: 600; margin-top: 8px;")
                        bit_layout.addWidget(clear_title)
                        
                        for condition in bit_analysis['clear_conditions']:
                            cond_label = BodyLabel(f"• {condition}", self)
                            cond_label.setWordWrap(True)
                            cond_label.setStyleSheet("color: #52C41A;")
                            bit_layout.addWidget(cond_label)
                    
                    self.detail_layout.insertWidget(self.detail_layout.count() - 1, bit_card)
                except Exception as e:
                    logger.exception(f"添加置位状态位 #{idx+1} 失败：{e}")
        
        # 清零状态位信息
        if result['cleared_bits']:
            logger.debug(f"清零状态位数量：{len(result['cleared_bits'])}")
            cleared_title = StrongBodyLabel("清零状态位", self.detail_container)
            cleared_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 16px;")
            self.detail_layout.insertWidget(self.detail_layout.count() - 1, cleared_title)
            
            cleared_card = CardWidget(self.detail_container)
            cleared_layout = QVBoxLayout(cleared_card)
            cleared_layout.setContentsMargins(16, 12, 16, 12)
            cleared_layout.setSpacing(8)
            
            cleared_list = []
            for bit_analysis in result['cleared_bits']:
                item = f"Bit {bit_analysis['bit']} - {bit_analysis['abbr']}: {bit_analysis['description']}"
                cleared_list.append(item)
            
            for item in cleared_list:
                item_label = BodyLabel(f"• {item}", self)
                item_label.setWordWrap(True)
                item_label.setStyleSheet("color: #52C41A;")
                cleared_layout.addWidget(item_label)
            
            self.detail_layout.insertWidget(self.detail_layout.count() - 1, cleared_card)
    
    def _clear_bits(self):
        """清空状态位分布卡片 - 安全删除所有子组件"""
        if not hasattr(self, 'bits_grid_layout'):
            return
        
        # 关键修复：必须先从布局中移除 item，再删除 widget
        while self.bits_grid_layout.count():
            item = self.bits_grid_layout.itemAt(0)
            if item:
                widget = item.widget()
                if widget:
                    self.bits_grid_layout.removeItem(item)  # 先从布局移除
                    widget.deleteLater()  # 再标记删除
        
        # 等待事件循环处理完删除操作
        QApplication.processEvents()
    
    def _clear_details(self):
        """清空详细解析卡片内容 - 安全删除所有子组件"""
        if not hasattr(self, 'detail_layout'):
            return
        
        # 关键修复：必须先从布局中移除 item，再删除 widget
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)  # takeAt 已经从布局移除
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
                else:
                    # 可能是 QSpacerItem 或其他非 widget 项
                    pass
        
        # 等待事件循环处理完删除操作
        QApplication.processEvents()
        
        # 重新添加底部弹簧
        self.detail_layout.addStretch()
    
    def _create_bit_block(self, bit_info, is_set) -> QWidget:
        """创建状态位方块"""
        widget = QWidget()
        # 增大宽度以显示完整描述
        widget.setFixedSize(120, 140)
        widget.setStyleSheet("""
            QWidget {
                border-radius: 8px;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)  # 内容靠上对齐
        
        # Bit 编号
        bit_label = StrongBodyLabel(f"Bit {bit_info.bit}", widget)
        bit_label.setAlignment(Qt.AlignCenter)
        bit_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(bit_label)
        
        # 缩写
        abbr_label = BodyLabel(bit_info.abbr, widget)
        abbr_label.setAlignment(Qt.AlignCenter)
        abbr_label.setStyleSheet("color: #0078D4; font-weight: bold; font-size: 13px;")
        layout.addWidget(abbr_label)
        
        # 名称 - 允许换行，不再截断
        name_label = BodyLabel(bit_info.name, widget)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)  # 自动换行
        name_label.setStyleSheet("font-size: 11px; color: #666; padding: 4px;")
        layout.addWidget(name_label)
        
        # 状态指示器 - 更大更清晰
        if is_set:
            status_label = QLabel("1", widget)
            status_label.setStyleSheet("""
                QLabel {
                    background-color: #FF4D4F;
                    color: white;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 8px;
                    border-radius: 8px;
                    min-width: 42px;
                    max-width: 42px;
                    min-height: 42px;
                    max-height: 42px;
                }
            """)
        else:
            status_label = QLabel("0", widget)
            status_label.setStyleSheet("""
                QLabel {
                    background-color: #52C41A;
                    color: white;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 8px;
                    border-radius: 8px;
                    min-width: 42px;
                    max-width: 42px;
                    min-height: 42px;
                    max-height: 42px;
                }
            """)
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        return widget
