from PySide6.QtWidgets import (
    QWidget,
    QFileDialog,
    QPushButton,
    QLineEdit,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QProgressBar,
    QPlainTextEdit,
    QCheckBox,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Manga Recap Studio")
        self.resize(900, 650)

        self.build_ui()

    def build_ui(self):
        main_layout = QVBoxLayout()

        # -----------------------------
        # Project Files
        # -----------------------------
        project_group = QGroupBox("Project")

        project_layout = QVBoxLayout()

        self.audio_path = QLineEdit()
        self.audio_path.setReadOnly(True)

        audio_button = QPushButton("Browse")

        row = QHBoxLayout()
        row.addWidget(QLabel("Voiceover"))
        row.addWidget(self.audio_path)
        row.addWidget(audio_button)

        project_layout.addLayout(row)

        self.images_path = QLineEdit()
        self.images_path.setReadOnly(True)

        images_button = QPushButton("Browse")

        row = QHBoxLayout()
        row.addWidget(QLabel("Images"))
        row.addWidget(self.images_path)
        row.addWidget(images_button)

        project_layout.addLayout(row)

        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)

        output_button = QPushButton("Browse")

        row = QHBoxLayout()
        row.addWidget(QLabel("Output"))
        row.addWidget(self.output_path)
        row.addWidget(output_button)

        project_layout.addLayout(row)

        project_group.setLayout(project_layout)

        # -----------------------------
        # Options
        # -----------------------------
        options_group = QGroupBox("Options")

        options_layout = QVBoxLayout()

        self.smart_matching = QCheckBox("Smart Image Matching")
        self.smart_matching.setChecked(True)

        self.cache_results = QCheckBox("Cache Image Analysis")
        self.cache_results.setChecked(True)

        self.auto_detect = QCheckBox("Auto Detect Scenes")
        self.auto_detect.setChecked(True)

        options_layout.addWidget(self.smart_matching)
        options_layout.addWidget(self.cache_results)
        options_layout.addWidget(self.auto_detect)

        options_group.setLayout(options_layout)

        # -----------------------------
        # Progress
        # -----------------------------
        self.status = QLabel("Ready")

        self.progress = QProgressBar()
        self.progress.setValue(0)

        # -----------------------------
        # Log
        # -----------------------------
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.appendPlainText("Application started.")

        # -----------------------------
        # Generate
        # -----------------------------
        self.generate = QPushButton("Generate Project")

        main_layout.addWidget(project_group)
        main_layout.addWidget(options_group)
        main_layout.addWidget(self.status)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.log)
        main_layout.addWidget(self.generate)

        self.setLayout(main_layout)

        audio_button.clicked.connect(self.select_audio)
        images_button.clicked.connect(self.select_images)
        output_button.clicked.connect(self.select_output)

    def log_message(self, text):
        self.log.appendPlainText(text)

    def select_audio(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Voiceover",
            "",
            "Audio (*.mp3 *.wav *.m4a)"
        )

        if file:
            self.audio_path.setText(file)
            self.log_message("Voiceover selected.")

    def select_images(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Images Folder"
        )

        if folder:
            self.images_path.setText(folder)
            self.log_message("Images folder selected.")

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Output Folder"
        )

        if folder:
            self.output_path.setText(folder)
            self.log_message("Output folder selected.")