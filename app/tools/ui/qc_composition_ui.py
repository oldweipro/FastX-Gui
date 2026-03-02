from PySide6.QtCore import QModelIndex, QPoint
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QInputDialog, QMessageBox, QVBoxLayout, QWidget, \
    QTableWidget, QTableWidgetItem, QHeaderView, QItemDelegate, QComboBox, QStyledItemDelegate, QMenu, QLineEdit, \
    QAbstractItemView
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, ScrollArea, FluentIconBase, ComboBox, TableWidget, IconWidget, FluentIcon, SearchLineEdit,
    StrongBodyLabel, Dialog, LineEdit, PrimaryPushButton, PushButton, MessageBoxBase, BodyLabel, SpinBox, SubtitleLabel
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon
from app.tools.core.rm_comments_core import RmCommentsCore


class CoreAssignDelegate(QStyledItemDelegate):
    """Fluent ComboBox Delegate"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.core_options = ['Core0', 'Core1', 'Core2', 'None']

    def createEditor(self, parent, option, index):
        editor = ComboBox(parent)
        editor.addItems(self.core_options)

        # 选中立即提交（工程上更干净）
        editor.currentIndexChanged.connect(
            lambda: self.commitData.emit(editor)
        )

        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value in self.core_options:
            editor.setCurrentText(value)
        else:
            editor.setCurrentIndex(0)  # Default to Core0

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        """Update editor geometry to match cell"""
        editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        """Paint the cell normally when not editing"""
        # Let the parent class handle the painting when not editing
        super().paint(painter, option, index)

    def sizeHint(self, option, index):
        """Return appropriate size hint"""
        return super().sizeHint(option, index)


class TableFrame(TableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 核心控制：禁用单元格直接编辑 , 否则双击会进入默认编辑器
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.verticalHeader().hide()
        self.setBorderRadius(8)
        self.setBorderVisible(True)
        self.setWordWrap(False)

        self.columnMeta = [
            {"type": "text"},  # Swc Name
            {"type": "combo", "options": ["Core0", "Core1", "Core2", "None"]},
            {"type": "int"},
            {"type": "int"},
            {"type": "int"},
            {"type": "int"}
        ]

        self.headInfos = [
            self.tr('Swc Name'),
            self.tr('Core Assign'),
            self.tr('P-Ports'),
            self.tr('R-Ports'),
            self.tr('Runnables'),
            self.tr('Events')
        ]
        
        # Load data from cfg
        self.swcsInfos = self._loadFromConfig()
        
        self.setColumnCount(len(self.headInfos))
        self.setRowCount(len(self.swcsInfos))
        self.setMinimumHeight(300)
        self.setHorizontalHeaderLabels(self.headInfos)
        
        # Set up table
        for i, swcInfo in enumerate(self.swcsInfos):
            for j in range(len(self.headInfos)):
                item = QTableWidgetItem(swcInfo[j])
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(i, j, item)
        
        # # Set delegate for Core Assign column (index 1)
        # self.coreDelegate = CoreAssignDelegate(self)
        # self.setItemDelegateForColumn(1, self.coreDelegate)
        
        # 核心：列宽自适应父窗口
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # 可选：Header 文本对齐
        header.setDefaultAlignment(Qt.AlignCenter)
        
        # Connect cell change signal
        self.itemChanged.connect(self._onItemChanged)
        
        # Enable double-click edit
        self.doubleClicked.connect(self._onDoubleClicked)
    
    def _loadFromConfig(self):
        """
        Load table data from configuration
        """
        try:
            data = cfg.get(cfg.QcCompositionTableData)
            if data:
                return data
        except:
            pass
        # Default data if no config
        return [['ExampleSwc', 'Core0', '0', '0', '2', '2']]
    
    def _saveToConfig(self):
        """
        Save table data to configuration
        """
        data = []
        for i in range(self.rowCount()):
            row = []
            for j in range(self.columnCount()):
                item = self.item(i, j)
                row.append(item.text() if item else '')
            data.append(row)
        cfg.set(cfg.QcCompositionTableData, data)
    
    def _onItemChanged(self, item):
        """
        Handle item change and save to config
        """
        self._saveToConfig()

    def createEditorDialog(self, headers, row_data, column_meta):
        class TableEditDialog(MessageBoxBase):
            def __init__(self, headers, row_data, column_meta, parent=None):
                super().__init__(parent)
                # 标题
                self.titleLabel = SubtitleLabel(self.tr("编辑条目"), self)
                self.viewLayout.addWidget(self.titleLabel)

                self._widgets = []
                # 创建每一行
                for i, title in enumerate(headers):
                    meta = column_meta[i]
                    value = row_data[i]

                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(10)

                    label = BodyLabel(title)
                    label.setFixedWidth(120)
                    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    row_layout.addWidget(label)

                    # 根据类型创建控件
                    if meta["type"] == "combo":
                        widget = ComboBox()
                        widget.addItems(meta["options"])
                        if value in meta["options"]:
                            widget.setCurrentText(value)
                    elif meta["type"] == "int":
                        widget = SpinBox()
                        widget.setRange(0, 9999)
                        widget.setValue(int(value))
                    else:
                        widget = LineEdit()
                        widget.setText(value)

                    widget.setMinimumWidth(250)
                    row_layout.addWidget(widget)
                    self._widgets.append(widget)

                    self.viewLayout.addLayout(row_layout)

                self.yesButton.setText(self.tr("Save"))
                self.cancelButton.setText(self.tr("Cancel"))
                self.widget.setMinimumWidth(600)  # 设置对话框最小宽度

            def get_data(self):
                """获取编辑后的数据"""
                data = []
                for w in self._widgets:
                    if isinstance(w, ComboBox):
                        data.append(w.currentText())
                    elif isinstance(w, SpinBox):
                        data.append(str(w.value()))
                    else:
                        data.append(w.text())
                return data

        # 创建对话框实例，父窗口为主窗口
        return TableEditDialog(headers, row_data, column_meta, self.window())

    def _onDoubleClicked(self, index):
        row = index.row()

        self.row_data = [
            self.item(row, col).text() if self.item(row, col) else ""
            for col in range(self.columnCount())
        ]

        dialog = self.createEditorDialog(
            self.headInfos,
            self.row_data,
            self.columnMeta
        )

        if dialog.exec():
            new_data = dialog.get_data()

            self.blockSignals(True)
            for col, value in enumerate(new_data):
                self.item(row, col).setText(value)
            self.blockSignals(False)

            self._saveToConfig()

        # 可选：让最后一列自动填满剩余空间（如果不想所有列均分）
        # header.setStretchLastSection(True)

        # 可选：通过内容主导宽度
        # self.setFixedSize(625, 440)
        # self.resizeColumnsToContents()


class QcCompositionUI(ExpandSettingCard):
    """QCraft Composition Arxml Adapter UI class"""

    def __init__(
        self,
        icon: str | QIcon | FluentIconBase=None,
        title: str = None,
        content=None,
        parent=None,
    ):
        # 如果 icon 为 None，可以设置一个默认图标
        if icon is None:
            icon = UnicodeIcon.get_icon_by_name("ic_fluent_comment_dismiss_24_regular")
        # 如果 title 为空字符串，设置默认标题
        if not title:
            title = self.tr("QCraft Composition Arxml Adapter")
        # 如果 content 为空字符串，设置默认标题
        if content is None:
            content = self.tr("To Modify QCraft Composition Arxml File To FT Rules For J6")
        super().__init__(icon, title, content, parent)
        self.core = RmCommentsCore()
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        # Load saved option from config
        selected_index = cfg.get(cfg.QcCompositionSelectedOption)
        if 0 <= selected_index < self.combox.count():
            self.combox.setCurrentIndex(selected_index)
        self.card.addWidget(self.combox)
        self.__initCards()
        # Apply initial card states based on saved option
        self.__onComboBoxChanged(selected_index)
        self.connectSignals()

    def __initCards(self):
        """
        初始化卡片
        """

        # 文件夹选择卡片
        self.qcCompositionInputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Input Directory"),
            cfg.get(cfg.QcCompositionInputFolder)
        )

        # 文件选择卡片
        self.qcCompositionInputFileCard = PushSettingCard(
            self.tr("Choose file"),
            FIF.HEART,
            self.tr("Input File"),
            cfg.get(cfg.QcCompositionInputFile)
        )

        # 表格卡片配置
        self.tabCard = TableFrame(self)

        # Execute button
        self.qcCompositionExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute QCraft Composition Adaptation"),
            self.tr("Click to start processing")
        )

        # 添加卡片到布局
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        """
        添加卡片到布局
        """
        self.viewLayout.addWidget(self.qcCompositionInputFolderCard)
        self.viewLayout.addWidget(self.qcCompositionInputFileCard)
        self.viewLayout.addWidget(self.tabCard)
        self.viewLayout.addWidget(self.qcCompositionExecuteCard)

        self._adjustViewSize()

    def connectSignals(self):
        """
        连接信号
        """
        # 按钮 | 选择文件夹
        self.qcCompositionInputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.QcCompositionInputFolder, self.qcCompositionInputFolderCard)
        )

        # 按钮 | 选择文件
        self.qcCompositionInputFileCard.clicked.connect(
            lambda: self.__onChooseFileClicked(cfg.QcCompositionInputFile, self.qcCompositionInputFileCard)
        )

        # Execute button connection
        self.qcCompositionExecuteCard.clicked.connect(self.__onExecuteQcCompositionClicked)
        
        # ComboBox signal for controlling cards
        self.combox.currentIndexChanged.connect(self.__onComboBoxChanged)

    def __onChooseFolderClicked(self, config_item, card):
        """
        通用文件夹选择方法

        Args:
            config_item: 配置项
            card: 卡片对象
        """
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), cfg.get(config_item))
        if not folder or cfg.get(config_item) == folder:
            return
        cfg.set(config_item, folder)
        card.setContent(folder)

    def __onChooseFileClicked(self, config_item, card):
        """
        通用文件选择方法

        Args:
            config_item: 配置项
            card: 卡片对象
        """
        file, _ = QFileDialog.getOpenFileName(self, self.tr("Choose file"), cfg.get(config_item), "Excel Files (*.xlsx);;ARXML Files (*.arxml);;All Files (*)")
        if not file or cfg.get(config_item) == file:
            return
        cfg.set(config_item, file)
        card.setContent(file)

    def __onSetValueClicked(self, config_item, card, title):
        """
        通用值设置方法

        Args:
            config_item: 配置项
            card: 卡片对象
            title: 对话框标题
        """
        current_value = cfg.get(config_item)
        value, ok = QInputDialog.getText(self, title, title, text=current_value)
        if ok and value != current_value:
            cfg.set(config_item, value)
            card.setContent(value)

    def __onExecuteQcCompositionClicked(self):
        """
        执行QCraft Composition适配
        """
        try:
            # 显示结果
            message = self.tr("Processing completed!\n")
            QMessageBox.information(self, self.tr("Success"), message)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Processing failed: {str(e)}"))
    
    def __onComboBoxChanged(self, index):
        """
        处理ComboBox选择变化，控制卡片的可见性和启用状态
        
        Args:
            index: 选中项的索引
        """
        # Save selected option to config
        cfg.set(cfg.QcCompositionSelectedOption, index)
        
        if index == 0:  # Option 1
            # 显示所有卡片并启用
            self.qcCompositionInputFolderCard.setVisible(True)
            self.qcCompositionInputFileCard.setVisible(True)
            self.qcCompositionExecuteCard.setVisible(True)
            self.qcCompositionInputFolderCard.setEnabled(True)
            self.qcCompositionInputFileCard.setEnabled(True)
            self.qcCompositionExecuteCard.setEnabled(True)
        elif index == 1:  # Option 2
            # 只显示输入文件夹卡片，禁用执行按钮
            self.qcCompositionInputFolderCard.setVisible(True)
            self.qcCompositionInputFileCard.setVisible(True)
            self.qcCompositionExecuteCard.setVisible(False)
            self.qcCompositionInputFolderCard.setEnabled(True)
            self.qcCompositionInputFileCard.setEnabled(True)
        elif index == 2:  # Option 3
            # 显示所有卡片但禁用
            self.qcCompositionInputFolderCard.setVisible(True)
            self.qcCompositionInputFileCard.setVisible(True)
            self.qcCompositionExecuteCard.setVisible(True)
            self.qcCompositionInputFolderCard.setEnabled(False)
            self.qcCompositionInputFileCard.setEnabled(False)
            self.qcCompositionExecuteCard.setEnabled(False)
        
        # 调整布局大小
        self._adjustViewSize()
