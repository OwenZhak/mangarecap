import json
from pathlib import Path

from timeline.matcher import TimelineMatcher


class TimelineBuilder:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

        self.matcher = TimelineMatcher(
            logger
        )

    def build(
        self,
        transcript,
        images,
    ):

        output_folder = Path("output")

        output_folder.mkdir(
            exist_ok=True
        )

        if self.logger:

            self.logger("")
            self.logger("=" * 70)
            self.logger("Global Chronological Matching")
            self.logger("=" * 70)

        matches = self.matcher.match(
            transcript,
            images,
        )

        timeline = []

        for match in matches:

            segment_index = match[
                "segment_index"
            ]

            image_index = match[
                "image_index"
            ]

            segment = transcript[
                segment_index
            ]

            selected_image = images[
                image_index
            ]

            if self.logger:

                self.logger("")
                self.logger("=" * 70)
                self.logger(
                    segment.text
                )
                self.logger("")
                self.logger(
                    f"Chosen image {image_index + 1}: "
                    f"{selected_image['file']}"
                )
                self.logger(
                    f"Score: {match['score']:.3f}, "
                    f"semantic: {match['semantic']:.3f}, "
                    f"ocr_current: {match['ocr_current']:.3f}, "
                    f"ocr_context: {match['ocr_context']:.3f}"
                )
                self.logger("")
                self.logger("Context used:")
                self.logger(
                    match["context"]
                )

            timeline.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "context": match["context"],
                    "image": selected_image["file"],
                    "image_path": selected_image["path"],
                    "score": round(
                        match["score"],
                        4,
                    ),
                    "semantic": round(
                        match["semantic"],
                        4,
                    ),
                    "ocr_current": round(
                        match["ocr_current"],
                        4,
                    ),
                    "ocr_context": round(
                        match["ocr_context"],
                        4,
                    ),
                }
            )

        with open(
            output_folder / "timeline.json",
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