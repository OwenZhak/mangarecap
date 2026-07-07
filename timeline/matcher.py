import re
from difflib import SequenceMatcher

import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


try:
    from ai.ocr_judge import OCRJudge
except Exception:
    OCRJudge = None


try:
    from ai.scene_judge import SceneJudge
except Exception:
    SceneJudge = None


class TimelineMatcher:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        if self.logger:

            self.logger(
                f"Timeline matcher device: {self.device}"
            )

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            device=self.device,
        )

        self.ocr_judge = (
            OCRJudge(logger=logger)
            if OCRJudge
            else None
        )

        self.scene_judge = (
            SceneJudge(logger=logger)
            if SceneJudge
            else None
        )

        self.top_ocr_candidates = 6

        self.top_scene_candidates = 6

        self.strong_ocr_threshold = 0.58

        self.medium_ocr_threshold = 0.42

        self.strong_scene_threshold = 0.48

        self.judge_anchor_threshold = 0.62

        self.comfortable_hold_chunks = 3

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
            "there",
            "when",
            "where",
            "what",
            "why",
            "how",
            "into",
            "from",
            "after",
            "before",
            "while",
            "because",
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
    # Image scene helpers
    # --------------------------------------------------

    def image_scene(
        self,
        image,
    ):

        return image.get(
            "scene",
            {},
        ) or {}

    def image_text(
        self,
        image,
    ):

        scene = self.image_scene(
            image
        )

        parts = [
            image.get("ocr", ""),
            scene.get("summary", ""),
            scene.get("detailed_description", ""),
            scene.get("possible_event", ""),
            scene.get("story_function", ""),
            scene.get("ocr_interpretation", ""),
            scene.get("visible_people", []),
            scene.get("character_details", []),
            scene.get("visible_actions", []),
            scene.get("body_language", []),
            scene.get("facial_expressions", []),
            scene.get("visible_objects", []),
            scene.get("background_details", []),
            scene.get("location", ""),
            scene.get("camera_framing", ""),
            scene.get("emotion", ""),
            scene.get("narration_keywords", []),
            scene.get("matchable_phrases", []),
        ]

        return "\n".join(
            self.as_text(part)
            for part in parts
            if self.as_text(part).strip()
        )

    def image_scene_text(
        self,
        image,
    ):

        scene = self.image_scene(
            image
        )

        parts = [
            scene.get("summary", ""),
            scene.get("detailed_description", ""),
            scene.get("possible_event", ""),
            scene.get("story_function", ""),
            scene.get("visible_people", []),
            scene.get("character_details", []),
            scene.get("visible_actions", []),
            scene.get("body_language", []),
            scene.get("facial_expressions", []),
            scene.get("visible_objects", []),
            scene.get("background_details", []),
            scene.get("location", ""),
            scene.get("camera_framing", ""),
            scene.get("emotion", ""),
            scene.get("narration_keywords", []),
            scene.get("matchable_phrases", []),
        ]

        return "\n".join(
            self.as_text(part)
            for part in parts
            if self.as_text(part).strip()
        )

    # --------------------------------------------------
    # OCR similarity
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
            "wanted",
            "morning",
            "routine",
            "school",
            "class",
            "help",
            "understood",
            "home",
            "return",
            "returned",
            "building",
            "house",
            "apartment",
            "entrance",
            "room",
            "classroom",
            "door",
            "phone",
            "message",
            "letter",
            "confess",
            "confession",
            "love",
            "date",
            "kiss",
            "marry",
            "marriage",
            "crying",
            "tears",
            "smile",
            "angry",
            "shocked",
            "surprised",
            "blush",
            "protect",
            "save",
            "saved",
            "kill",
            "death",
            "dead",
            "monster",
            "demon",
            "hero",
            "villain",
            "party",
            "level",
            "skill",
            "magic",
        }

        important_overlap = overlap.intersection(
            important_words
        )

        important_bonus = min(
            0.40,
            0.12 * len(important_overlap),
        )

        final_score = max(
            sequence_score,
            overlap_score,
        )

        final_score += important_bonus

        return min(
            1.0,
            final_score,
        )

    # --------------------------------------------------
    # Global score matrix
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

        scene_texts = [
            self.image_scene_text(image)
            for image in images
        ]

        if self.logger:

            self.logger("")
            self.logger("=" * 70)
            self.logger("Building global score matrix")
            self.logger("=" * 70)
            self.logger(
                "Encoding transcript and all image descriptions..."
            )

        context_embeddings = self.model.encode(
            contexts,
            convert_to_tensor=True,
            device=self.device,
        )

        current_embeddings = self.model.encode(
            current_texts,
            convert_to_tensor=True,
            device=self.device,
        )

        image_embeddings = self.model.encode(
            image_texts,
            convert_to_tensor=True,
            device=self.device,
        )

        scene_embeddings = self.model.encode(
            scene_texts,
            convert_to_tensor=True,
            device=self.device,
        )

        context_to_image = cos_sim(
            context_embeddings,
            image_embeddings,
        )

        current_to_scene = cos_sim(
            current_embeddings,
            scene_embeddings,
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
                    context_to_image[
                        segment_index
                    ][
                        image_index
                    ]
                )

                scene_semantic = float(
                    current_to_scene[
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

                total = (
                    0.52 * ocr_current
                    + 0.18 * ocr_context
                    + 0.18 * semantic
                    + 0.12 * scene_semantic
                )

                row.append(
                    {
                        "score": total,
                        "semantic": semantic,
                        "scene_semantic": scene_semantic,
                        "ocr_current": ocr_current,
                        "ocr_context": ocr_context,
                    }
                )

            scores.append(
                row
            )

        return scores, contexts

    # --------------------------------------------------
    # Candidate helpers
    # --------------------------------------------------

    def top_indices(
        self,
        scores,
        segment_index,
        key,
        count,
    ):

        indexed = []

        for image_index, detail in enumerate(
            scores[segment_index]
        ):

            indexed.append(
                (
                    image_index,
                    detail[key],
                )
            )

        indexed.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return [
            image_index
            for image_index, value in indexed[:count]
        ]

    def candidate_score(
        self,
        detail,
    ):

        return (
            0.54 * detail["ocr_current"]
            + 0.18 * detail["ocr_context"]
            + 0.16 * detail["semantic"]
            + 0.12 * detail["scene_semantic"]
        )

    # --------------------------------------------------
    # Qwen OCR judge
    # --------------------------------------------------

    def run_ocr_judge(
        self,
        segment,
        context,
        images,
        candidate_indices,
    ):

        if not self.ocr_judge:

            return None

        candidates = []

        number_to_image_index = {}

        for number, image_index in enumerate(
            candidate_indices,
            start=1,
        ):

            candidates.append(
                {
                    "number": number,
                    "ocr": images[image_index].get(
                        "ocr",
                        "",
                    ),
                }
            )

            number_to_image_index[number] = image_index

        result = self.ocr_judge.judge(
            segment.text,
            context,
            candidates,
        )

        if not result:

            return None

        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
        )

        best_number = int(
            result.get(
                "best_candidate",
                0,
            )
        )

        image_index = number_to_image_index.get(
            best_number
        )

        if image_index is None:

            return None

        return {
            "image_index": image_index,
            "confidence": confidence,
            "reason": result.get(
                "reason",
                "",
            ),
        }

    # --------------------------------------------------
    # Qwen scene judge
    # --------------------------------------------------

    def run_scene_judge(
        self,
        segment,
        context,
        images,
        candidate_indices,
    ):

        if not self.scene_judge:

            return None

        candidates = []

        number_to_image_index = {}

        for number, image_index in enumerate(
            candidate_indices,
            start=1,
        ):

            image = images[image_index]

            scene = self.image_scene(
                image
            )

            candidates.append(
                {
                    "number": number,
                    "ocr": image.get("ocr", ""),
                    "summary": self.as_text(
                        scene.get("summary", "")
                    ),
                    "detailed_description": self.as_text(
                        scene.get("detailed_description", "")
                    ),
                    "possible_event": self.as_text(
                        scene.get("possible_event", "")
                    ),
                    "story_function": self.as_text(
                        scene.get("story_function", "")
                    ),
                    "location": self.as_text(
                        scene.get("location", "")
                    ),
                    "camera_framing": self.as_text(
                        scene.get("camera_framing", "")
                    ),
                    "people": self.as_text(
                        scene.get("visible_people", [])
                    ),
                    "character_details": self.as_text(
                        scene.get("character_details", [])
                    ),
                    "actions": self.as_text(
                        scene.get("visible_actions", [])
                    ),
                    "body_language": self.as_text(
                        scene.get("body_language", [])
                    ),
                    "facial_expressions": self.as_text(
                        scene.get("facial_expressions", [])
                    ),
                    "objects": self.as_text(
                        scene.get("visible_objects", [])
                    ),
                    "background": self.as_text(
                        scene.get("background_details", [])
                    ),
                    "emotion": self.as_text(
                        scene.get("emotion", "")
                    ),
                    "keywords": self.as_text(
                        scene.get("narration_keywords", [])
                    ),
                    "matchable_phrases": self.as_text(
                        scene.get("matchable_phrases", [])
                    ),
                }
            )

            number_to_image_index[number] = image_index

        result = self.scene_judge.judge(
            segment.text,
            context,
            candidates,
        )

        if not result:

            return None

        confidence = float(
            result.get(
                "confidence",
                0.0,
            )
        )

        best_number = int(
            result.get(
                "best_candidate",
                0,
            )
        )

        image_index = number_to_image_index.get(
            best_number
        )

        if image_index is None:

            return None

        return {
            "image_index": image_index,
            "confidence": confidence,
            "reason": result.get(
                "reason",
                "",
            ),
        }

    # --------------------------------------------------
    # Anchor discovery
    # --------------------------------------------------

    def find_anchor_candidates(
        self,
        transcript,
        images,
        scores,
        contexts,
    ):

        anchors = []

        segment_count = len(
            transcript
        )

        image_count = len(
            images
        )

        if self.logger:

            self.logger("")
            self.logger("=" * 70)
            self.logger("Finding global anchors")
            self.logger("=" * 70)

        for segment_index, segment in enumerate(
            transcript
        ):

            expected_image = round(
                (
                    segment_index
                    / max(1, segment_count - 1)
                )
                * max(0, image_count - 1)
            )

            # ----------------------------------------
            # Direct OCR anchors
            # ----------------------------------------

            ocr_candidates = self.top_indices(
                scores,
                segment_index,
                "ocr_current",
                self.top_ocr_candidates,
            )

            best_ocr_index = ocr_candidates[0]

            best_ocr_detail = scores[
                segment_index
            ][
                best_ocr_index
            ]

            best_ocr = best_ocr_detail[
                "ocr_current"
            ]

            if best_ocr >= self.strong_ocr_threshold:

                anchors.append(
                    {
                        "segment_index": segment_index,
                        "image_index": best_ocr_index,
                        "confidence": min(
                            0.95,
                            0.62 + best_ocr * 0.35,
                        ),
                        "type": "cheap_ocr",
                        "score": best_ocr,
                        "reason": "Strong direct OCR match.",
                    }
                )

            # ----------------------------------------
            # Qwen OCR judge anchors
            # ----------------------------------------

            if best_ocr >= self.medium_ocr_threshold:

                judge_result = self.run_ocr_judge(
                    segment,
                    contexts[segment_index],
                    images,
                    ocr_candidates,
                )

                if judge_result:

                    judge_confidence = judge_result[
                        "confidence"
                    ]

                    if judge_confidence >= self.judge_anchor_threshold:

                        anchors.append(
                            {
                                "segment_index": segment_index,
                                "image_index": judge_result["image_index"],
                                "confidence": min(
                                    0.98,
                                    judge_confidence,
                                ),
                                "type": "qwen_ocr",
                                "score": judge_confidence,
                                "reason": judge_result.get(
                                    "reason",
                                    "",
                                ),
                            }
                        )

            # ----------------------------------------
            # Direct scene anchors
            # ----------------------------------------

            scene_candidates = self.top_indices(
                scores,
                segment_index,
                "scene_semantic",
                self.top_scene_candidates,
            )

            best_scene_index = scene_candidates[0]

            best_scene_detail = scores[
                segment_index
            ][
                best_scene_index
            ]

            best_scene = best_scene_detail[
                "scene_semantic"
            ]

            if best_scene >= self.strong_scene_threshold:

                anchors.append(
                    {
                        "segment_index": segment_index,
                        "image_index": best_scene_index,
                        "confidence": min(
                            0.82,
                            0.40 + best_scene * 0.50,
                        ),
                        "type": "cheap_scene",
                        "score": best_scene,
                        "reason": "Strong scene similarity.",
                    }
                )

            # ----------------------------------------
            # Qwen scene judge anchors
            # ----------------------------------------

            if best_scene >= 0.34:

                scene_judge_result = self.run_scene_judge(
                    segment,
                    contexts[segment_index],
                    images,
                    scene_candidates,
                )

                if scene_judge_result:

                    scene_confidence = scene_judge_result[
                        "confidence"
                    ]

                    if scene_confidence >= 0.68:

                        anchors.append(
                            {
                                "segment_index": segment_index,
                                "image_index": scene_judge_result["image_index"],
                                "confidence": min(
                                    0.90,
                                    scene_confidence,
                                ),
                                "type": "qwen_scene",
                                "score": scene_confidence,
                                "reason": scene_judge_result.get(
                                    "reason",
                                    "",
                                ),
                            }
                        )

            # ----------------------------------------
            # Weak progress fallback
            # ----------------------------------------

            anchors.append(
                {
                    "segment_index": segment_index,
                    "image_index": expected_image,
                    "confidence": 0.12,
                    "type": "progress_fallback",
                    "score": 0.12,
                    "reason": "Expected chapter progress.",
                }
            )

        if self.logger:

            self.logger(
                f"Raw anchor candidates: {len(anchors)}"
            )

        return anchors

    # --------------------------------------------------
    # Anchor cleanup
    # --------------------------------------------------

    def clean_anchors(
        self,
        anchors,
        transcript_count,
        image_count,
    ):

        if not anchors:

            return [
                {
                    "segment_index": 0,
                    "image_index": 0,
                    "confidence": 1.0,
                    "type": "start",
                    "score": 1.0,
                    "reason": "Start.",
                }
            ]

        anchors.append(
            {
                "segment_index": 0,
                "image_index": 0,
                "confidence": 1.0,
                "type": "start",
                "score": 1.0,
                "reason": "Start.",
            }
        )

        anchors.append(
            {
                "segment_index": transcript_count - 1,
                "image_index": image_count - 1,
                "confidence": 0.20,
                "type": "soft_end",
                "score": 0.20,
                "reason": "Soft end progress.",
            }
        )

        by_segment = {}

        for anchor in anchors:

            segment_index = anchor[
                "segment_index"
            ]

            by_segment.setdefault(
                segment_index,
                []
            ).append(
                anchor
            )

        reduced = []

        for segment_index, items in by_segment.items():

            items.sort(
                key=lambda item: item["confidence"],
                reverse=True,
            )

            reduced.extend(
                items[:4]
            )

        reduced.sort(
            key=lambda item: (
                item["segment_index"],
                item["image_index"],
            )
        )

        n = len(
            reduced
        )

        dp = [
            0.0
            for _ in range(n)
        ]

        parent = [
            -1
            for _ in range(n)
        ]

        for i in range(n):

            current = reduced[i]

            weight = current[
                "confidence"
            ]

            if current["type"] in {
                "qwen_ocr",
                "cheap_ocr",
            }:

                weight *= 2.5

            elif current["type"] in {
                "qwen_scene",
                "cheap_scene",
            }:

                weight *= 1.6

            elif current["type"] == "progress_fallback":

                weight *= 0.35

            dp[i] = weight

            for j in range(i):

                previous = reduced[j]

                if previous["segment_index"] >= current["segment_index"]:

                    continue

                if previous["image_index"] > current["image_index"]:

                    continue

                segment_gap = (
                    current["segment_index"]
                    - previous["segment_index"]
                )

                image_gap = (
                    current["image_index"]
                    - previous["image_index"]
                )

                jump_penalty = 0.0

                if segment_gap <= 2 and image_gap >= 12:

                    jump_penalty = 0.25

                elif segment_gap <= 1 and image_gap >= 6:

                    jump_penalty = 0.18

                candidate_score = (
                    dp[j]
                    + weight
                    - jump_penalty
                )

                if candidate_score > dp[i]:

                    dp[i] = candidate_score

                    parent[i] = j

        best_index = max(
            range(n),
            key=lambda index: dp[index],
        )

        chosen = []

        while best_index != -1:

            chosen.append(
                reduced[best_index]
            )

            best_index = parent[
                best_index
            ]

        chosen.reverse()

        final = []

        for anchor in chosen:

            if anchor["type"] != "progress_fallback":

                final.append(
                    anchor
                )

                continue

            keep = True

            for real_anchor in chosen:

                if real_anchor["type"] == "progress_fallback":

                    continue

                if abs(
                    real_anchor["segment_index"]
                    - anchor["segment_index"]
                ) <= 2:

                    keep = False

                    break

            if keep:

                final.append(
                    anchor
                )

        final.sort(
            key=lambda item: item["segment_index"]
        )

        if self.logger:

            self.logger("")
            self.logger("=" * 70)
            self.logger("Cleaned anchors")
            self.logger("=" * 70)

            for anchor in final:

                self.logger(
                    f"Chunk {anchor['segment_index'] + 1} "
                    f"-> Image {anchor['image_index'] + 1} "
                    f"[{anchor['type']}] "
                    f"confidence {anchor['confidence']:.2f} "
                    f"reason: {anchor['reason']}"
                )

        return final

    # --------------------------------------------------
    # Fill between anchors
    # --------------------------------------------------

    def expected_image_between(
        self,
        segment_index,
        left_anchor,
        right_anchor,
    ):

        left_segment = left_anchor[
            "segment_index"
        ]

        right_segment = right_anchor[
            "segment_index"
        ]

        left_image = left_anchor[
            "image_index"
        ]

        right_image = right_anchor[
            "image_index"
        ]

        if right_segment == left_segment:

            return left_image

        progress = (
            segment_index
            - left_segment
        ) / (
            right_segment
            - left_segment
        )

        expected = round(
            left_image
            + progress * (
                right_image
                - left_image
            )
        )

        return expected

    def local_best_near_expected(
        self,
        segment_index,
        scores,
        expected_image,
        min_image,
        max_image,
    ):

        best_index = expected_image

        best_score = -999.0

        radius = 3

        start = max(
            min_image,
            expected_image - radius,
        )

        end = min(
            max_image,
            expected_image + radius,
        )

        for image_index in range(
            start,
            end + 1,
        ):

            detail = scores[
                segment_index
            ][
                image_index
            ]

            distance = abs(
                image_index - expected_image
            )

            score = self.candidate_score(
                detail
            )

            score -= distance * 0.035

            if score > best_score:

                best_score = score

                best_index = image_index

        return best_index

    def fill_timeline(
        self,
        transcript,
        images,
        scores,
        contexts,
        anchors,
    ):

        segment_count = len(
            transcript
        )

        image_count = len(
            images
        )

        if not anchors:

            anchors = [
                {
                    "segment_index": 0,
                    "image_index": 0,
                    "confidence": 1.0,
                    "type": "start",
                    "score": 1.0,
                    "reason": "Start.",
                },
                {
                    "segment_index": segment_count - 1,
                    "image_index": image_count - 1,
                    "confidence": 0.20,
                    "type": "soft_end",
                    "score": 0.20,
                    "reason": "End.",
                },
            ]

        if anchors[0]["segment_index"] != 0:

            anchors.insert(
                0,
                {
                    "segment_index": 0,
                    "image_index": 0,
                    "confidence": 1.0,
                    "type": "start",
                    "score": 1.0,
                    "reason": "Start.",
                },
            )

        if anchors[-1]["segment_index"] != segment_count - 1:

            anchors.append(
                {
                    "segment_index": segment_count - 1,
                    "image_index": min(
                        image_count - 1,
                        anchors[-1]["image_index"] + 4,
                    ),
                    "confidence": 0.15,
                    "type": "soft_end",
                    "score": 0.15,
                    "reason": "Soft end.",
                }
            )

        image_for_segment = [
            0
            for _ in range(segment_count)
        ]

        for anchor_index in range(
            len(anchors) - 1
        ):

            left = anchors[
                anchor_index
            ]

            right = anchors[
                anchor_index + 1
            ]

            left_segment = left[
                "segment_index"
            ]

            right_segment = right[
                "segment_index"
            ]

            left_image = left[
                "image_index"
            ]

            right_image = right[
                "image_index"
            ]

            for segment_index in range(
                left_segment,
                right_segment + 1,
            ):

                expected = self.expected_image_between(
                    segment_index,
                    left,
                    right,
                )

                expected = max(
                    left_image,
                    min(
                        right_image,
                        expected,
                    ),
                )

                chosen = self.local_best_near_expected(
                    segment_index,
                    scores,
                    expected,
                    left_image,
                    right_image,
                )

                image_for_segment[
                    segment_index
                ] = chosen

        for anchor in anchors:

            image_for_segment[
                anchor["segment_index"]
            ] = anchor[
                "image_index"
            ]

        current = 0

        hold_count = 0

        previous_image = 0

        for segment_index in range(
            segment_count
        ):

            chosen = image_for_segment[
                segment_index
            ]

            if chosen < current:

                chosen = current

            if chosen == previous_image:

                hold_count += 1

            else:

                hold_count = 1

            if hold_count > self.comfortable_hold_chunks:

                next_image = min(
                    image_count - 1,
                    chosen + 1,
                )

                current_detail = scores[
                    segment_index
                ][
                    chosen
                ]

                next_detail = scores[
                    segment_index
                ][
                    next_image
                ]

                current_score = self.candidate_score(
                    current_detail
                )

                next_score = self.candidate_score(
                    next_detail
                )

                if next_score + 0.05 >= current_score:

                    chosen = next_image

                    hold_count = 1

            image_for_segment[
                segment_index
            ] = chosen

            current = chosen

            previous_image = chosen

        results = []

        if self.logger:

            self.logger("")
            self.logger("=" * 70)
            self.logger("Final timeline choices")
            self.logger("=" * 70)

        for segment_index in range(
            segment_count
        ):

            image_index = image_for_segment[
                segment_index
            ]

            detail = scores[
                segment_index
            ][
                image_index
            ]

            score = self.candidate_score(
                detail
            )

            if self.logger:

                self.logger("")
                self.logger(
                    f"Chunk {segment_index + 1}: "
                    f"{transcript[segment_index].text}"
                )

                self.logger(
                    f"Chosen image {image_index + 1}: "
                    f"{images[image_index]['file']}"
                )

                self.logger(
                    f"score {score:.3f}, "
                    f"semantic {detail['semantic']:.3f}, "
                    f"scene {detail['scene_semantic']:.3f}, "
                    f"ocr_current {detail['ocr_current']:.3f}, "
                    f"ocr_context {detail['ocr_context']:.3f}"
                )

            results.append(
                {
                    "segment_index": segment_index,
                    "image_index": image_index,
                    "score": score,
                    "semantic": detail["semantic"],
                    "ocr_current": detail["ocr_current"],
                    "ocr_context": detail["ocr_context"],
                    "context": contexts[segment_index],
                }
            )

        return results

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

        if self.logger:

            self.logger("")
            self.logger("=" * 70)
            self.logger("ANCHOR BASED MATCHER")
            self.logger("=" * 70)
            self.logger(
                f"Transcript chunks: {len(transcript)}"
            )
            self.logger(
                f"Images: {len(images)}"
            )

        scores, contexts = self.build_scores(
            transcript,
            images,
        )

        raw_anchors = self.find_anchor_candidates(
            transcript,
            images,
            scores,
            contexts,
        )

        clean_anchors = self.clean_anchors(
            raw_anchors,
            len(transcript),
            len(images),
        )

        results = self.fill_timeline(
            transcript,
            images,
            scores,
            contexts,
            clean_anchors,
        )

        return results