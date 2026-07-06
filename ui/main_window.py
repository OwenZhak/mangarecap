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

        self.resize(
            900,
            700,
        )

        self.build_ui()

        self.load_settings()

        self.log_message("Application started.")

    def build_ui(self):

        layout = QVBoxLayout()

        # ----------------------------------------
        # Audio
        # ----------------------------------------

        audio_layout = QHBoxLayout()

        audio_label = QLabel("Voiceover:")

        self.audio_path = QLineEdit()

        audio_button = QPushButton("Browse")

        audio_button.clicked.connect(
            self.select_audio
        )

        audio_layout.addWidget(audio_label)

        audio_layout.addWidget(self.audio_path)

        audio_layout.addWidget(audio_button)

        layout.addLayout(audio_layout)

        # ----------------------------------------
        # Images
        # ----------------------------------------

        images_layout = QHBoxLayout()

        images_label = QLabel("Images Folder:")

        self.images_path = QLineEdit()

        images_button = QPushButton("Browse")

        images_button.clicked.connect(
            self.select_images
        )

        images_layout.addWidget(images_label)

        images_layout.addWidget(self.images_path)

        images_layout.addWidget(images_button)

        layout.addLayout(images_layout)

        # ----------------------------------------
        # Output
        # ----------------------------------------

        output_layout = QHBoxLayout()

        output_label = QLabel("Output Folder:")

        self.output_path = QLineEdit()

        output_button = QPushButton("Browse")

        output_button.clicked.connect(
            self.select_output
        )

        output_layout.addWidget(output_label)

        output_layout.addWidget(self.output_path)

        output_layout.addWidget(output_button)

        layout.addLayout(output_layout)

        # ----------------------------------------
        # Status
        # ----------------------------------------

        self.status = QLabel("Ready")

        layout.addWidget(self.status)

        self.progress = QProgressBar()

        self.progress.setValue(0)

        layout.addWidget(self.progress)

        # ----------------------------------------
        # Log
        # ----------------------------------------

        self.log = QTextEdit()

        self.log.setReadOnly(True)

        layout.addWidget(self.log)

        # ----------------------------------------
        # Buttons
        # ----------------------------------------

        buttons_layout = QHBoxLayout()

        self.generate_button = QPushButton(
            "Generate Project"
        )

        self.generate_button.clicked.connect(
            self.generate_project
        )

        self.clear_output_button = QPushButton(
            "Clear Previous Output Project"
        )

        self.clear_output_button.clicked.connect(
            self.clear_output_project
        )

        buttons_layout.addWidget(
            self.generate_button
        )

        buttons_layout.addWidget(
            self.clear_output_button
        )

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    # --------------------------------------------------
    # File Pickers
    # --------------------------------------------------

    def select_audio(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Voiceover",
            "",
            "Audio Files (*.mp3 *.wav *.m4a *.aac *.flac)",
        )

        if file_path:

            self.audio_path.setText(file_path)

    def select_images(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Images Folder",
        )

        if folder:

            self.images_path.setText(folder)

    def select_output(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
        )

        if folder:

            self.output_path.setText(folder)

    # --------------------------------------------------
    # Actions
    # --------------------------------------------------

    def clear_output_project(self):

        messages = self.controller.clear_output_project()

        self.status.setText(
            "Previous output cleared"
        )

        self.log_message("")
        self.log_message("=" * 70)
        self.log_message("Clear Previous Output Project")
        self.log_message("=" * 70)

        for message in messages:

            self.log_message(message)

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

    def project_finished(self):

        self.status.setText("Finished")

        self.progress.setValue(100)

        self.log_message("Project complete.")

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log_message(
        self,
        message,
    ):

        self.log.append(
            str(message)
        )

    # --------------------------------------------------
    # Settings
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

    def save_settings(self):

        self.controller.save_paths(
            self.audio_path.text(),
            self.images_path.text(),
            self.output_path.text(),
        )

    def closeEvent(
        self,
        event,
    ):

        self.save_settings()

        event.accept()