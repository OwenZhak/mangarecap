from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QTextEdit,
    QProgressBar,
)

from app.controller import Controller


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.controller = Controller()

        self.setWindowTitle("Manga Recap Studio")
        self.resize(950, 700)

        self.build_ui()

        self.load_settings()

        self.log_message("Application started.")

    # --------------------------------------------------

    def build_ui(self):

        layout = QVBoxLayout()

        # ---------------- Audio ----------------

        layout.addWidget(QLabel("Voiceover"))

        row = QHBoxLayout()

        self.audio_path = QLineEdit()
        self.audio_path.setPlaceholderText("Select voiceover...")

        audio_button = QPushButton("Browse")

        row.addWidget(self.audio_path)
        row.addWidget(audio_button)

        layout.addLayout(row)

        # ---------------- Images ----------------

        layout.addWidget(QLabel("Images Folder"))

        row = QHBoxLayout()

        self.images_path = QLineEdit()
        self.images_path.setPlaceholderText("Select images folder...")

        images_button = QPushButton("Browse")

        row.addWidget(self.images_path)
        row.addWidget(images_button)

        layout.addLayout(row)

        # ---------------- Output ----------------

        layout.addWidget(QLabel("Output Folder"))

        row = QHBoxLayout()

        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Select output folder...")

        output_button = QPushButton("Browse")

        row.addWidget(self.output_path)
        row.addWidget(output_button)

        layout.addLayout(row)

        # ---------------- Status ----------------

        self.status = QLabel("Ready")

        layout.addWidget(self.status)

        # ---------------- Progress ----------------

        self.progress = QProgressBar()

        self.progress.setValue(0)

        layout.addWidget(self.progress)

        # ---------------- Log ----------------

        self.log = QTextEdit()

        self.log.setReadOnly(True)

        layout.addWidget(self.log)

        # ---------------- Generate ----------------

        self.generate = QPushButton("Generate Project")

        layout.addWidget(self.generate)

        self.setLayout(layout)

        # Connections

        audio_button.clicked.connect(
            self.select_audio
        )

        images_button.clicked.connect(
            self.select_images
        )

        output_button.clicked.connect(
            self.select_output
        )

        self.generate.clicked.connect(
            self.generate_project
        )

    # --------------------------------------------------

    def select_audio(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Voiceover",
            "",
            "Audio (*.mp3 *.wav *.m4a)"
        )

        if filename:
            self.audio_path.setText(filename)

    # --------------------------------------------------

    def select_images(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Images Folder"
        )

        if folder:
            self.images_path.setText(folder)

    # --------------------------------------------------

    def select_output(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder"
        )

        if folder:
            self.output_path.setText(folder)

    # --------------------------------------------------

    def generate_project(self):

        self.progress.setValue(0)

        self.status.setText("Validating...")

        self.log.clear()

        errors = self.controller.start_job(
            self.audio_path.text(),
            self.images_path.text(),
            self.output_path.text(),
        )

        if errors:

            self.status.setText("Validation Failed")

            for error in errors:
                self.log_message(error)

            return

        self.status.setText("Processing...")

        self.controller.worker.progress.connect(
            self.progress.setValue
        )

        self.controller.worker.status.connect(
            self.status.setText
        )

        self.controller.worker.log.connect(
            self.log_message
        )

        self.controller.worker.error.connect(
            self.log_message
        )

        self.controller.worker.finished.connect(
            self.project_finished
        )

    # --------------------------------------------------

    def project_finished(self):

        self.status.setText("Finished")

        self.progress.setValue(100)

        self.log_message("Project complete.")

    # --------------------------------------------------

    def log_message(self, message):

        self.log.append(message)

    # --------------------------------------------------

    def load_settings(self):

        paths = self.controller.load_paths()

        self.audio_path.setText(
            paths["audio"]
        )

        self.images_path.setText(
            paths["images"]
        )

        self.output_path.setText(
            paths["output"]
        )

    # --------------------------------------------------

    def save_settings(self):

        self.controller.save_paths(
            self.audio_path.text(),
            self.images_path.text(),
            self.output_path.text(),
        )

    # --------------------------------------------------

    def closeEvent(self, event):

        self.save_settings()

        event.accept()