import json
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QFileDialog, QListWidget, QListWidgetItem, 
                               QMessageBox, QComboBox, QLabel, QProgressBar)
from qfluentwidgets import (
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    SubtitleLabel,
    BodyLabel,
    ElevatedCardWidget,
    ProgressBar
)

from app.model.fault_model import FaultManager


class ImportExportUI(QWidget):
    """导入导出管理界面"""
    def __init__(self, fault_manager: FaultManager, parent=None):
        super().__init__(parent)
        self.fault_manager = fault_manager
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        layout.addWidget(SubtitleLabel(self.tr("批量导入导出"), self))
        
        # 导出功能
        export_card = ElevatedCardWidget(self)
        export_layout = QVBoxLayout(export_card)
        export_layout.addWidget(SubtitleLabel(self.tr("导出数据"), self))
        
        # 导出项目选择
        export_project_layout = QHBoxLayout()
        export_project_layout.addWidget(BodyLabel(self.tr("选择项目:"), self))
        self.exportProjectComboBox = QComboBox(self)
        self.exportProjectComboBox.setPlaceholderText(self.tr("选择项目"))
        export_project_layout.addWidget(self.exportProjectComboBox)
        export_project_layout.addStretch()
        export_layout.addLayout(export_project_layout)
        
        # 导出按钮
        export_button_layout = QHBoxLayout()
        self.exportJsonButton = PrimaryPushButton(FIF.SHARE, self.tr("导出为JSON"), self)
        self.exportExcelButton = PushButton(FIF.SHARE, self.tr("导出为Excel"), self)
        export_button_layout.addWidget(self.exportJsonButton)
        export_button_layout.addWidget(self.exportExcelButton)
        export_button_layout.addStretch()
        export_layout.addLayout(export_button_layout)
        
        layout.addWidget(export_card)
        
        # 导入功能
        import_card = ElevatedCardWidget(self)
        import_layout = QVBoxLayout(import_card)
        import_layout.addWidget(SubtitleLabel(self.tr("导入数据"), self))
        
        # 导入项目选择
        import_project_layout = QHBoxLayout()
        import_project_layout.addWidget(BodyLabel(self.tr("目标项目:"), self))
        self.importProjectComboBox = QComboBox(self)
        self.importProjectComboBox.setPlaceholderText(self.tr("选择项目"))
        import_project_layout.addWidget(self.importProjectComboBox)
        import_project_layout.addStretch()
        import_layout.addLayout(import_project_layout)
        
        # 导入按钮
        import_button_layout = QHBoxLayout()
        self.importJsonButton = PrimaryPushButton(FIF.DOWNLOAD, self.tr("从JSON导入"), self)
        self.importExcelButton = PushButton(FIF.DOWNLOAD, self.tr("从Excel导入"), self)
        import_button_layout.addWidget(self.importJsonButton)
        import_button_layout.addWidget(self.importExcelButton)
        import_button_layout.addStretch()
        import_layout.addLayout(import_button_layout)
        
        layout.addWidget(import_card)
        
        # 进度条
        self.progressBar = ProgressBar(self)
        self.progressBar.setVisible(False)
        layout.addWidget(self.progressBar)
        
        # 连接信号
        self.exportJsonButton.clicked.connect(self._on_export_json)
        self.exportExcelButton.clicked.connect(self._on_export_excel)
        self.importJsonButton.clicked.connect(self._on_import_json)
        self.importExcelButton.clicked.connect(self._on_import_excel)
        
        # 加载项目列表
        self._load_projects()
    
    def _load_projects(self):
        """加载项目列表"""
        self.exportProjectComboBox.clear()
        self.importProjectComboBox.clear()
        
        for project_id, project in self.fault_manager.projects.items():
            self.exportProjectComboBox.addItem(project.name, project_id)
            self.importProjectComboBox.addItem(project.name, project_id)
    
    def _on_export_json(self):
        """导出为JSON文件"""
        project_id = self.exportProjectComboBox.currentData()
        if not project_id:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个项目"))
            return
        
        project = self.fault_manager.get_project(project_id)
        if not project:
            QMessageBox.warning(self, self.tr("警告"), self.tr("项目不存在"))
            return
        
        # 选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            self.tr("导出为JSON"), 
            f"{project.name}_export.json", 
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        # 导出数据
        try:
            items_data = []
            for item_id in project.item_ids:
                item = self.fault_manager.get_item(item_id)
                if item:
                    items_data.append(item.to_dict())
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(items_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, self.tr("成功"), self.tr(f"已成功导出 {len(items_data)} 个条目到 {file_path}"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("错误"), self.tr(f"导出失败: {str(e)}"))
    
    def _on_export_excel(self):
        """导出为Excel文件"""
        QMessageBox.information(self, self.tr("提示"), self.tr("Excel导出功能暂未实现"))
    
    def _on_import_json(self):
        """从JSON文件导入"""
        project_id = self.importProjectComboBox.currentData()
        if not project_id:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个目标项目"))
            return
        
        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            self.tr("从JSON导入"), 
            "", 
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        # 导入数据
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                items_data = json.load(f)
            
            # 显示进度条
            self.progressBar.setVisible(True)
            self.progressBar.setRange(0, len(items_data))
            
            # 导入条目
            imported_count = 0
            for i, item_data in enumerate(items_data):
                # 更新进度
                self.progressBar.setValue(i + 1)
                
                # 创建新条目
                item = self.fault_manager.create_item(
                    template_id=item_data['template_id'],
                    project_id=project_id,
                    title=item_data.get('title', "")
                )
                
                # 设置字段值和关联关系
                item.field_values = item_data.get('field_values', {})
                item.relationships = item_data.get('relationships', [])
                self.fault_manager.update_item(item)
                imported_count += 1
            
            # 隐藏进度条
            self.progressBar.setVisible(False)
            
            QMessageBox.information(self, self.tr("成功"), self.tr(f"已成功导入 {imported_count} 个条目"))
        except Exception as e:
            self.progressBar.setVisible(False)
            QMessageBox.critical(self, self.tr("错误"), self.tr(f"导入失败: {str(e)}"))
    
    def _on_import_excel(self):
        """从Excel文件导入"""
        QMessageBox.information(self, self.tr("提示"), self.tr("Excel导入功能暂未实现"))