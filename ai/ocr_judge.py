import json
import re

from ollama import chat


class OCRJudge:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

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
            )

        prompt = f"""
You are matching manga OCR text to a voiceover narration.

The OCR may contain mistakes.
The voiceover may paraphrase the OCR.
Your job is to find which candidate OCR has the same meaning as the MAIN voiceover chunk.

MAIN voiceover chunk:
{main_voiceover}

Nearby voiceover context:
{context_voiceover}

Candidates:
{candidate_text}

Rules:
- The MAIN voiceover chunk is most important.
- Use nearby context only to understand the scene and meaning.
- Focus on meaning, not exact wording.
- If the voiceover says "he would never let her reincarnate" and OCR says "I won't let you reincarnate", that is a strong match.
- If the voiceover says "the teacher wanted to support him" and OCR says "as a teacher I have a duty to support students", that is a strong match.
- If names are slightly wrong because OCR misread them, still judge by meaning.
- Do not choose a candidate only because it has the same character names.
- If none match well, choose the closest one but use low confidence.
- Confidence should be high only when the OCR directly matches or strongly paraphrases the MAIN chunk.
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
                    f"OCR Judge: candidate {best_candidate}, "
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
                    f"OCR Judge failed: {e}"
                )

            return None