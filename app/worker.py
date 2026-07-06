from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from ai.whisper_engine import WhisperEngine
from ai.image_analyzer import ImageAnalyzer


class Worker(QObject):

    progress = Signal(int)
    status = Signal(str)
    log = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self):

        super().__init__()

        self.audio = ""
        self.images = ""
        self.output = ""

    @Slot()
    def run(self):

        try:

            # ----------------------------
            # Whisper
            # ----------------------------

            self.status.emit("Transcribing audio...")

            whisper = WhisperEngine()

            transcript = whisper.transcribe(
                self.audio,
                None,
                self.log.emit,
            )

            whisper.save_json(
                transcript,
                "cache/transcript.json",
            )

            # ----------------------------
            # Images
            # ----------------------------

            self.status.emit("Analyzing images...")

            analyzer = ImageAnalyzer()

            image_extensions = {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
            }

            images = []

            for file in Path(self.images).iterdir():

                if file.suffix.lower() in image_extensions:

                    images.append(file)

            total = len(images)

            for index, image in enumerate(images):

                analyzer.analyze(image)

                progress = int(
                    ((index + 1) / total) * 100
                )

                self.progress.emit(progress)

                self.log.emit(
                    f"Analyzed {image.name}"
                )

            self.status.emit("Finished")

            self.finished.emit()

        except Exception as e:

            self.error.emit(str(e))