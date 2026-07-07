from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

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
            # CapCut Project Export
            # ----------------------------------------

            self.status.emit(
                "Preparing CapCut project..."
            )

            self.log.emit(
                ""
            )

            self.log.emit(
                "=" * 70
            )

            self.log.emit(
                "CAPCUT PROJECT EXPORT"
            )

            self.log.emit(
                "=" * 70
            )

            self.log.emit(
                "This version does not use AI matching."
            )

            self.log.emit(
                "It creates a simple editable CapCut project."
            )

            self.log.emit(
                ""
            )

            # ----------------------------------------
            # Scan images
            # ----------------------------------------

            image_extensions = {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
            }

            image_folder = Path(
                self.images
            )

            images = sorted(
                [
                    file
                    for file in image_folder.iterdir()
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

            self.progress.emit(
                20
            )

            # ----------------------------------------
            # Export CapCut project
            # ----------------------------------------

            exporter = CapCutExporter(
                logger=self.log.emit
            )

            project_folder = exporter.export(
                audio_path=self.audio,
                image_paths=images,
            )

            self.progress.emit(
                100
            )

            self.status.emit(
                "Finished"
            )

            self.log.emit(
                ""
            )

            self.log.emit(
                "=" * 70
            )

            self.log.emit(
                "DONE"
            )

            self.log.emit(
                "=" * 70
            )

            self.log.emit(
                f"CapCut project folder: {project_folder}"
            )

            self.log.emit(
                ""
            )

            self.log.emit(
                "Close and reopen CapCut."
            )

            self.log.emit(
                "The new MangaRecap project should appear in your projects."
            )

            self.finished.emit()

        except Exception as e:

            self.error.emit(
                str(e)
            )