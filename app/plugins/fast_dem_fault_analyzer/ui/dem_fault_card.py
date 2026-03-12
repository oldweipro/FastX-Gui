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
)
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


class DEMFaultCard(CardWidget):
    """DEM 故障分析器主卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.analyzer = DEMFaultAnalyzer()
        
        # 设置卡片的最小尺寸
        self.setMinimumSize(800, 600)
        
        self._init_ui()
        self._connect_signals()
    
    def _init_ui(self):
        self.setObjectName("DEMFaultCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # 标题
        title = TitleLabel("DEM 故障分析器", self)
        layout.addWidget(title)
        
        # 副标题
        subtitle = BodyLabel("基于 AUTOSAR CP DEM 的 DTC 故障状态分析工具", self)
        subtitle.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(subtitle)
        
        # 输入区域
        input_card = CardWidget(self)
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)
        
        input_label = StrongBodyLabel("请输入 DTC 状态码:", self)
        input_layout.addWidget(input_label)
        
        self.input_edit = LineEdit(self)
        self.input_edit.setPlaceholderText("格式：0x6C 或 6C")
        self.input_edit.setMinimumHeight(36)
        input_layout.addWidget(self.input_edit)
        
        analyze_btn = PrimaryPushButton("分析", self)
        analyze_btn.setIcon(FIF.SEARCH)
        analyze_btn.setMinimumHeight(36)
        analyze_btn.installEventFilter(ToolTipFilter(analyze_btn))
        analyze_btn.setToolTip("点击分析 DTC 状态码")
        input_layout.addWidget(analyze_btn)
        
        layout.addWidget(input_card)
        
        # 结果显示区域 - 增加最小高度
        result_scroll = SmoothScrollArea(self)
        result_scroll.setWidgetResizable(True)
        result_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        result_scroll.enableTransparentBackground()
        result_scroll.setMinimumHeight(400)  # 设置最小高度
        
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_layout.setSpacing(12)
        
        result_scroll.setWidget(self.result_container)
        layout.addWidget(result_scroll, 1)  # stretch=1 让它占据剩余空间
        
        # 初始提示
        self._show_initial_message()
    
    def _connect_signals(self):
        # 获取所有按钮
        buttons = self.findChildren(PrimaryPushButton)
        for btn in buttons:
            if btn.text() == "分析":
                btn.clicked.connect(self._on_analyze_clicked)
    
    def _show_initial_message(self):
        """显示初始提示信息"""
        self._clear_result()
        
        msg_label = BodyLabel("请输入 DTC 状态码（格式：0x6C 或 6C），然后点击分析按钮", self.result_container)
        msg_label.setStyleSheet("color: #999; font-style: italic; padding: 20px;")
        msg_label.setAlignment(Qt.AlignCenter)
        self.result_layout.addWidget(msg_label)
    
    def _clear_result(self):
        """清空结果区域"""
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _on_analyze_clicked(self):
        """点击分析按钮"""
        status_input = self.input_edit.text().strip()
        
        if not status_input:
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
            InfoBar.error(
                title="分析失败",
                content=result.get('error', '未知错误'),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return
        
        # 显示分析结果
        self._display_analysis_result(result)
        
        InfoBar.success(
            title="分析完成",
            content=f"DTC 状态码 {status_input} 分析完成",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2000
        )
    
    def _display_analysis_result(self, result: Dict):
        """显示分析结果"""
        self._clear_result()
        
        basic_info = result['basic_info']
        
        # 基本信息卡片
        info_card = CardWidget(self.result_container)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(16, 12, 16, 12)
        info_layout.setSpacing(8)
        
        # 标题
        info_title = StrongBodyLabel("状态码信息", self)
        info_layout.addWidget(info_title)
        
        # HEX
        hex_label = BodyLabel(f"HEX: {basic_info['hex']}", self)
        info_layout.addWidget(hex_label)
        
        # Decimal
        dec_label = BodyLabel(f"Decimal: {basic_info['decimal']}", self)
        info_layout.addWidget(dec_label)
        
        # Binary
        bin_label = BodyLabel(f"Binary: {basic_info['binary']}", self)
        info_layout.addWidget(bin_label)
        
        self.result_layout.addWidget(info_card)
        
        # 状态位方块视图
        bits_card = CardWidget(self.result_container)
        bits_layout = QVBoxLayout(bits_card)
        bits_layout.setContentsMargins(16, 12, 16, 12)
        bits_layout.setSpacing(12)
        
        bits_title = StrongBodyLabel("状态位分布", self)
        bits_layout.addWidget(bits_title)
        
        # 网格布局显示 8 个状态位
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        # 从高位到低位显示 (Bit7 到 Bit0)
        for i in range(8):
            bit = 7 - i
            is_set = basic_info['bits'][bit]
            bit_info = DTCStatusConfig.get_bit_info(bit)
            
            if bit_info:
                bit_widget = self._create_bit_block(bit_info, is_set)
                row = 0
                col = i
                grid_layout.addWidget(bit_widget, row, col)
        
        bits_layout.addLayout(grid_layout)
        self.result_layout.addWidget(bits_card)
        
        # 置位状态位详细解析
        if result['set_bits']:
            detail_card = CardWidget(self.result_container)
            detail_layout = QVBoxLayout(detail_card)
            detail_layout.setContentsMargins(16, 12, 16, 12)
            detail_layout.setSpacing(12)
            
            detail_title = StrongBodyLabel("置位状态位详细解析", self)
            detail_layout.addWidget(detail_title)
            
            for bit_analysis in result['set_bits']:
                bit_card = BitStatusCard(
                    type('BitInfo', (), bit_analysis),
                    True,
                    self.result_container
                )
                detail_layout.addWidget(bit_card)
            
            self.result_layout.addWidget(detail_card)
    
    def _create_bit_block(self, bit_info, is_set) -> QWidget:
        """创建状态位方块"""
        widget = QWidget()
        widget.setFixedSize(90, 120)  # 增大方块尺寸
        widget.setStyleSheet("""
            QWidget {
                border-radius: 8px;
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)  # 增加间距
        layout.setAlignment(Qt.AlignCenter)
        
        # Bit 编号
        bit_label = StrongBodyLabel(f"Bit {bit_info.bit}", widget)
        bit_label.setAlignment(Qt.AlignCenter)
        bit_label.setStyleSheet("font-size: 13px; font-weight: bold;")  # 增大字体
        layout.addWidget(bit_label)
        
        # 缩写
        abbr_label = BodyLabel(bit_info.abbr, widget)
        abbr_label.setAlignment(Qt.AlignCenter)
        abbr_label.setStyleSheet("color: #0078D4; font-weight: bold; font-size: 12px;")  # 增大字体
        layout.addWidget(abbr_label)
        
        # 名称（截断）
        name = bit_info.name
        if len(name) > 10:
            name = name[:9] + "…"
        name_label = BodyLabel(name, widget)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(name_label)
        
        # 状态 - 增大数字和内边距
        if is_set:
            status_label = QLabel("1", widget)
            status_label.setStyleSheet("""
                QLabel {
                    background-color: #FF4D4F;
                    color: white;
                    font-weight: bold;
                    font-size: 18px;
                    padding: 6px;
                    border-radius: 6px;
                    min-width: 36px;
                    max-width: 36px;
                    min-height: 36px;
                    max-height: 36px;
                }
            """)
        else:
            status_label = QLabel("0", widget)
            status_label.setStyleSheet("""
                QLabel {
                    background-color: #52C41A;
                    color: white;
                    font-weight: bold;
                    font-size: 18px;
                    padding: 6px;
                    border-radius: 6px;
                    min-width: 36px;
                    max-width: 36px;
                    min-height: 36px;
                    max-height: 36px;
                }
            """)
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        return widget
