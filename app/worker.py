from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from ai.whisper_engine import WhisperEngine
from ai.image_analyzer import ImageAnalyzer
from timeline.timeline_builder import TimelineBuilder
from timeline.segment import Segment
from exporter.resolve_xml_exporter import ResolveXMLExporter


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

            # ----------------------------------------
            # Whisper
            # ----------------------------------------

            self.status.emit("Transcribing audio...")

            whisper = WhisperEngine()

            transcript_data = whisper.transcribe(
                self.audio,
                None,
                self.log.emit,
            )

            whisper.save_json(
                transcript_data,
                "cache/transcript.json",
            )

            transcript = []

            for item in transcript_data:

                transcript.append(
                    Segment(
                        start=item["start"],
                        end=item["end"],
                        text=item["text"],
                    )
                )

            # ----------------------------------------
            # Images
            # ----------------------------------------

            self.status.emit("Preparing images...")

            self.log.emit("--------------------------------")
            self.log.emit("Scanning image folder...")
            self.log.emit("")

            image_extensions = {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
            }

            images = sorted(
                [
                    file
                    for file in Path(self.images).iterdir()
                    if file.suffix.lower() in image_extensions
                ],
                key=lambda x: x.name.lower(),
            )

            self.log.emit(
                f"Found {len(images)} images."
            )

            self.log.emit("")
            self.log.emit("Initializing AI...")

            analyzer = ImageAnalyzer(
                logger=self.log.emit
            )

            analyzed = []

            total = len(images)

            for index, image in enumerate(images):

                self.status.emit(
                    f"Analyzing {index + 1}/{total}"
                )

                self.log.emit("")
                self.log.emit("=" * 70)
                self.log.emit(
                    f"Image {index + 1}/{total}"
                )

                analyzed.append(
                    analyzer.analyze(image)
                )

                if total > 0:

                    self.progress.emit(
                        int(
                            ((index + 1) / total) * 70
                        )
                    )

            # ----------------------------------------
            # Timeline
            # ----------------------------------------

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("Building Timeline")
            self.log.emit("=" * 70)

            builder = TimelineBuilder(
                logger=self.log.emit
            )

            builder.build(
                transcript,
                analyzed,
            )

            # ----------------------------------------
            # Export Resolve XML
            # ----------------------------------------

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("Exporting Resolve XML")
            self.log.emit("=" * 70)

            exporter = ResolveXMLExporter(
                logger=self.log.emit
            )

            exporter.export(
                audio_path=self.audio,
                timeline_path="output/timeline.json",
                output_path="output/project.xml",
            )

            self.progress.emit(100)

            self.status.emit("Finished")

            self.finished.emit()

        except Exception as e:

            self.error.emit(
                str(e)
            )