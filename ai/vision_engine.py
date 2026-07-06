import json

from ollama import chat


class VisionEngine:

    def __init__(self, logger=None):

        self.logger = logger

        self.model = "qwen2.5vl:7b"

        if logger:
            logger("Loading Qwen2.5-VL 7b")
            logger("Qwen2.5-VL 7b Ready.")

    def describe(
        self,
        image_path,
        ocr_text,
    ):

        prompt = f"""
You are analyzing ONE manga screenshot.

OCR extracted from speech bubbles:

{ocr_text}

Rules:

- OCR may contain mistakes.
- Use OCR only if it agrees with the artwork.
- Ignore speech bubbles when describing what is visible.
- Never invent clothing, hairstyles, objects or locations.
- If uncertain, write "unknown".
- Report only observable facts.

Return ONLY valid JSON.

{{
    "summary":"",
    "visible_people":[],
    "visible_actions":[],
    "visible_objects":[],
    "possible_event":"",
    "location":"",
    "emotion":"",
    "confidence":0.0
}}
"""

        response = chat(
            model=self.model,
            format="json",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [str(image_path)],
                }
            ],
        )

        return json.loads(
            response.message.content
        )