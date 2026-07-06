from pathlib import Path
import json

from faster_whisper import WhisperModel


class WhisperEngine:

    def __init__(self):

        self.model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"
        )

    def transcribe(
        self,
        audio_path,
        progress_callback=None,
        log_callback=None,
    ):

        if log_callback:
            log_callback("Loading Whisper model...")

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
        )

        transcript = []

        segments = list(segments)

        total = len(segments)

        for i, segment in enumerate(segments):

            transcript.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
            })

            if progress_callback:

                progress = int(
                    ((i + 1) / total) * 100
                )

                progress_callback(progress)

            if log_callback:

                log_callback(
                    segment.text.strip()
                )

        return transcript

    def save_json(
        self,
        transcript,
        output_file,
    ):

        Path(output_file).parent.mkdir(
            exist_ok=True
        )

        with open(
            output_file,
            "w",
            encoding="utf8"
        ) as f:

            json.dump(
                transcript,
                f,
                indent=4,
                ensure_ascii=False,
            )