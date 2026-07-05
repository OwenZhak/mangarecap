from PySide6.QtCore import QSettings


class SettingsManager:
    def __init__(self):
        self.settings = QSettings("MangaRecapStudio", "MangaRecap")

    def get(self, key, default=""):
        return self.settings.value(key, default)

    def set(self, key, value):
        self.settings.setValue(key, value)