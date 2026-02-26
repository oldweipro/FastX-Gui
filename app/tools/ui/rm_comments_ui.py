from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QInputDialog, QMessageBox, QVBoxLayout, QWidget
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, ScrollArea,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon
from app.tools.core.rm_comments_core import RmCommentsCore


class RmCommentsUI(ScrollArea):
    """Remove Comments UI class"""

    def __init__(self, parent=None):
        """
        初始化

        Args:
            parent: 父级窗口
        """
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.core = RmCommentsCore()
        self.__initCards()

    def __initCards(self):
        """
        初始化卡片
        """
        # 创建主卡片
        self.rmCodeCommentsGroupCard = ExpandSettingCard(
            UnicodeIcon.get_icon_by_name("ic_fluent_comment_dismiss_24_regular"),
            self.tr("Remove Python Code Comment"),
            self.tr("To apply software copyrights, need supply whole code without comments"),
            self.view,
        )

        # 文件夹选择卡片
        self.rmCodeCommentsInputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Input Directory"),
            cfg.get(cfg.RmCommentsInputFolder),
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsOutputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Output Directory"),
            cfg.get(cfg.RmCommentsOutputFolder),
            self.rmCodeCommentsGroupCard,
        )

        # RemoveComments options
        self.rmCodeCommentsRemoveCommentsCard = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("Remove Comments"),
            self.tr("Remove single line comments"),
            cfg.RmCommentsRemoveComments,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsRemoveDocstringsCard = SwitchSettingCard(
            FIF.EDIT,
            self.tr("Remove Docstrings"),
            self.tr("Remove module, class and function docstrings"),
            cfg.RmCommentsRemoveDocstrings,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsRemoveEmptyLinesCard = SwitchSettingCard(
            FIF.LAYOUT,
            self.tr("Remove Empty Lines"),
            self.tr("Remove empty lines from code"),
            cfg.RmCommentsRemoveEmptyLines,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsKeepTripleQuotesCard = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("Keep Triple Quotes"),
            self.tr("Keep triple quoted strings"),
            cfg.RmCommentsKeepTripleQuotes,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsRecursiveCard = SwitchSettingCard(
            FIF.SYNC,
            self.tr("Recursive"),
            self.tr("Process subdirectories recursively"),
            cfg.RmCommentsRecursive,
            self.rmCodeCommentsGroupCard,
        )

        # Output suffix setting
        self.rmCodeCommentsOutputSuffixCard = PushSettingCard(
            self.tr("Set suffix"),
            FIF.EDIT,
            self.tr("Output File Suffix"),
            cfg.get(cfg.RmCommentsOutputSuffix),
            self.rmCodeCommentsGroupCard,
        )

        # Exclude files setting
        self.rmCodeCommentsExcludeFilesCard = PushSettingCard(
            self.tr("Set exclude files"),
            FIF.FILTER,
            self.tr("Exclude Files (comma separated)"),
            cfg.get(cfg.RmCommentsExcludeFiles),
            self.rmCodeCommentsGroupCard,
        )

        # Exclude patterns setting
        self.rmCodeCommentsExcludePatternsCard = PushSettingCard(
            self.tr("Set exclude patterns"),
            FIF.FILTER,
            self.tr("Exclude Patterns (comma separated)"),
            cfg.get(cfg.RmCommentsExcludePatterns),
            self.rmCodeCommentsGroupCard,
        )

        # Execute button
        self.rmCodeCommentsExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute Code Comment Removal"),
            self.tr("Click to start processing"),
            self.rmCodeCommentsGroupCard,
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
        self.rmCodeCommentsGroupCard.viewLayout.addLayout(self.columnLayout)
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
        self.rmCodeCommentsGroupCard.viewLayout.addWidget(self.rmCodeCommentsExecuteCard)

        self.rmCodeCommentsGroupCard._adjustViewSize()

    def connectSignals(self):
        """
        连接信号
        """
        # 按钮 | 去除Python代码备注,空行
        self.rmCodeCommentsInputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.RmCommentsInputFolder, self.rmCodeCommentsInputFolderCard)
        )
        self.rmCodeCommentsOutputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.RmCommentsOutputFolder, self.rmCodeCommentsOutputFolderCard)
        )

        # RemoveComments options connections
        self.rmCodeCommentsRemoveCommentsCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.RmCommentsRemoveComments, checked)
        )
        self.rmCodeCommentsRemoveDocstringsCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.RmCommentsRemoveDocstrings, checked)
        )
        self.rmCodeCommentsRemoveEmptyLinesCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.RmCommentsRemoveEmptyLines, checked)
        )
        self.rmCodeCommentsKeepTripleQuotesCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.RmCommentsKeepTripleQuotes, checked)
        )
        self.rmCodeCommentsRecursiveCard.checkedChanged.connect(
            lambda checked: cfg.set(cfg.RmCommentsRecursive, checked)
        )

        # Input cards connections
        self.rmCodeCommentsOutputSuffixCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.RmCommentsOutputSuffix, self.rmCodeCommentsOutputSuffixCard, self.tr("Set Output Suffix"))
        )
        self.rmCodeCommentsExcludeFilesCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.RmCommentsExcludeFiles, self.rmCodeCommentsExcludeFilesCard, self.tr("Set Exclude Files"))
        )
        self.rmCodeCommentsExcludePatternsCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.RmCommentsExcludePatterns, self.rmCodeCommentsExcludePatternsCard, self.tr("Set Exclude Patterns"))
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
        folder = QFileDialog.getExistingDirectory(self.parent, self.tr("Choose folder"), "./")
        if not folder or cfg.get(config_item) == folder:
            return
        cfg.set(config_item, folder)
        card.setContent(folder)

    def __onSetValueClicked(self, config_item, card, title):
        """
        通用值设置方法

        Args:
            config_item: 配置项
            card: 卡片对象
            title: 对话框标题
        """
        current_value = cfg.get(config_item)
        value, ok = QInputDialog.getText(self.parent, title, title, text=current_value)
        if ok and value != current_value:
            cfg.set(config_item, value)
            card.setContent(value)

    def __onExecuteRmCommentsClicked(self):
        """
        执行代码清理
        """
        try:
            # 获取配置
            input_path = cfg.get(cfg.RmCommentsInputFolder)
            output_path = cfg.get(cfg.RmCommentsOutputFolder)
            remove_comments = cfg.get(cfg.RmCommentsRemoveComments)
            remove_docstrings = cfg.get(cfg.RmCommentsRemoveDocstrings)
            remove_empty_lines = cfg.get(cfg.RmCommentsRemoveEmptyLines)
            keep_triple_quotes = cfg.get(cfg.RmCommentsKeepTripleQuotes)
            output_suffix = cfg.get(cfg.RmCommentsOutputSuffix)
            recursive = cfg.get(cfg.RmCommentsRecursive)
            exclude_files = [f.strip() for f in cfg.get(cfg.RmCommentsExcludeFiles).split(',') if f.strip()]
            exclude_patterns = [p.strip() for p in cfg.get(cfg.RmCommentsExcludePatterns).split(',') if p.strip()]

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

            QMessageBox.information(self.parent, self.tr("Success"), message)

        except Exception as e:
            QMessageBox.critical(self.parent, self.tr("Error"), self.tr(f"Processing failed: {str(e)}"))
