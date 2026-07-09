from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from ai.whisper_engine import WhisperEngine
from ai.image_analyzer import ImageAnalyzer
from timeline.timeline_builder import TimelineBuilder
from timeline.segment import Segment
from exporter.resolve_xml_exporter import ResolveXMLExporter
from exporter.capcut_exporter import CapCutExporter


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
            # Start
            # ----------------------------------------

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("FULL PROJECT GENERATION")
            self.log.emit("=" * 70)
            self.log.emit("This will create both Resolve XML and CapCut project.")
            self.log.emit("")

            # ----------------------------------------
            # Whisper
            # ----------------------------------------

            self.status.emit("Transcribing audio...")

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("WHISPER TRANSCRIPTION")
            self.log.emit("=" * 70)

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

            self.progress.emit(10)

            # ----------------------------------------
            # Images
            # ----------------------------------------

            self.status.emit("Scanning images...")

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("SCANNING IMAGE FOLDER")
            self.log.emit("=" * 70)

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

            if not images:

                raise ValueError(
                    "No images found in selected image folder."
                )

            # ----------------------------------------
            # Analyze Images
            # ----------------------------------------

            self.status.emit("Initializing AI...")

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("IMAGE ANALYSIS")
            self.log.emit("=" * 70)

            analyzer = ImageAnalyzer(
                logger=self.log.emit
            )

            analyzed = []

            total_images = len(images)

            for index, image in enumerate(images):

                self.status.emit(
                    f"Analyzing image {index + 1}/{total_images}"
                )

                self.log.emit("")
                self.log.emit("=" * 70)
                self.log.emit(
                    f"Image {index + 1}/{total_images}: {image.name}"
                )

                analyzed.append(
                    analyzer.analyze(image)
                )

                if total_images > 0:

                    progress = 10 + int(
                        ((index + 1) / total_images) * 55
                    )

                    self.progress.emit(
                        progress
                    )

            # ----------------------------------------
            # Build Timeline
            # ----------------------------------------

            self.status.emit("Building matched timeline...")

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("BUILDING MATCHED TIMELINE")
            self.log.emit("=" * 70)

            builder = TimelineBuilder(
                logger=self.log.emit
            )

            builder.build(
                transcript,
                analyzed,
            )

            self.progress.emit(75)

            # ----------------------------------------
            # Export Resolve XML
            # ----------------------------------------

            self.status.emit("Exporting Resolve XML...")

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("EXPORTING RESOLVE XML")
            self.log.emit("=" * 70)

            resolve_exporter = ResolveXMLExporter(
                logger=self.log.emit
            )

            resolve_exporter.export(
                audio_path=self.audio,
                timeline_path="output/timeline.json",
                output_path="output/project.xml",
            )

            self.progress.emit(85)

            # ----------------------------------------
            # Export CapCut Project
            # ----------------------------------------

            self.status.emit("Exporting CapCut project...")

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("EXPORTING CAPCUT PROJECT")
            self.log.emit("=" * 70)

            capcut_exporter = CapCutExporter(
                logger=self.log.emit
            )

            capcut_project = capcut_exporter.export_from_timeline(
                audio_path=self.audio,
                timeline_path="output/timeline.json",
            )

            self.progress.emit(100)

            # ----------------------------------------
            # Done
            # ----------------------------------------

            self.status.emit("Finished")

            self.log.emit("")
            self.log.emit("=" * 70)
            self.log.emit("DONE")
            self.log.emit("=" * 70)
            self.log.emit("Resolve XML:")
            self.log.emit("output/project.xml")
            self.log.emit("")
            self.log.emit("CapCut project:")
            self.log.emit(str(capcut_project))
            self.log.emit("")
            self.log.emit("Close and reopen CapCut.")
            self.log.emit("The new MangaRecap project should appear.")

            self.finished.emit()

        except Exception as e:

            self.error.emit(
                str(e)
            )