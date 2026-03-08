"""
CCP工具主界面组件
采用MVC模式，分离视图和业务逻辑
"""

from typing import Dict, Any, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QInputDialog, QMessageBox
)
from qfluentwidgets import (
    ExpandSettingCard, PrimaryPushSettingCard, PushSettingCard, 
    ComboBox, FluentIcon as FIF
)

from app.common.config import cfg
from app.common.icon import Icon
from ..core.processor import CCPProcessor


class CCPMainWidget(ExpandSettingCard):
    """CCP工具主界面组件"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化主界面
        
        Args:
            parent: 父级窗口
        """
        super().__init__(
            icon=Icon.CCP,
            title=self.tr("CCP Tool"),
            content=self.tr("CCP protocol diagnostic and analysis tool"),
            parent=parent
        )
        
        # 初始化核心处理器
        self.processor = CCPProcessor()
        
        # 初始化UI组件
        self._init_ui()
        self._setup_connections()
    
    def _init_ui(self):
        """初始化UI组件"""
        # 选项选择器
        self.option_combo = ComboBox(self)
        self.option_combo.addItems([
            self.tr("Full Processing"),
            self.tr("Analysis Only"), 
            self.tr("Configuration Mode")
        ])
        
        # 文件夹选择卡片
        self.output_folder_card = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Output Directory"),
            cfg.get(cfg.fastCCPOutputFolder) or ""
        )
        
        # 文件选择卡片
        self.input_file_card = PushSettingCard(
            self.tr("Choose file"),
            FIF.DOCUMENT,
            self.tr("Input File"),
            cfg.get(cfg.fastCCPInputFile) or ""
        )
        
        # 执行按钮
        self.execute_card = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute CCP Processing"),
            self.tr("Click to start processing")
        )
        
        # 添加到布局
        self._add_cards_to_layout()
        
        # 应用初始状态
        self._apply_option_state(0)
    
    def _add_cards_to_layout(self):
        """添加卡片到布局"""
        self.card.addWidget(self.option_combo)
        self.viewLayout.addWidget(self.input_file_card)
        self.viewLayout.addWidget(self.output_folder_card)
        self.viewLayout.addWidget(self.execute_card)
        self._adjustViewSize()
    
    def _setup_connections(self):
        """设置信号连接"""
        # 选项变化
        self.option_combo.currentIndexChanged.connect(self._on_option_changed)
        
        # 文件夹选择
        self.output_folder_card.clicked.connect(self._on_choose_output_folder)
        
        # 文件选择
        self.input_file_card.clicked.connect(self._on_choose_input_file)
        
        # 执行按钮
        self.execute_card.clicked.connect(self._on_execute_clicked)
    
    def _on_option_changed(self, index: int):
        """处理选项变化"""
        self._apply_option_state(index)
        # 保存选择到配置
        cfg.set(cfg.fastCCPSelectedOption, index)
    
    def _on_choose_output_folder(self):
        """选择输出文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, 
            self.tr("Choose output folder"), 
            cfg.get(cfg.fastCCPOutputFolder) or ""
        )
        if folder:
            cfg.set(cfg.fastCCPOutputFolder, folder)
            self.output_folder_card.setContent(folder)
    
    def _on_choose_input_file(self):
        """选择输入文件"""
        file, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Choose input file"),
            cfg.get(cfg.fastCCPInputFile) or "",
            "All Files (*.*);;Excel Files (*.xlsx);;ARXML Files (*.arxml)"
        )
        if file:
            cfg.set(cfg.fastCCPInputFile, file)
            self.input_file_card.setContent(file)
    
    def _on_execute_clicked(self):
        """执行处理"""
        try:
            # 获取配置
            config = self.get_config()
            
            # 验证输入
            if not config["input_file"]:
                QMessageBox.warning(self, self.tr("Warning"), self.tr("Please select input file"))
                return
            
            # 执行处理
            result = self.processor.process(config)
            
            # 显示结果
            if result.success:
                QMessageBox.information(
                    self, 
                    self.tr("Success"), 
                    self.tr(f"Processing completed!\n{result.message}")
                )
            else:
                QMessageBox.critical(
                    self, 
                    self.tr("Error"), 
                    self.tr(f"Processing failed: {result.message}")
                )
                
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Processing error: {str(e)}"))
    
    def _apply_option_state(self, index: int):
        """根据选项应用UI状态"""
        if index == 0:  # Full Processing
            self.output_folder_card.setVisible(True)
            self.input_file_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.output_folder_card.setEnabled(True)
            self.input_file_card.setEnabled(True)
            self.execute_card.setEnabled(True)
        elif index == 1:  # Analysis Only
            self.output_folder_card.setVisible(False)
            self.input_file_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.input_file_card.setEnabled(True)
            self.execute_card.setEnabled(True)
        elif index == 2:  # Configuration Mode
            self.output_folder_card.setVisible(True)
            self.input_file_card.setVisible(False)
            self.execute_card.setVisible(False)
            self.output_folder_card.setEnabled(True)
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取当前配置
        
        Returns:
            Dict: 配置字典
        """
        return {
            "input_file": cfg.get(cfg.fastCCPInputFile) or "",
            "output_folder": cfg.get(cfg.fastCCPOutputFolder) or "",
            "selected_option": self.option_combo.currentIndex()
        }
    
    def set_config(self, config: Dict[str, Any]):
        """
        设置配置
        
        Args:
            config: 配置字典
        """
        if "input_file" in config:
            cfg.set(cfg.fastCCPInputFile, config["input_file"])
            self.input_file_card.setContent(config["input_file"])
            
        if "output_folder" in config:
            cfg.set(cfg.fastCCPOutputFolder, config["output_folder"])
            self.output_folder_card.setContent(config["output_folder"])
            
        if "selected_option" in config:
            index = config["selected_option"]
            if 0 <= index < self.option_combo.count():
                self.option_combo.setCurrentIndex(index)
                self._apply_option_state(index)
    
    def cleanup(self):
        """清理资源"""
        # 清理处理器
        self.processor.cleanup()