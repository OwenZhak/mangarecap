import sys

from PySide6.QtWidgets import QApplication

import qdarktheme

from ui.main_window import MainWindow


def run():
    app = QApplication(sys.argv)

    qdarktheme.setup_theme()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())