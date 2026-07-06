import re
from difflib import SequenceMatcher

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


class TimelineMatcher:

    def __init__(self, logger=None):

        self.logger = logger

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        self.window_back = 2

        self.window_forward = 4

        self.used_counts = {}

    def as_text(self, value):

        if value is None:
            return ""

        if isinstance(value, str):
            return value

        if isinstance(value, (int, float)):
            return str(value)

        if isinstance(value, list):

            return " ".join(
                self.as_text(item)
                for item in value
            )

        if isinstance(value, dict):

            return " ".join(
                self.as_text(item)
                for item in value.values()
            )

        return str(value)

    def normalize(self, text):

        text = text.lower()

        text = re.sub(
            r"[^a-z0-9\s']",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        return text

    def words(self, text):

        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "to",
            "of",
            "in",
            "on",
            "at",
            "for",
            "with",
            "as",
            "it",
            "is",
            "was",
            "were",
            "be",
            "been",
            "that",
            "this",
            "he",
            "she",
            "they",
            "his",
            "her",
            "their",
            "him",
            "them",
            "had",
            "has",
            "have",
            "would",
            "could",
            "should",
            "then",
            "now",
            "just",
            "like",
            "right",
            "back",
        }

        cleaned = self.normalize(text)

        result = []

        for word in cleaned.split():

            if word in stop_words:
                continue

            if len(word) <= 1:
                continue

            result.append(word)

        return result

    def image_text(self, image):

        scene = image.get("scene", {}) or {}

        parts = [
            image.get("ocr", ""),
            scene.get("summary", ""),
            scene.get("possible_event", ""),
            scene.get("visible_people", []),
            scene.get("visible_actions", []),
            scene.get("visible_objects", []),
            scene.get("location", ""),
            scene.get("emotion", ""),
        ]

        return "\n".join(
            self.as_text(part)
            for part in parts
            if self.as_text(part).strip()
        )

    def semantic_similarity(
        self,
        transcript,
        image,
    ):

        transcript_embedding = self.model.encode(
            transcript,
            convert_to_tensor=True,
        )

        image_embedding = self.model.encode(
            self.image_text(image),
            convert_to_tensor=True,
        )

        score = cos_sim(
            transcript_embedding,
            image_embedding,
        )

        return float(score)

    def ocr_similarity(
        self,
        transcript,
        image,
    ):

        ocr = image.get("ocr", "")

        if not ocr:
            return 0.0

        transcript_clean = self.normalize(transcript)

        ocr_clean = self.normalize(ocr)

        if not transcript_clean or not ocr_clean:
            return 0.0

        sequence_score = SequenceMatcher(
            None,
            transcript_clean,
            ocr_clean,
        ).ratio()

        transcript_words = self.words(transcript)

        ocr_words = self.words(ocr)

        if not transcript_words or not ocr_words:
            return sequence_score

        transcript_set = set(transcript_words)

        ocr_set = set(ocr_words)

        overlap = transcript_set.intersection(
            ocr_set
        )

        short_length = max(
            1,
            min(
                len(transcript_set),
                len(ocr_set),
            ),
        )

        overlap_score = len(overlap) / short_length

        joined_transcript = " ".join(
            transcript_words
        )

        joined_ocr = " ".join(
            ocr_words
        )

        phrase_bonus = 0.0

        if joined_transcript in joined_ocr:
            phrase_bonus = 0.35

        elif joined_ocr in joined_transcript:
            phrase_bonus = 0.25

        return min(
            1.0,
            max(sequence_score, overlap_score)
            + phrase_bonus,
        )

    def position_bonus(
        self,
        index,
        current_index,
    ):

        distance = abs(index - current_index)

        if distance == 0:
            return 0.08

        if distance == 1:
            return 0.06

        if distance == 2:
            return 0.03

        return 0.0

    def progress_bonus(
        self,
        index,
        current_index,
    ):

        if index > current_index:
            return 0.04

        if index == current_index:
            return 0.02

        return -0.03

    def usage_bonus(
        self,
        index,
    ):

        count = self.used_counts.get(
            index,
            0,
        )

        if count == 0:
            return 0.06

        if count == 1:
            return 0.0

        return -0.04 * count

    def final_score(
        self,
        semantic,
        ocr,
        index,
        current_index,
    ):

        score = 0.45 * semantic

        score += 0.45 * ocr

        score += self.position_bonus(
            index,
            current_index,
        )

        score += self.progress_bonus(
            index,
            current_index,
        )

        score += self.usage_bonus(
            index,
        )

        if ocr >= 0.65:
            score += 0.20

        elif ocr >= 0.45:
            score += 0.10

        return score

    def choose(
        self,
        transcript,
        images,
        current_index,
    ):

        if not images:
            raise ValueError("No images to match.")

        start = max(
            0,
            current_index - self.window_back,
        )

        end = min(
            len(images),
            current_index + self.window_forward + 1,
        )

        best_index = current_index

        best_total = -999

        best_semantic = 0.0

        best_ocr = 0.0

        for index in range(start, end):

            semantic = self.semantic_similarity(
                transcript,
                images[index],
            )

            ocr = self.ocr_similarity(
                transcript,
                images[index],
            )

            total = self.final_score(
                semantic,
                ocr,
                index,
                current_index,
            )

            if self.logger:

                self.logger(
                    f"{images[index]['file']} -> "
                    f"semantic {semantic:.3f}, "
                    f"ocr {ocr:.3f}, "
                    f"total {total:.3f}"
                )

            if total > best_total:

                best_total = total

                best_index = index

                best_semantic = semantic

                best_ocr = ocr

        self.used_counts[best_index] = (
            self.used_counts.get(
                best_index,
                0,
            )
            + 1
        )

        if self.logger:

            self.logger(
                f"Best detail: semantic {best_semantic:.3f}, "
                f"ocr {best_ocr:.3f}, "
                f"total {best_total:.3f}"
            )

        return best_index, best_total