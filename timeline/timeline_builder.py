import json
from pathlib import Path

from timeline.matcher import TimelineMatcher


class TimelineBuilder:

    def __init__(self, logger=None):

        self.logger = logger

        self.matcher = TimelineMatcher(
            logger
        )

    def build(
        self,
        transcript,
        images,
    ):

        timeline = []

        current = 0

        Path("output").mkdir(exist_ok=True)

        for segment in transcript:

            if self.logger:

                self.logger("")
                self.logger("=" * 70)
                self.logger(segment.text)

            chosen, score = self.matcher.choose(
                segment.text,
                images,
                current,
            )

            current = chosen

            if self.logger:

                self.logger(
                    f"Chosen: {images[chosen]['file']} ({score:.3f})"
                )

            timeline.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "image": images[chosen]["file"],
                    "score": round(score, 4),
                }
            )

        with open(
            "output/timeline.json",
            "w",
            encoding="utf8",
        ) as f:

            json.dump(
                timeline,
                f,
                indent=4,
                ensure_ascii=False,
            )

        if self.logger:

            self.logger("")
            self.logger("timeline.json written.")

        return timeline