# coding:utf-8
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme, SettingCard, PushButton,
                            ExpandSettingCard)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QLabel, QFileDialog, QHBoxLayout

from app.common.background_manager import get_background_manager
from app.common.config import cfg, isWin11
from app.common.setting import HELP_URL, FEEDBACK_URL, AUTHOR, VERSION, YEAR
from app.common.signal_bus import signalBus
from app.common.style_sheet import StyleSheet


class BackgroundImageCard(SettingCard):
    """ Custom setting card with select and clear buttons for background image """

    def __init__(self, title, content, icon, parent=None):
        super().__init__(icon, title, content, parent)

        # Create buttons
        self.selectButton = PushButton(self.tr('Select image'), self)
        self.clearButton = PushButton(self.tr('Clear'), self)

        # Create button layout
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(10)
        self.buttonLayout.addWidget(self.selectButton)
        self.buttonLayout.addWidget(self.clearButton)

        # Add button layout to the card
        self.hBoxLayout.addLayout(self.buttonLayout)
        self.hBoxLayout.addSpacing(16)

        # Initialize display
        self._updateDisplay()

    def _updateDisplay(self):
        """ Update the card display based on current background image path """
        bg_path = cfg.get(cfg.backgroundImagePath)
        if bg_path:
            import os
            file_name = os.path.basename(bg_path)
            self.setContent(f"Selected: {file_name}")
            self.clearButton.setEnabled(True)
        else:
            self.setContent(self.tr('Choose a custom background image file'))
            self.clearButton.setEnabled(False)


class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        # initialize background manager
        self.backgroundManager = get_background_manager(cfg)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        # Project folders
        self.projectInThisPCGroup = SettingCardGroup(self.tr("Project on this PC"), self.scrollWidget)
        self.projectFolderCard = FolderListSettingCard(
            cfg.projectFolders,
            self.tr("Local Project library"),
            directory=QStandardPaths.writableLocation(QStandardPaths.MusicLocation),
            parent=self.projectInThisPCGroup
        )
        self.downloadFolderCard = PushSettingCard(
            self.tr('Choose folder'),
            FIF.DOWNLOAD,
            self.tr("Project directory"),
            cfg.get(cfg.downloadFolder),
            self.projectInThisPCGroup
        )

        # personalization
        self.personalGroup = SettingCardGroup(self.tr('Personalization'), self.scrollWidget)
        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr('Mica effect'),
            self.tr('Apply semi transparent to windows and surfaces'),
            cfg.micaEnabled,
            self.personalGroup
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr('Application theme'),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr('Light'), self.tr('Dark'),
                self.tr('Use system setting')
            ],
            parent=self.personalGroup
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr('Theme color'),
            self.tr('Change the theme color of you application'),
            self.personalGroup
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                self.tr("Use system setting")
            ],
            parent=self.personalGroup
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr('Language'),
            self.tr('Set your preferred language for UI'),
            texts=['简体中文', '繁體中文', 'English', self.tr('Use system setting')],
            parent=self.personalGroup
        )
        # background settings
        self.backgroundGroupCard = ExpandSettingCard(
            FIF.PHOTO,
            self.tr('Background'),
            self.tr('Customize application background settings'),
            self.scrollWidget)
        self.backgroundEnabledCard = SwitchSettingCard(
            FIF.PHOTO,
            self.tr('Background image'),
            self.tr('Enable custom background image for the application'),
            cfg.backgroundImageEnabled,
            self.backgroundGroupCard
        )
        self.backgroundImageCard = BackgroundImageCard(
            self.tr('Background image path'),
            self.tr('Choose a custom background image file'),
            FIF.FOLDER,
            self.backgroundGroupCard
        )
        self.backgroundOpacityCard = RangeSettingCard(
            cfg.backgroundOpacity,
            FIF.TRANSPARENT,
            self.tr('Background opacity'),
            self.tr('Adjust the opacity of the background image (0-100%)'),
            self.backgroundGroupCard
        )
        self.backgroundBlurCard = RangeSettingCard(
            cfg.backgroundBlurRadius,
            FIF.BRUSH,
            self.tr('Background blur'),
            self.tr('Adjust the blur radius of the background image (0-50px)'),
            self.backgroundGroupCard
        )
        self.backgroundDisplayModeCard = ComboBoxSettingCard(
            cfg.backgroundDisplayMode,
            FIF.LAYOUT,
            self.tr('Display mode'),
            self.tr('Choose how the background image is displayed'),
            texts=[
                self.tr('Stretch'), self.tr('Keep Aspect Ratio'),
                self.tr('Tile'), self.tr('Original Size'), self.tr('Fit Window')
            ],
            parent=self.backgroundGroupCard
        )

        # material
        self.materialGroup = SettingCardGroup(self.tr('Material'), self.scrollWidget)
        self.blurRadiusCard = RangeSettingCard(
            cfg.blurRadius,
            FIF.ALBUM,
            self.tr('Acrylic blur radius'),
            self.tr('The greater the radius, the more blurred the image'),
            self.materialGroup
        )

        # Application
        self.appGroup = SettingCardGroup(self.tr('Application settings'), self.scrollWidget)
        self.betaCard = SwitchSettingCard(
            FIF.DEVELOPER_TOOLS,
            self.tr('Beta experimental features'),
            self.tr('When turned on, experimental features will be enabled'),
            configItem=cfg.beta,
            parent=self.appGroup
        )
        self.closeWindowActionCard = ComboBoxSettingCard(
            cfg.close_window_action,
            FIF.MINIMIZE,
            self.tr('when close windows'),
            self.tr('Select the default behavior when closing the window, or you can be asked by the dialog box on closing'),
            texts = [
                self.tr("ask"),
                self.tr("minimize"),
                self.tr("close")
            ],
            parent = self.appGroup
        )

        # update software
        self.updateSoftwareGroup = SettingCardGroup(self.tr("Software update"), self.scrollWidget)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr('Check for updates when the application starts'),
            self.tr('The new version will be more stable and have more features'),
            configItem=cfg.checkUpdateAtStartUp,
            parent=self.updateSoftwareGroup
        )

        # About
        self.aboutGroup = SettingCardGroup(self.tr('About'), self.scrollWidget)
        self.helpCard = HyperlinkCard(
            HELP_URL,
            self.tr('Open help page'),
            FIF.HELP,
            self.tr('Help'),
            self.tr(
                'Discover new features and learn useful tips about FastXTeam/FastX-Gui'),
            self.aboutGroup
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr('Provide feedback'),
            FIF.FEEDBACK,
            self.tr('Provide feedback'),
            self.tr('Help us improve FastXTeam/FastX-Gui by providing feedback'),
            self.aboutGroup
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr('Check update'),
            ":/app/images/logo.png",
            self.tr('About'),
            '© ' + self.tr('Copyright') + f" {YEAR}, {AUTHOR}. " +
            self.tr('Version') + " v" + VERSION,
            self.aboutGroup
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)

        # initialize style sheet
        self.__setQss()

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __setQss(self):
        """ set style sheet """
        # initialize style sheet
        self.setObjectName('settingInterface')
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        StyleSheet.SETTING_INTERFACE.apply(self)
        # micaCard
        self.micaCard.setEnabled(isWin11())
        # initialize background cards state
        self.__updateBackgroundCardsState()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # add cards to group
        self.projectInThisPCGroup.addSettingCard(self.projectFolderCard)
        self.projectInThisPCGroup.addSettingCard(self.downloadFolderCard)

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)
        self.personalGroup.addSettingCard(self.backgroundGroupCard)
        # Add widgets to expand card view instead of as setting cards
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundEnabledCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundImageCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundOpacityCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundBlurCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundDisplayModeCard)
        self.backgroundGroupCard._adjustViewSize()

        self.materialGroup.addSettingCard(self.blurRadiusCard)
        self.appGroup.addSettingCard(self.betaCard)
        self.appGroup.addSettingCard(self.closeWindowActionCard)
        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.projectInThisPCGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.appGroup)
        self.expandLayout.addWidget(self.materialGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)
        self._betaEnable() if cfg.beta.value else None   #Beta


    def _createBetaSetting(self):
        self.BetaGroup = SettingCardGroup(self.tr('Beta'), self.scrollWidget)
        self.debug_Card = SwitchSettingCard(
                FIF.CODE,
                self.tr('Debug Mode'),
                self.tr('The global exception capture will be disabled, and there will be outputs in the commandline.(Code Running Only)'),
                configItem=cfg.debug_card,
                parent=self.BetaGroup
        )

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return
        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def _betaEnable(self):
        if cfg.beta.value:
            self._createBetaSetting()
            self.expandLayout.addWidget(self.BetaGroup)
            self.BetaGroup.addSettingCard(self.debug_Card)
            self.debug_Card.setVisible(True)
            self.BetaGroup.setVisible(True)
        else:
            self.debug_Card.setValue(False)
            self.debug_Card.setVisible(False)
            self.BetaGroup.setVisible(False)

    def __onBackgroundEnabledChanged(self, isChecked: bool):
        """ Handle background image enable/disable """
        cfg.set(cfg.backgroundImageEnabled, isChecked)
        self.backgroundManager.update_background()
        self.__updateBackgroundCardsState()
        self.__updateBackgroundPreview()

    def __onSelectBackgroundImage(self):
        """ Handle background image selection """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr('Select background image'),
            '',
            self.tr('Image files (*.jpg *.jpeg *.png *.bmp *.gif *.webp)')
        )

        if file_path:
            cfg.set(cfg.backgroundImagePath, file_path)
            self.backgroundManager.update_background()
            self.backgroundImageCard._updateDisplay()
            self.__updateBackgroundPreview()

    def __onClearBackgroundImage(self):
        """ Handle background image clearing """
        cfg.set(cfg.backgroundImagePath, "")
        self.backgroundManager.update_background()
        self.backgroundImageCard._updateDisplay()
        self.__updateBackgroundPreview()

    def __onBackgroundOpacityChanged(self, value: int):
        """ Handle background opacity change """
        cfg.set(cfg.backgroundOpacity, value)
        self.backgroundManager.update_background()
        self.__updateBackgroundPreview()

    def __onBackgroundBlurChanged(self, value: int):
        """ Handle background blur radius change """
        cfg.set(cfg.backgroundBlurRadius, value)
        self.backgroundManager.update_background()
        self.__updateBackgroundPreview()

    def __onBackgroundDisplayModeChanged(self, index: int):
        """ Handle background display mode change """
        mode = self.backgroundDisplayModeCard.comboBox.itemData(index)
        cfg.set(cfg.backgroundDisplayMode, mode)
        self.backgroundManager.update_background()
        self.__updateBackgroundPreview()

    def __updateBackgroundPreview(self):
        """ Update background preview in main window """
        parent_window = self.window()
        if hasattr(parent_window, 'update'):
            parent_window.update()  # Trigger repaint to show background changes

    def __updateBackgroundCardsState(self):
        """ Update the enabled state of background setting cards """
        is_background_enabled = cfg.get(cfg.backgroundImageEnabled)

        # Enable/disable background related cards based on background enabled state
        self.backgroundImageCard.setEnabled(is_background_enabled)
        self.backgroundOpacityCard.setEnabled(is_background_enabled)
        self.backgroundBlurCard.setEnabled(is_background_enabled)
        self.backgroundDisplayModeCard.setEnabled(is_background_enabled)

        # Update display when background is enabled/disabled
        if hasattr(self.backgroundImageCard, '_updateDisplay'):
            self.backgroundImageCard._updateDisplay()

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # project in the pc
        self.downloadFolderCard.clicked.connect(self.__onDownloadFolderCardClicked)

        # personalization
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        # background settings
        self.backgroundEnabledCard.checkedChanged.connect(self.__onBackgroundEnabledChanged)
        self.backgroundImageCard.selectButton.clicked.connect(self.__onSelectBackgroundImage)
        self.backgroundImageCard.clearButton.clicked.connect(self.__onClearBackgroundImage)
        self.backgroundOpacityCard.valueChanged.connect(self.__onBackgroundOpacityChanged)
        self.backgroundBlurCard.valueChanged.connect(self.__onBackgroundBlurChanged)
        self.backgroundDisplayModeCard.comboBox.currentIndexChanged.connect(self.__onBackgroundDisplayModeChanged)

        # application
        self.betaCard.checkedChanged.connect(self._betaEnable)

        # check update
        self.aboutCard.clicked.connect(signalBus.checkUpdateSig)

        # about
        self.feedbackCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))