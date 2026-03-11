from PySide6.QtCore import QModelIndex, QPoint
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget, \
    QTableWidget, QTableWidgetItem, QHeaderView, QItemDelegate, QComboBox, QStyledItemDelegate, QMenu, QLineEdit, \
    QAbstractItemView
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, ScrollArea, FluentIconBase, ComboBox, TableWidget, IconWidget, FluentIcon, SearchLineEdit,
    StrongBodyLabel, Dialog, LineEdit, PrimaryPushButton, PushButton, MessageBoxBase, BodyLabel, SpinBox, SubtitleLabel,
    ComboBoxSettingCard, MessageBox
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon, Icon
from app.common.notification import Notification
from app.common.utils import downloadTemplate


class FastE2EToolUI(ExpandSettingCard):
    """FastE2E Tool UI class"""

    def __init__(
            self,
            icon: str | QIcon | FluentIconBase = None,
            title: str = None,
            content=None,
            parent=None,
    ):
        # 如果 icon 为 None，可以设置一个默认图标
        if icon is None:
            icon = Icon.E2E
        # 如果 title 为空字符串，设置默认标题
        if not title:
            title = self.tr("FastE2E Tool")
        # 如果 content 为空字符串，设置默认标题
        if content is None:
            content = self.tr("FastE2E Tool for processing E2E files")
        super().__init__(icon, title, content, parent)
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        # Load saved option from config
        selected_index = cfg.get(cfg.fastE2ESelectedOption)
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
        self.fastE2EOutputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("FastE2E Output Directory"),
            cfg.get(cfg.fastE2EOutputFolder)
        )

        # 文件选择卡片
        self.fastE2EInputFileCard = PushSettingCard(
            self.tr("Choose file"),
            UnicodeIcon.get_icon_by_name('ic_fluent_document_table_truck_24_regular'),
            self.tr("Input File"),
            cfg.get(cfg.fastE2EInputFile)
        )

        # 方向切换组合框 (Tx/Rx)
        self.directionCard = ComboBoxSettingCard(
            cfg.fastE2EDirection,
            UnicodeIcon.get_icon_by_name("ic_fluent_text_paragraph_24_regular"),
            self.tr("Direction"),
            self.tr("Select the direction for E2E processing"),
            texts=[self.tr("Tx"), self.tr("Rx")]
        )

        # 下载模板按钮
        self.downloadTemplateCard = PushSettingCard(
            self.tr("Download Template"),
            FIF.DOWNLOAD,
            self.tr("Download Excel Template"),
            self.tr("Click to download the Excel template for E2E processing")
        )

        # Execute button
        self.fastE2EExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute FastE2E Processing"),
            self.tr("Click to start processing")
        )

        # 添加卡片到布局
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        """
        添加卡片到布局
        """
        self.viewLayout.addWidget(self.fastE2EInputFileCard)
        self.viewLayout.addWidget(self.fastE2EOutputFolderCard)
        self.viewLayout.addWidget(self.directionCard)
        self.viewLayout.addWidget(self.downloadTemplateCard)
        self.viewLayout.addWidget(self.fastE2EExecuteCard)

        self._adjustViewSize()

    def connectSignals(self):
        """
        连接信号
        """
        # 按钮 | 选择文件夹
        self.fastE2EOutputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.fastE2EOutputFolder, self.fastE2EOutputFolderCard)
        )

        # 按钮 | 选择文件
        self.fastE2EInputFileCard.clicked.connect(
            lambda: self.__onChooseFileClicked(cfg.fastE2EInputFile, self.fastE2EInputFileCard)
        )

        # Execute button connection
        self.fastE2EExecuteCard.clicked.connect(self.__onExecuteFastE2EClicked)

        # 下载模板按钮连接
        self.downloadTemplateCard.clicked.connect(self.__onDownloadTemplateClicked)

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
        file, _ = QFileDialog.getOpenFileName(self, self.tr("Choose file"), cfg.get(config_item), "Excel Files (*.xlsx);;ARXML Files (*.arxml)")
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
        # 使用 MessageBoxBase 创建输入对话框
        class InputDialog(MessageBoxBase):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.titleLabel = SubtitleLabel(title, self)
                self.viewLayout.addWidget(self.titleLabel)
                self.lineEdit = LineEdit(self)
                self.lineEdit.setText(current_value)
                self.lineEdit.setClearButtonEnabled(True)
                self.viewLayout.addWidget(self.lineEdit)
                self.yesButton.setText(self.tr("OK"))
                self.cancelButton.setText(self.tr("Cancel"))
                self.widget.setMinimumWidth(300)
            
            def get_value(self):
                return self.lineEdit.text()
        
        dialog = InputDialog(self.window())
        if dialog.exec():
            value = dialog.get_value()
            if value != current_value:
                cfg.set(config_item, value)
                card.setContent(value)

    def __onExecuteFastE2EClicked(self):
        """
        执行FastE2E处理
        """
        try:
            # 显示结果
            message = self.tr("Processing completed!\n")
            Notification.success(
                self.tr("Success"),
                message,
                parent=self
            )
        except Exception as e:
            Notification.error(
                self.tr("Error"),
                self.tr(f"Processing failed: {str(e)}"),
                parent=self
            )

    def __onDownloadTemplateClicked(self):
        """
        下载模板文件
        """
        try:
            # 下载模板
            template_name = "E2E_Template.xlsx"
            save_path = downloadTemplate(template_name)
            
            if save_path:
                # 显示成功消息
                message = self.tr(f"Template downloaded successfully!\nSaved to: {save_path}")
                Notification.success(
                    self.tr("Success"),
                    message,
                    parent=self
                )
            else:
                # 显示取消或失败消息
                message = self.tr("Template download cancelled or failed.")
                Notification.warning(
                    self.tr("Warning"),
                    message,
                    parent=self
                )
        except Exception as e:
            Notification.error(
                self.tr("Error"),
                self.tr(f"Failed to download template: {str(e)}"),
                parent=self
            )

    def __onComboBoxChanged(self, index):
        """
        处理ComboBox选择变化，控制卡片的可见性和启用状态

        Args:
            index: 选中项的索引
        """
        # Save selected option to config
        cfg.set(cfg.fastE2ESelectedOption, index)

        if index == 0:  # Option 1
            # 显示所有卡片并启用
            self.fastE2EOutputFolderCard.setVisible(True)
            self.fastE2EInputFileCard.setVisible(True)
            self.directionCard.setVisible(True)
            self.fastE2EExecuteCard.setVisible(True)
            self.fastE2EOutputFolderCard.setEnabled(True)
            self.fastE2EInputFileCard.setEnabled(True)
            self.directionCard.setEnabled(True)
            self.fastE2EExecuteCard.setEnabled(True)
        elif index == 1:  # Option 2
            # 只显示输入文件夹卡片，禁用执行按钮
            self.fastE2EOutputFolderCard.setVisible(True)
            self.fastE2EInputFileCard.setVisible(True)
            self.directionCard.setVisible(True)
            self.fastE2EExecuteCard.setVisible(False)
            self.fastE2EOutputFolderCard.setEnabled(True)
            self.fastE2EInputFileCard.setEnabled(True)
            self.directionCard.setEnabled(True)
        elif index == 2:  # Option 3
            # 显示所有卡片但禁用
            self.fastE2EOutputFolderCard.setVisible(True)
            self.fastE2EInputFileCard.setVisible(True)
            self.directionCard.setVisible(True)
            self.fastE2EExecuteCard.setVisible(True)
            self.fastE2EOutputFolderCard.setEnabled(False)
            self.fastE2EInputFileCard.setEnabled(False)
            self.directionCard.setEnabled(False)
            self.fastE2EExecuteCard.setEnabled(False)

        # 调整布局大小
        self._adjustViewSize()
