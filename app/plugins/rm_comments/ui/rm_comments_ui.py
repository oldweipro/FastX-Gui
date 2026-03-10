from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QInputDialog, QMessageBox, QVBoxLayout, QWidget
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, ScrollArea, FluentIconBase, MessageBox, MessageBoxBase, SubtitleLabel, LineEdit, CaptionLabel,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon
from ..core.rm_comments_core import RmCommentsCore


class RmCommentsUI(ExpandSettingCard):
    """Remove Comments UI class"""

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
            title = self.tr("Remove Python Code Comment")
        # 如果 content 为空字符串，设置默认标题
        if content is None:
            content = self.tr("To apply software copyrights, need supply whole code without comments")
        super().__init__(icon, title, content, parent)
        self.core = RmCommentsCore()
        self.__initCards()
        self.connectSignals()

    def __initCards(self):
        """
        初始化卡片
        """

        # 文件夹选择卡片
        self.rmCodeCommentsInputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Input Directory"),
            cfg.get(cfg.rmCommentsInputFolder)
        )
        self.rmCodeCommentsOutputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Output Directory"),
            cfg.get(cfg.rmCommentsOutputFolder)
        )

        # RemoveComments options
        self.rmCodeCommentsRemoveCommentsCard = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("Remove Comments"),
            self.tr("Remove single line comments"),
            cfg.rmCommentsRemoveComments
        )
        self.rmCodeCommentsRemoveDocstringsCard = SwitchSettingCard(
            FIF.EDIT,
            self.tr("Remove Docstrings"),
            self.tr("Remove module, class and function docstrings"),
            cfg.rmCommentsRemoveDocstrings
        )
        self.rmCodeCommentsRemoveEmptyLinesCard = SwitchSettingCard(
            FIF.LAYOUT,
            self.tr("Remove Empty Lines"),
            self.tr("Remove empty lines from code"),
            cfg.rmCommentsRemoveEmptyLines
        )
        self.rmCodeCommentsKeepTripleQuotesCard = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("Keep Triple Quotes"),
            self.tr("Keep triple quoted strings"),
            cfg.rmCommentsKeepTripleQuotes
        )
        self.rmCodeCommentsRecursiveCard = SwitchSettingCard(
            FIF.SYNC,
            self.tr("Recursive"),
            self.tr("Process subdirectories recursively"),
            cfg.rmCommentsRecursive
        )

        # Output suffix setting
        self.rmCodeCommentsOutputSuffixCard = PushSettingCard(
            self.tr("Set suffix"),
            FIF.EDIT,
            self.tr("Output File Suffix"),
            cfg.get(cfg.rmCommentsOutputSuffix)
        )

        # Exclude files setting
        self.rmCodeCommentsExcludeFilesCard = PushSettingCard(
            self.tr("Set exclude files"),
            FIF.FILTER,
            self.tr("Exclude Files (comma separated)"),
            cfg.get(cfg.rmCommentsExcludeFiles)
        )

        # Exclude patterns setting
        self.rmCodeCommentsExcludePatternsCard = PushSettingCard(
            self.tr("Set exclude patterns"),
            FIF.FILTER,
            self.tr("Exclude Patterns (comma separated)"),
            cfg.get(cfg.rmCommentsExcludePatterns)
        )

        # Execute button
        self.rmCodeCommentsExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute Code Comment Removal"),
            self.tr("Click to start processing")
        )

        # 添加卡片到布局
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        """
        添加卡片到布局
        """
        self.columnLayout = QHBoxLayout()
        self.rowLeftLayout = QVBoxLayout()
        self.rowRightLayout = QVBoxLayout()

        self.viewLayout.addLayout(self.columnLayout)
        self.columnLayout.addLayout(self.rowLeftLayout)
        self.columnLayout.addLayout(self.rowRightLayout)

        self.rowLeftLayout.addWidget(self.rmCodeCommentsInputFolderCard)
        self.rowLeftLayout.addWidget(self.rmCodeCommentsOutputFolderCard)

        # Add option cards
        self.rowLeftLayout.addWidget(self.rmCodeCommentsRemoveCommentsCard)
        self.rowLeftLayout.addWidget(self.rmCodeCommentsRemoveDocstringsCard)
        self.rowLeftLayout.addWidget(self.rmCodeCommentsRemoveEmptyLinesCard)

        self.rowRightLayout.addWidget(self.rmCodeCommentsKeepTripleQuotesCard)
        self.rowRightLayout.addWidget(self.rmCodeCommentsRecursiveCard)

        # Add input cards
        self.rowRightLayout.addWidget(self.rmCodeCommentsOutputSuffixCard)
        self.rowRightLayout.addWidget(self.rmCodeCommentsExcludeFilesCard)
        self.rowRightLayout.addWidget(self.rmCodeCommentsExcludePatternsCard)

        # Add execute button
        self.viewLayout.addWidget(self.rmCodeCommentsExecuteCard)

        self._adjustViewSize()

    def connectSignals(self):
        """
        连接信号
        """
        # 按钮 | 去除Python代码备注,空行
        self.rmCodeCommentsInputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.rmCommentsInputFolder, self.rmCodeCommentsInputFolderCard)
        )
        self.rmCodeCommentsOutputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.rmCommentsOutputFolder, self.rmCodeCommentsOutputFolderCard)
        )

        # RemoveComments options connections
        self.rmCodeCommentsRemoveCommentsCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRemoveComments, checked)
        )
        self.rmCodeCommentsRemoveDocstringsCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRemoveDocstrings, checked)
        )
        self.rmCodeCommentsRemoveEmptyLinesCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRemoveEmptyLines, checked)
        )
        self.rmCodeCommentsKeepTripleQuotesCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsKeepTripleQuotes, checked)
        )
        self.rmCodeCommentsRecursiveCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRecursive, checked)
        )

        # Input cards connections
        self.rmCodeCommentsOutputSuffixCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.rmCommentsOutputSuffix, self.rmCodeCommentsOutputSuffixCard, self.tr("Set Output Suffix"))
        )
        self.rmCodeCommentsExcludeFilesCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.rmCommentsExcludeFiles, self.rmCodeCommentsExcludeFilesCard, self.tr("Set Exclude Files"))
        )
        self.rmCodeCommentsExcludePatternsCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.rmCommentsExcludePatterns, self.rmCodeCommentsExcludePatternsCard, self.tr("Set Exclude Patterns"))
        )

        # Execute button connection
        self.rmCodeCommentsExecuteCard.clicked.connect(self.__onExecuteRmCommentsClicked)

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

    def createInputDialog(self, title, default_value=""):
        """
        创建输入对话框
        Args:
            title: 对话框标题
            default_value: 默认值
        """
        class InputDialog(MessageBoxBase):
            def __init__(self, parent=None):
                super().__init__(parent)
                # 标题
                self.titleLabel = SubtitleLabel(title, self)
                # 输入框
                self.lineEdit = LineEdit(self)
                self.lineEdit.setText(default_value)
                self.lineEdit.setPlaceholderText(self.tr("请输入..."))
                self.lineEdit.setClearButtonEnabled(True)
                # 添加到布局
                self.viewLayout.addWidget(self.titleLabel)
                self.viewLayout.addWidget(self.lineEdit)
                # 设置按钮文本
                self.yesButton.setText(self.tr("确定"))
                self.cancelButton.setText(self.tr("取消"))
                # 设置最小宽度
                self.widget.setMinimumWidth(600)
                # 连接信号
                self.lineEdit.textChanged.connect(self.validate)
            def validate(self):
                """验证输入（可选重写）"""
                # 这里可以添加输入验证逻辑
                # 返回 True 表示验证通过，False 表示验证失败
                return True
        return InputDialog(self.window())

    def __onSetValueClicked(self, config_item, card, title):
        """
        通用值设置方法

        Args:
            config_item: 配置项
            card: 卡片对象
            title: 对话框标题
        """
        # 获取当前值
        current_value = cfg.get(config_item)
        # 创建自定义输入对话框
        dialog = self.createInputDialog(title, current_value)
        if dialog.exec():
            new_value = dialog.lineEdit.text()
            if new_value != current_value:
                cfg.set(config_item, new_value)
                card.setContent(new_value)

    def __onExecuteRmCommentsClicked(self):
        """
        执行代码清理
        """
        try:
            # 获取配置
            input_path = cfg.get(cfg.rmCommentsInputFolder)
            output_path = cfg.get(cfg.rmCommentsOutputFolder)
            remove_comments = cfg.get(cfg.rmCommentsRemoveComments)
            remove_docstrings = cfg.get(cfg.rmCommentsRemoveDocstrings)
            remove_empty_lines = cfg.get(cfg.rmCommentsRemoveEmptyLines)
            keep_triple_quotes = cfg.get(cfg.rmCommentsKeepTripleQuotes)
            output_suffix = cfg.get(cfg.rmCommentsOutputSuffix)
            recursive = cfg.get(cfg.rmCommentsRecursive)
            exclude_files = [f.strip() for f in cfg.get(cfg.rmCommentsExcludeFiles).split(',') if f.strip()]
            exclude_patterns = [p.strip() for p in cfg.get(cfg.rmCommentsExcludePatterns).split(',') if p.strip()]

            # 执行清理
            stats = self.core.execute(
                input_path=input_path,
                output_path=output_path,
                remove_comments=remove_comments,
                remove_docstrings=remove_docstrings,
                remove_empty_lines=remove_empty_lines,
                keep_triple_quotes=keep_triple_quotes,
                output_suffix=output_suffix,
                recursive=recursive,
                exclude_files=exclude_files,
                exclude_patterns=exclude_patterns
            )

            # 显示结果
            message = self.tr("Processing completed!\n")
            message += self.tr(f"Total files: {stats['total_files']}\n")
            message += self.tr(f"Processed: {stats['processed']}\n")
            message += self.tr(f"Skipped: {stats['skipped']}\n")
            message += self.tr(f"Errors: {stats['errors']}")

            w = MessageBox(self.tr("Success"), message, self.window())
            # close the message box when mask is clicked
            w.setClosableOnMaskClicked(True)
            # enable dragging
            w.setDraggable(True)
            w.exec_()

        except Exception as e:
            MessageBox(self.tr("Error"), self.tr(f"Processing failed: {str(e)}"), self.window()).exec_()
