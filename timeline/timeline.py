import json

from timeline.matcher import TimelineMatcher


class TimelineBuilder:

    def __init__(self, logger=None):

        self.logger = logger

        self.matcher = TimelineMatcher(
            logger,
        )

    def build(
        self,
        transcript,
        images,
    ):

        timeline = []

        current = 0

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

            timeline.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "image": images[
                        chosen
                    ]["file"],
                    "score": score,
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
            )

        if self.logger:

            self.logger("")
            self.logger(
                "timeline.json written."
            )

        return timeline