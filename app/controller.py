from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread

from app.logger import Logger
from app.settings import SettingsManager
from app.worker import Worker


class Controller(QObject):
    """
    Main application controller.

    The UI should ONLY communicate with this class.
    Everything else (AI, timeline, exporting) will be
    coordinated from here.
    """

    def __init__(self):
        super().__init__()

        self.settings = SettingsManager()
        self.logger = Logger()

        self.thread: Optional[QThread] = None
        self.worker: Optional[Worker] = None

    # --------------------------------------------------
    # Settings
    # --------------------------------------------------

    def save_paths(
        self,
        audio: str,
        images: str,
        output: str,
    ) -> None:

        self.settings.set("audio_path", audio)
        self.settings.set("images_path", images)
        self.settings.set("output_path", output)

    def load_paths(self):

        return {
            "audio": self.settings.get("audio_path", ""),
            "images": self.settings.get("images_path", ""),
            "output": self.settings.get("output_path", ""),
        }

    # --------------------------------------------------
    # Validation
    # --------------------------------------------------

    def validate(
        self,
        audio: str,
        images: str,
        output: str,
    ):

        errors = []

        if not audio:
            errors.append("Voiceover not selected.")

        elif not Path(audio).exists():
            errors.append("Voiceover file doesn't exist.")

        if not images:
            errors.append("Images folder not selected.")

        elif not Path(images).exists():
            errors.append("Images folder doesn't exist.")

        if not output:
            errors.append("Output folder not selected.")

        elif not Path(output).exists():
            errors.append("Output folder doesn't exist.")

        return errors

    # --------------------------------------------------
    # Worker
    # --------------------------------------------------

    def create_worker(self):

        self.thread = QThread()

        self.worker = Worker()

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.finished.connect(
            self.worker.deleteLater
        )

        self.thread.finished.connect(
            self.thread.deleteLater
        )

    def start_job(
        self,
        audio: str,
        images: str,
        output: str,
    ):

        errors = self.validate(
            audio,
            images,
            output,
        )

        if errors:
            return errors

        self.logger.info("Starting project generation.")

        self.create_worker()

        self.worker.audio = audio
        self.worker.images = images
        self.worker.output = output

        self.thread.start()

        return []

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log(self, message: str):

        self.logger.info(message)