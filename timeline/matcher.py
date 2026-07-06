import re
from difflib import SequenceMatcher

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from ai.ocr_judge import OCRJudge


class TimelineMatcher:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        # Check current image + next 3 images.
        # Never go backward.
        self.window_forward = 3

        self.used_counts = {}

        self.ocr_judge = OCRJudge(
            logger=logger
        )

    # --------------------------------------------------
    # Text helpers
    # --------------------------------------------------

    def as_text(
        self,
        value,
    ):

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

    def normalize(
        self,
        text,
    ):

        text = str(text).lower()

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

    def words(
        self,
        text,
    ):

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
            "somehow",
            "suddenly",
            "usual",
            "full",
            "situation",
            "one",
            "two",
            "also",
            "really",
            "actually",
        }

        return [
            word
            for word in self.normalize(text).split()
            if word not in stop_words
            and len(word) > 1
        ]

    # --------------------------------------------------
    # Transcript context
    # --------------------------------------------------

    def transcript_context(
        self,
        transcript,
        index,
    ):

        parts = []

        if index - 2 >= 0:

            parts.append(
                transcript[index - 2].text
            )

        if index - 1 >= 0:

            parts.append(
                transcript[index - 1].text
            )

        parts.append(
            transcript[index].text
        )

        if index + 1 < len(transcript):

            parts.append(
                transcript[index + 1].text
            )

        if index + 2 < len(transcript):

            parts.append(
                transcript[index + 2].text
            )

        return " ".join(parts)

    # --------------------------------------------------
    # Image text
    # --------------------------------------------------

    def image_text(
        self,
        image,
    ):

        scene = image.get(
            "scene",
            {},
        ) or {}

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

    # --------------------------------------------------
    # OCR score
    # --------------------------------------------------

    def ocr_similarity(
        self,
        text,
        image,
    ):

        ocr = image.get(
            "ocr",
            "",
        )

        if not ocr:
            return 0.0

        text_clean = self.normalize(
            text
        )

        ocr_clean = self.normalize(
            ocr
        )

        if not text_clean or not ocr_clean:
            return 0.0

        sequence_score = SequenceMatcher(
            None,
            text_clean,
            ocr_clean,
        ).ratio()

        text_words = set(
            self.words(text)
        )

        ocr_words = set(
            self.words(ocr)
        )

        if not text_words or not ocr_words:
            return sequence_score

        overlap = text_words.intersection(
            ocr_words
        )

        overlap_score = len(overlap) / max(
            1,
            min(
                len(text_words),
                len(ocr_words),
            ),
        )

        important_words = {
            "reincarnate",
            "promise",
            "never",
            "hesitate",
            "enemy",
            "teacher",
            "student",
            "transfer",
            "fate",
            "arguing",
            "fight",
            "favor",
            "friend",
            "foe",
            "study",
            "support",
            "moral",
            "duty",
            "inukai",
            "pamura",
            "shibasaki",
            "better",
            "wanted",
            "morning",
            "routine",
            "school",
            "class",
            "help",
            "understood",
            "situation",
        }

        important_overlap = overlap.intersection(
            important_words
        )

        important_bonus = min(
            0.45,
            0.15 * len(important_overlap),
        )

        return min(
            1.0,
            max(
                sequence_score,
                overlap_score,
            )
            + important_bonus,
        )

    # --------------------------------------------------
    # Score building
    # --------------------------------------------------

    def build_scores(
        self,
        transcript,
        images,
    ):

        contexts = [
            self.transcript_context(
                transcript,
                index,
            )
            for index in range(len(transcript))
        ]

        current_texts = [
            segment.text
            for segment in transcript
        ]

        image_texts = [
            self.image_text(image)
            for image in images
        ]

        if self.logger:

            self.logger(
                "Encoding transcript and image text..."
            )

        context_embeddings = self.model.encode(
            contexts,
            convert_to_tensor=True,
        )

        image_embeddings = self.model.encode(
            image_texts,
            convert_to_tensor=True,
        )

        semantic_matrix = cos_sim(
            context_embeddings,
            image_embeddings,
        )

        scores = []

        for segment_index in range(
            len(transcript)
        ):

            row = []

            for image_index in range(
                len(images)
            ):

                semantic = float(
                    semantic_matrix[
                        segment_index
                    ][
                        image_index
                    ]
                )

                ocr_current = self.ocr_similarity(
                    current_texts[segment_index],
                    images[image_index],
                )

                ocr_context = self.ocr_similarity(
                    contexts[segment_index],
                    images[image_index],
                )

                total = 0.18 * semantic

                total += 0.78 * ocr_current

                total += 0.18 * ocr_context

                if ocr_current >= 0.70:

                    total += 0.50

                elif ocr_current >= 0.55:

                    total += 0.28

                elif ocr_current >= 0.40:

                    total += 0.12

                row.append(
                    {
                        "semantic": semantic,
                        "ocr_current": ocr_current,
                        "ocr_context": ocr_context,
                        "score": total,
                    }
                )

            scores.append(
                row
            )

        return scores, contexts

    # --------------------------------------------------
    # OCR judge
    # --------------------------------------------------

    def apply_ocr_judge(
        self,
        segment_text,
        context_text,
        images,
        candidate_indices,
        scores,
        segment_index,
    ):

        candidates = []

        number_to_image_index = {}

        for number, image_index in enumerate(
            candidate_indices,
            start=1,
        ):

            ocr = images[image_index].get(
                "ocr",
                "",
            )

            candidates.append(
                {
                    "number": number,
                    "ocr": ocr,
                }
            )

            number_to_image_index[number] = image_index

        result = self.ocr_judge.judge(
            segment_text,
            context_text,
            candidates,
        )

        if not result:

            return None

        confidence = result.get(
            "confidence",
            0.0,
        )

        if confidence < 0.55:

            return None

        best_number = result.get(
            "best_candidate",
            0,
        )

        chosen_image_index = number_to_image_index.get(
            best_number
        )

        if chosen_image_index is None:

            return None

        detail = scores[
            segment_index
        ][
            chosen_image_index
        ]

        return {
            "image_index": chosen_image_index,
            "confidence": confidence,
            "detail": detail,
            "reason": result.get(
                "reason",
                "",
            ),
        }

    # --------------------------------------------------
    # Movement rules
    # --------------------------------------------------

    def advance_threshold(
        self,
        current_ocr,
        candidate_ocr,
        distance,
        current_used_count,
        segment_index,
        total_segments,
        current_image_index,
        image_count,
    ):

        threshold = 0.18

        # Do not jump too fast.
        if distance == 2:

            threshold += 0.14

        elif distance >= 3:

            threshold += 0.30

        # If current image still matches OCR,
        # keep it longer.
        if current_ocr >= 0.60:

            threshold += 0.22

        elif current_ocr >= 0.45:

            threshold += 0.14

        elif current_ocr >= 0.35:

            threshold += 0.07

        # If candidate OCR is clearly strong,
        # allow moving.
        if candidate_ocr >= 0.75:

            threshold -= 0.24

        elif candidate_ocr >= 0.60:

            threshold -= 0.16

        elif candidate_ocr >= 0.45:

            threshold -= 0.08

        # If current image has been held too long
        # and no longer matches, move easier.
        if current_used_count >= 3 and current_ocr < 0.30:

            threshold -= 0.08

        if current_used_count >= 5 and current_ocr < 0.40:

            threshold -= 0.10

        # If we are far behind expected image,
        # allow movement, but only if current OCR is weak.
        progress = segment_index / max(
            1,
            total_segments - 1,
        )

        expected = round(
            progress * max(
                0,
                image_count - 1,
            )
        )

        behind_by = expected - current_image_index

        if behind_by >= 4 and current_ocr < 0.45:

            threshold -= 0.12

        elif behind_by >= 3 and current_ocr < 0.40:

            threshold -= 0.08

        elif behind_by >= 2 and current_ocr < 0.30:

            threshold -= 0.05

        return max(
            0.05,
            threshold,
        )

    def movement_penalty(
        self,
        distance,
    ):

        if distance == 0:

            return 0.00

        if distance == 1:

            return 0.01

        if distance == 2:

            return -0.10

        return -0.22

    # --------------------------------------------------
    # Segment choice
    # --------------------------------------------------

    def choose_for_segment(
        self,
        segment_index,
        transcript,
        images,
        scores,
        contexts,
        current_image_index,
    ):

        image_count = len(images)

        total_segments = len(transcript)

        current_detail = scores[
            segment_index
        ][
            current_image_index
        ]

        current_score = current_detail[
            "score"
        ]

        current_ocr = current_detail[
            "ocr_current"
        ]

        current_used_count = self.used_counts.get(
            current_image_index,
            0,
        )

        start = current_image_index

        end = min(
            image_count,
            current_image_index + self.window_forward + 1,
        )

        candidate_indices = list(
            range(
                start,
                end,
            )
        )

        judge_result = self.apply_ocr_judge(
            transcript[segment_index].text,
            contexts[segment_index],
            images,
            candidate_indices,
            scores,
            segment_index,
        )

        best_index = current_image_index

        best_detail = current_detail

        best_score = current_score

        if self.logger:

            self.logger("")
            self.logger(
                f"Search window: {start + 1} to {end}"
            )

        for image_index in candidate_indices:

            detail = scores[
                segment_index
            ][
                image_index
            ]

            distance = image_index - current_image_index

            penalty = self.movement_penalty(
                distance
            )

            candidate_score = (
                detail["score"]
                + penalty
            )

            if self.logger:

                self.logger(
                    f"{images[image_index]['file']} -> "
                    f"base {detail['score']:.3f}, "
                    f"semantic {detail['semantic']:.3f}, "
                    f"ocr_current {detail['ocr_current']:.3f}, "
                    f"ocr_context {detail['ocr_context']:.3f}, "
                    f"move_penalty {penalty:.3f}, "
                    f"candidate {candidate_score:.3f}"
                )

            if candidate_score > best_score:

                best_score = candidate_score

                best_index = image_index

                best_detail = detail

        # --------------------------------------------------
        # Smart OCR judge override / boost
        # --------------------------------------------------

        if judge_result:

            judge_image_index = judge_result[
                "image_index"
            ]

            judge_confidence = judge_result[
                "confidence"
            ]

            judge_detail = judge_result[
                "detail"
            ]

            if self.logger:

                self.logger(
                    f"OCR judge wants image {judge_image_index + 1} "
                    f"with confidence {judge_confidence:.2f}"
                )

            # Never go backward.
            if judge_image_index >= current_image_index:

                judge_distance = (
                    judge_image_index
                    - current_image_index
                )

                # Very high confidence can override,
                # but still respects forward-only.
                if judge_confidence >= 0.78:

                    best_index = judge_image_index

                    best_detail = judge_detail

                    best_score = (
                        judge_detail["score"]
                        + 0.60
                        - 0.05 * judge_distance
                    )

                    if self.logger:

                        self.logger(
                            "Decision: OCR judge strong override."
                        )

                elif judge_confidence >= 0.65:

                    judge_candidate_score = (
                        judge_detail["score"]
                        + 0.30
                        - 0.04 * judge_distance
                    )

                    if judge_candidate_score > best_score:

                        best_index = judge_image_index

                        best_detail = judge_detail

                        best_score = judge_candidate_score

                        if self.logger:

                            self.logger(
                                "Decision: OCR judge medium boost."
                            )

        # --------------------------------------------------
        # Advance check
        # --------------------------------------------------

        if best_index > current_image_index:

            distance = best_index - current_image_index

            threshold = self.advance_threshold(
                current_ocr,
                best_detail["ocr_current"],
                distance,
                current_used_count,
                segment_index,
                total_segments,
                current_image_index,
                image_count,
            )

            improvement = (
                best_score - current_score
            )

            if self.logger:

                self.logger(
                    f"Advance check: current {current_score:.3f}, "
                    f"best {best_score:.3f}, "
                    f"improvement {improvement:.3f}, "
                    f"needed {threshold:.3f}"
                )

            if improvement < threshold:

                best_index = current_image_index

                best_detail = current_detail

                best_score = current_score

                if self.logger:

                    self.logger(
                        "Decision: stay on current image."
                    )

            else:

                if self.logger:

                    self.logger(
                        "Decision: advance to new image."
                    )

        else:

            if self.logger:

                self.logger(
                    "Decision: stay on current image."
                )

        self.used_counts[best_index] = (
            self.used_counts.get(
                best_index,
                0,
            )
            + 1
        )

        return {
            "segment_index": segment_index,
            "image_index": best_index,
            "score": best_score,
            "semantic": best_detail["semantic"],
            "ocr_current": best_detail["ocr_current"],
            "ocr_context": best_detail["ocr_context"],
            "context": contexts[segment_index],
        }

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def match(
        self,
        transcript,
        images,
    ):

        if not transcript:

            raise ValueError(
                "Transcript is empty."
            )

        if not images:

            raise ValueError(
                "No images to match."
            )

        scores, contexts = self.build_scores(
            transcript,
            images,
        )

        results = []

        current_image_index = 0

        for segment_index in range(
            len(transcript)
        ):

            if self.logger:

                self.logger("")
                self.logger("=" * 70)
                self.logger(
                    transcript[segment_index].text
                )

            result = self.choose_for_segment(
                segment_index,
                transcript,
                images,
                scores,
                contexts,
                current_image_index,
            )

            current_image_index = result[
                "image_index"
            ]

            results.append(
                result
            )

        return results