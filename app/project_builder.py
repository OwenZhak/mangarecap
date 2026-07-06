from pathlib import Path

from ai.image_analyzer import ImageAnalyzer
from ai.whisper_engine import WhisperEngine

from exporter.models import (
    AudioClip,
    TimelineClip,
)

from exporter.project import (
    EditorProject,
)

from exporter.resolve_xml import (
    ResolveXMLExporter,
)

from timeline.segment import Segment
from timeline.timeline_builder import TimelineBuilder


class ProjectBuilder:

    def __init__(
        self,
        logger=None,
        progress=None,
    ):

        self.logger = logger

        self.progress = progress

    def build(

        self,

        audio,

        image_folder,

    ):

        whisper = WhisperEngine()

        transcript_raw = whisper.transcribe(

            audio,

            None,

            self.logger,

        )

        whisper.save_json(

            transcript_raw,

            "cache/transcript.json",

        )

        transcript = [

            Segment(

                start=x["start"],

                end=x["end"],

                text=x["text"],

            )

            for x in transcript_raw

        ]

        analyzer = ImageAnalyzer(

            logger=self.logger

        )

        extensions = {

            ".png",

            ".jpg",

            ".jpeg",

            ".webp",

        }

        images = sorted(

            [

                p

                for p in Path(image_folder).iterdir()

                if p.suffix.lower() in extensions

            ],

            key=lambda x: x.name.lower(),

        )

        analyzed = []

        for image in images:

            analyzed.append(

                analyzer.analyze(image)

            )

        timeline = TimelineBuilder(

            logger=self.logger

        ).build(

            transcript,

            analyzed,

        )

        project = EditorProject(

            audio=AudioClip(

                path=audio,

                duration=transcript[-1].end,

            )

        )

        for clip in timeline:

            project.clips.append(

                TimelineClip(

                    image=clip["image"],

                    start=clip["start"],

                    end=clip["end"],

                    duration=clip["end"] - clip["start"],

                )

            )

        ResolveXMLExporter(

            self.logger

        ).export(

            project,

            "output/project.xml",

        )

        return project