import json
import re

from ollama import chat


class VisionEngine:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

        self.model = "qwen2.5vl:7b"

        if logger:

            logger(
                "Loading Qwen2.5-VL 7B..."
            )

            logger(
                "Qwen2.5-VL 7B Ready."
            )

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def extract_json(
        self,
        text,
    ):

        text = str(text).strip()

        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL,
        )

        if not match:

            return None

        try:

            return json.loads(
                match.group(0)
            )

        except Exception:

            return None

    def safe_scene(
        self,
        data,
    ):

        if not isinstance(data, dict):

            data = {}

        return {
            "summary": str(
                data.get(
                    "summary",
                    "",
                )
            ),
            "detailed_description": str(
                data.get(
                    "detailed_description",
                    "",
                )
            ),
            "visible_people": data.get(
                "visible_people",
                [],
            ),
            "character_details": data.get(
                "character_details",
                [],
            ),
            "visible_actions": data.get(
                "visible_actions",
                [],
            ),
            "body_language": data.get(
                "body_language",
                [],
            ),
            "facial_expressions": data.get(
                "facial_expressions",
                [],
            ),
            "visible_objects": data.get(
                "visible_objects",
                [],
            ),
            "background_details": data.get(
                "background_details",
                [],
            ),
            "location": str(
                data.get(
                    "location",
                    "unknown",
                )
            ),
            "camera_framing": str(
                data.get(
                    "camera_framing",
                    "unknown",
                )
            ),
            "emotion": str(
                data.get(
                    "emotion",
                    "unknown",
                )
            ),
            "possible_event": str(
                data.get(
                    "possible_event",
                    "",
                )
            ),
            "story_function": str(
                data.get(
                    "story_function",
                    "",
                )
            ),
            "narration_keywords": data.get(
                "narration_keywords",
                [],
            ),
            "matchable_phrases": data.get(
                "matchable_phrases",
                [],
            ),
            "ocr_interpretation": str(
                data.get(
                    "ocr_interpretation",
                    "",
                )
            ),
            "confidence": float(
                data.get(
                    "confidence",
                    0.0,
                )
            ),
        }

    # --------------------------------------------------
    # Main vision call
    # --------------------------------------------------

    def describe(
        self,
        image_path,
        ocr_text,
    ):

        prompt = f"""
You are analyzing ONE manga panel or manga screenshot for an automatic video editor.

The editor will match this image to a voiceover narration.
So your job is NOT to be short.
Your job is to describe everything useful for matching this image to a story recap.

OCR text found in speech bubbles or text boxes:
{ocr_text}

Important rules:

- OCR may be wrong or incomplete.
- Use OCR only as supporting information.
- First describe what is visually visible.
- Do not invent things that are not visible.
- If something is unclear, write "unknown".
- Manga panels are black and white, so do not guess colors.
- Do not simply write "a person" if you can describe pose, expression, clothing, hair, and action.
- If there is no OCR, still describe the image in detail.
- Focus on details useful for matching a voiceover.
- Describe the scene as if a human editor needs to know when to use this panel.
- Return ONLY valid JSON.

Write detailed but factual descriptions.

JSON format:

{{
    "summary": "One clear sentence describing the whole panel.",
    "detailed_description": "Longer description of the panel, including characters, pose, expressions, background, objects, and what seems to be happening.",
    "visible_people": [
        "short description of each visible person"
    ],
    "character_details": [
        "hair, clothing, age impression, gender impression if obvious, posture, position in frame"
    ],
    "visible_actions": [
        "observable actions only"
    ],
    "body_language": [
        "standing, leaning, grabbing, running, looking away, tense posture, relaxed posture, etc"
    ],
    "facial_expressions": [
        "surprised, embarrassed, angry, smiling, crying, serious, blank, etc"
    ],
    "visible_objects": [
        "phones, books, bags, desks, doors, beds, food, papers, weapons, etc"
    ],
    "background_details": [
        "classroom, hallway, bedroom, street, building exterior, sky, window, furniture, crowd, blank background, speed lines, etc"
    ],
    "location": "best guess location, or unknown",
    "camera_framing": "close-up, bust shot, half body, full body, two-shot, group shot, wide shot, etc",
    "emotion": "main emotional feeling of the panel",
    "possible_event": "What story event this panel likely shows, based only on visible evidence and OCR.",
    "story_function": "How this panel might be used in a recap, for example introduction, reaction, confrontation, confession, explanation, transition, reveal, comedy beat, emotional moment, action moment.",
    "narration_keywords": [
        "single words useful for matching narration"
    ],
    "matchable_phrases": [
        "short phrases a voiceover might say when this image appears"
    ],
    "ocr_interpretation": "If OCR is readable, summarize its meaning. If OCR is empty or unclear, write unknown.",
    "confidence": 0.0
}}
"""

        try:

            response = chat(
                model=self.model,
                format="json",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [
                            str(image_path)
                        ],
                    }
                ],
            )

            data = self.extract_json(
                response.message.content
            )

            return self.safe_scene(
                data
            )

        except Exception as e:

            if self.logger:

                self.logger(
                    f"Vision failed: {e}"
                )

            return self.safe_scene(
                {}
            )