from PySide6.QtCore import QObject, Signal, Slot

from ai.whisper_engine import WhisperEngine


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

            self.status.emit(
                "Loading Whisper..."
            )

            whisper = WhisperEngine()

            transcript = whisper.transcribe(
                self.audio,
                self.progress.emit,
                self.log.emit,
            )

            whisper.save_json(
                transcript,
                "cache/transcript.json",
            )

            self.status.emit(
                "Transcript created."
            )

            self.progress.emit(100)

            self.finished.emit()

        except Exception as e:

            self.error.emit(str(e))