from dataclasses import dataclass, field

from exporter.models import (
    AudioClip,
    TimelineClip,
)


@dataclass
class EditorProject:

    audio: AudioClip

    clips: list[TimelineClip] = field(
        default_factory=list
    )