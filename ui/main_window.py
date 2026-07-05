from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QFileDialog,
    QVBoxLayout,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Manga Recap Studio")
        self.resize(700, 500)

        layout = QVBoxLayout()

        self.audio_label = QLabel("🎤 Voiceover: Not selected")
        self.audio_button = QPushButton("Select Voiceover")

        self.script_label = QLabel("📄 Transcript: Not selected")
        self.script_button = QPushButton("Select Transcript")

        self.images_label = QLabel("🖼 Images Folder: Not selected")
        self.images_button = QPushButton("Select Images Folder")

        self.output_label = QLabel("📁 Output Folder: Not selected")
        self.output_button = QPushButton("Select Output Folder")

        self.generate_button = QPushButton("Generate Project")

        layout.addWidget(self.audio_label)
        layout.addWidget(self.audio_button)

        layout.addSpacing(10)

        layout.addWidget(self.script_label)
        layout.addWidget(self.script_button)

        layout.addSpacing(10)

        layout.addWidget(self.images_label)
        layout.addWidget(self.images_button)

        layout.addSpacing(10)

        layout.addWidget(self.output_label)
        layout.addWidget(self.output_button)

        layout.addSpacing(25)

        layout.addWidget(self.generate_button)

        self.setLayout(layout)

        self.audio_button.clicked.connect(self.select_audio)
        self.script_button.clicked.connect(self.select_script)
        self.images_button.clicked.connect(self.select_images)
        self.output_button.clicked.connect(self.select_output)

    def select_audio(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Voiceover",
            "",
            "Audio Files (*.mp3 *.wav *.m4a)"
        )

        if file:
            self.audio_label.setText(f"🎤 Voiceover: {file}")

    def select_script(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Transcript",
            "",
            "Text Files (*.txt)"
        )

        if file:
            self.script_label.setText(f"📄 Transcript: {file}")

    def select_images(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Images Folder"
        )

        if folder:
            self.images_label.setText(f"🖼 Images Folder: {folder}")

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder"
        )

        if folder:
            self.output_label.setText(f"📁 Output Folder: {folder}")