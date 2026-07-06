from dataclasses import dataclass


@dataclass
class TimelineClip:

    image: str

    start: float

    end: float

    duration: float


@dataclass
class AudioClip:

    path: str

    duration: float