from PyQt5.QtWidgets import QInputDialog, QFileDialog, QMessageBox, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    ExpandSettingCard,
    PushSettingCard,
    SwitchSettingCard,
    FluentIcon as FIF, PrimaryPushSettingCard,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon
from app.tools.core.rm_comments_core import RmCommentsCore


class RmCommentsUI:
    """Remove Comments UI class"""

    def __init__(self, parent):
        """
        初始化

        Args:
            parent: 父级窗口
        """
        self.parent = parent
        self.core = RmCommentsCore()
        self.__initCards()

    def __initCards(self):
        """
        初始化卡片
        """
        # 创建主卡片
        self.rmCodeCommentsGroupCard = ExpandSettingCard(
            UnicodeIcon.get_icon_by_name("ic_fluent_comment_dismiss_24_regular"),
            self.parent.tr("Remove Python Code Comment"),
            self.parent.tr("To apply software copyrights, need supply whole code without comments"),
            self.parent.view,
        )

        # 文件夹选择卡片
        self.rmCodeCommentsInputFolderCard = PushSettingCard(
            self.parent.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.parent.tr("Project Input Directory"),
            cfg.get(cfg.RmCommentsInputFolder),
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsOutputFolderCard = PushSettingCard(
            self.parent.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.parent.tr("Project Output Directory"),
            cfg.get(cfg.RmCommentsOutputFolder),
            self.rmCodeCommentsGroupCard,
        )

        # RemoveComments options
        self.rmCodeCommentsRemoveCommentsCard = SwitchSettingCard(
            FIF.DOCUMENT,
            self.parent.tr("Remove Comments"),
            self.parent.tr("Remove single line comments"),
            cfg.RmCommentsRemoveComments,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsRemoveDocstringsCard = SwitchSettingCard(
            FIF.EDIT,
            self.parent.tr("Remove Docstrings"),
            self.parent.tr("Remove module, class and function docstrings"),
            cfg.RmCommentsRemoveDocstrings,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsRemoveEmptyLinesCard = SwitchSettingCard(
            FIF.LAYOUT,
            self.parent.tr("Remove Empty Lines"),
            self.parent.tr("Remove empty lines from code"),
            cfg.RmCommentsRemoveEmptyLines,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsKeepTripleQuotesCard = SwitchSettingCard(
            FIF.DOCUMENT,
            self.parent.tr("Keep Triple Quotes"),
            self.parent.tr("Keep triple quoted strings"),
            cfg.RmCommentsKeepTripleQuotes,
            self.rmCodeCommentsGroupCard,
        )
        self.rmCodeCommentsRecursiveCard = SwitchSettingCard(
            FIF.SYNC,
            self.parent.tr("Recursive"),
            self.parent.tr("Process subdirectories recursively"),
            cfg.RmCommentsRecursive,
            self.rmCodeCommentsGroupCard,
        )

        # Output suffix setting
        self.rmCodeCommentsOutputSuffixCard = PushSettingCard(
            self.parent.tr("Set suffix"),
            FIF.EDIT,
            self.parent.tr("Output File Suffix"),
            cfg.get(cfg.RmCommentsOutputSuffix),
            self.rmCodeCommentsGroupCard,
        )

        # Exclude files setting
        self.rmCodeCommentsExcludeFilesCard = PushSettingCard(
            self.parent.tr("Set exclude files"),
            FIF.FILTER,
            self.parent.tr("Exclude Files (comma separated)"),
            cfg.get(cfg.RmCommentsExcludeFiles),
            self.rmCodeCommentsGroupCard,
        )

        # Exclude patterns setting
        self.rmCodeCommentsExcludePatternsCard = PushSettingCard(
            self.parent.tr("Set exclude patterns"),
            FIF.FILTER,
            self.parent.tr("Exclude Patterns (comma separated)"),
            cfg.get(cfg.RmCommentsExcludePatterns),
            self.rmCodeCommentsGroupCard,
        )

        # Execute button
        self.rmCodeCommentsExecuteCard = PrimaryPushSettingCard(
            self.parent.tr("Execute"),
            FIF.PLAY,
            self.parent.tr("Execute Code Comment Removal"),
            self.parent.tr("Click to start processing"),
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
            lambda: self.__onSetValueClicked(cfg.RmCommentsOutputSuffix, self.rmCodeCommentsOutputSuffixCard, self.parent.tr("Set Output Suffix"))
        )
        self.rmCodeCommentsExcludeFilesCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.RmCommentsExcludeFiles, self.rmCodeCommentsExcludeFilesCard, self.parent.tr("Set Exclude Files"))
        )
        self.rmCodeCommentsExcludePatternsCard.clicked.connect(
            lambda: self.__onSetValueClicked(cfg.RmCommentsExcludePatterns, self.rmCodeCommentsExcludePatternsCard, self.parent.tr("Set Exclude Patterns"))
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
        folder = QFileDialog.getExistingDirectory(self.parent, self.parent.tr("Choose folder"), "./")
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
            message = self.parent.tr(f"Processing completed!\n")
            message += self.parent.tr(f"Total files: {stats['total_files']}\n")
            message += self.parent.tr(f"Processed: {stats['processed']}\n")
            message += self.parent.tr(f"Skipped: {stats['skipped']}\n")
            message += self.parent.tr(f"Errors: {stats['errors']}")

            QMessageBox.information(self.parent, self.parent.tr("Success"), message)

        except Exception as e:
            QMessageBox.critical(self.parent, self.parent.tr("Error"), self.parent.tr(f"Processing failed: {str(e)}"))