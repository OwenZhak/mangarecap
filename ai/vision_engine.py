import json
from ollama import chat


class VisionEngine:

    def __init__(self, logger=None):

        self.logger = logger

        if logger:
            logger("Loading Qwen2.5-VL...")

        self.model = "qwen2.5vl:3b"

        if logger:
            logger("Qwen2.5-VL Ready.")

    def describe(self, image_path):

        prompt = """
You are analyzing a manga screenshot.

Return ONLY valid JSON.

{
  "summary":"",
  "characters":[],
  "actions":[],
  "emotion":"",
  "location":""
}

Rules:

- Ignore speech bubbles.
- Ignore narration boxes.
- Ignore text.
- Focus ONLY on the artwork.
- Keep summary under 30 words.
"""

        response = chat(

            model=self.model,

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "images": [str(image_path)],
                }
            ],

            format="json",
        )

        return json.loads(
            response.message.content
        )