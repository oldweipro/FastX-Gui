from PySide6.QtCore import QObject


class Translator(QObject):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.home = self.tr("Home")
        self.app = self.tr("App")
        self.project = self.tr("Project")
        self.library = self.tr("Library")
        self.help = self.tr("Help")
        self.log = self.tr("Log")
        self.rte = self.tr("Rte")
        self.settings = self.tr("Settings")
        self.navigation = self.tr("Navigation")
