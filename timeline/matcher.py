from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


class TimelineMatcher:

    def __init__(self, logger=None):

        self.logger = logger

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    def image_text(self, image):

        scene = image["scene"]

        parts = []

        parts.append(
            image.get(
                "ocr",
                "",
            )
        )

        parts.append(
            scene.get(
                "summary",
                "",
            )
        )

        parts.append(
            scene.get(
                "possible_event",
                "",
            )
        )

        parts.extend(
            scene.get(
                "visible_actions",
                [],
            )
        )

        parts.append(
            scene.get(
                "location",
                "",
            )
        )

        return "\n".join(parts)

    def similarity(
        self,
        transcript,
        image,
    ):

        a = self.model.encode(
            transcript,
            convert_to_tensor=True,
        )

        b = self.model.encode(
            self.image_text(image),
            convert_to_tensor=True,
        )

        return float(
            cos_sim(a, b)
        )

    def choose(
        self,
        transcript,
        images,
        current_index,
    ):

        best_index = current_index

        best_score = -1

        end = min(
            current_index + 8,
            len(images),
        )

        for i in range(
            current_index,
            end,
        ):

            score = self.similarity(
                transcript,
                images[i],
            )

            if self.logger:

                self.logger(
                    f"{images[i]['file']} -> {score:.3f}"
                )

            if score > best_score:

                best_score = score

                best_index = i

        return best_index, best_score