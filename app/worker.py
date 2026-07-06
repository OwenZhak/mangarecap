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

            self.status.emit("Preparing image analysis...")

            self.log.emit("--------------------------------")
            self.log.emit("Scanning image folder...")
            self.log.emit("")

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

            self.log.emit(
                f"Found {len(images)} images."
            )

            self.log.emit("")
            self.log.emit("Initializing AI models...")

            analyzer = ImageAnalyzer(
                logger=self.log.emit
            )

            self.log.emit("")
            self.log.emit("All AI models loaded.")
            self.log.emit("--------------------------------")

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

                self.status.emit(
                    f"Analyzing {index+1}/{len(images)}"
                )

                self.log.emit("")
                self.log.emit(
                    "=" * 60
                )

                self.log.emit(
                    f"Image {index+1} / {len(images)}"
                )

                analyzer.analyze(image)

                progress = int(
                    ((index + 1) / len(images)) * 100
                )

                self.progress.emit(progress)

            self.status.emit("Finished")

            self.finished.emit()

        except Exception as e:

            self.error.emit(str(e))