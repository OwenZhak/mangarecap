import json
import re

from ollama import chat


class SceneJudge:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

        # Text-only model.
        # Use qwen2.5:7b if you installed it.
        # If you use qwen3:8b, change this line.
        self.model = "qwen2.5:7b"

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

    def judge(
        self,
        main_voiceover,
        context_voiceover,
        candidates,
    ):

        if not candidates:

            return None

        candidate_text = ""

        for item in candidates:

            candidate_text += (
                f"\nCandidate {item['number']}:\n"
                f"OCR: {item['ocr']}\n"
                f"Scene Summary: {item['summary']}\n"
                f"Possible Event: {item['possible_event']}\n"
                f"Location: {item['location']}\n"
                f"Visible Actions: {item['actions']}\n"
                f"Visible Objects: {item['objects']}\n"
                f"Emotion: {item['emotion']}\n"
            )

        prompt = f"""
You are matching manga panel descriptions to a voiceover narration.

The OCR may be missing or unrelated.
The image descriptions may be imperfect.
Your job is to find which candidate PANEL SCENE best matches the MAIN voiceover chunk.

MAIN voiceover chunk:
{main_voiceover}

Nearby voiceover context:
{context_voiceover}

Candidates:
{candidate_text}

Rules:
- The MAIN voiceover chunk is most important.
- Use nearby context only to understand the story flow.
- Focus on scene meaning, not exact words.
- If the voiceover talks about returning home, a building, house, apartment, entrance, street, hallway, or exterior can be a strong scene match.
- If the voiceover talks about school, classroom, teacher, transfer student, or class, classroom/school panels are strong matches.
- If the voiceover talks about arguing, fighting, confrontation, promise, threat, or emotional tension, panels with characters facing each other or intense expressions may match.
- Do not choose only because names match.
- Do not choose only because OCR matches; OCR is secondary here.
- If none match well, choose the closest one but use low confidence.
- Confidence should be high only when the scene clearly matches the MAIN chunk.
- Return ONLY valid JSON.

Format:
{{
    "best_candidate": 1,
    "confidence": 0.0,
    "reason": "short reason"
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
                    }
                ],
            )

            data = self.extract_json(
                response.message.content
            )

            if not data:

                return None

            best_candidate = int(
                data.get(
                    "best_candidate",
                    0,
                )
            )

            confidence = float(
                data.get(
                    "confidence",
                    0.0,
                )
            )

            reason = str(
                data.get(
                    "reason",
                    "",
                )
            )

            if self.logger:

                self.logger(
                    f"Scene Judge: candidate {best_candidate}, "
                    f"confidence {confidence:.2f}, "
                    f"reason: {reason}"
                )

            return {
                "best_candidate": best_candidate,
                "confidence": confidence,
                "reason": reason,
            }

        except Exception as e:

            if self.logger:

                self.logger(
                    f"Scene Judge failed: {e}"
                )

            return None