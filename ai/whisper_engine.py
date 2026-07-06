from pathlib import Path
import json
import re

from faster_whisper import WhisperModel


class WhisperEngine:

    def __init__(self):

        self.model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8",
        )

        # Main editing rule:
        # Around 1 image every 5–7 seconds.
        self.target_chunk_seconds = 6.0

        self.min_chunk_seconds = 2.5

        self.max_chunk_seconds = 8.0

        self.max_words = 24

        self.min_words = 5

    # --------------------------------------------------
    # Text helpers
    # --------------------------------------------------

    def clean_text(
        self,
        text,
    ):

        text = str(text).strip()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        text = re.sub(
            r"\s+([,.!?;:])",
            r"\1",
            text,
        )

        return text.strip()

    def ends_sentence(
        self,
        text,
    ):

        text = self.clean_text(
            text
        )

        if not text:
            return False

        return text.endswith(
            (
                ".",
                "?",
                "!",
                "…",
                "。",
                "？",
                "！",
            )
        )

    # --------------------------------------------------
    # Word extraction
    # --------------------------------------------------

    def collect_words(
        self,
        segments,
    ):

        words = []

        for segment in segments:

            segment_words = getattr(
                segment,
                "words",
                None,
            )

            if segment_words:

                for word in segment_words:

                    word_text = self.clean_text(
                        getattr(
                            word,
                            "word",
                            "",
                        )
                    )

                    if not word_text:
                        continue

                    words.append(
                        {
                            "start": float(
                                getattr(
                                    word,
                                    "start",
                                    segment.start,
                                )
                            ),
                            "end": float(
                                getattr(
                                    word,
                                    "end",
                                    segment.end,
                                )
                            ),
                            "text": word_text,
                        }
                    )

            else:

                text = self.clean_text(
                    segment.text
                )

                if not text:
                    continue

                words.append(
                    {
                        "start": float(
                            segment.start
                        ),
                        "end": float(
                            segment.end
                        ),
                        "text": text,
                    }
                )

        return words

    # --------------------------------------------------
    # Editing chunks
    # --------------------------------------------------

    def should_close_chunk(
        self,
        chunk_words,
        chunk_start,
        current_end,
        is_sentence_end,
    ):

        if not chunk_words:
            return False

        word_count = len(
            chunk_words
        )

        duration = current_end - chunk_start

        if (
            is_sentence_end
            and duration >= self.min_chunk_seconds
            and word_count >= self.min_words
        ):

            return True

        if duration >= self.target_chunk_seconds:

            return True

        if duration >= self.max_chunk_seconds:

            return True

        if word_count >= self.max_words:

            return True

        return False

    def merge_into_editing_chunks(
        self,
        words,
        log_callback=None,
    ):

        chunks = []

        chunk_words = []

        chunk_start = None

        chunk_end = None

        for word in words:

            text = word["text"]

            if chunk_start is None:

                chunk_start = word["start"]

            chunk_end = word["end"]

            chunk_words.append(
                text
            )

            combined_text = self.clean_text(
                " ".join(
                    chunk_words
                )
            )

            close_chunk = self.should_close_chunk(
                chunk_words,
                chunk_start,
                chunk_end,
                self.ends_sentence(
                    combined_text
                ),
            )

            if close_chunk:

                chunks.append(
                    {
                        "start": chunk_start,
                        "end": chunk_end,
                        "text": combined_text,
                    }
                )

                chunk_words = []

                chunk_start = None

                chunk_end = None

        if chunk_words:

            combined_text = self.clean_text(
                " ".join(
                    chunk_words
                )
            )

            chunks.append(
                {
                    "start": chunk_start,
                    "end": chunk_end,
                    "text": combined_text,
                }
            )

        if log_callback:

            log_callback("")
            log_callback("Editing transcript chunks:")
            log_callback("-" * 60)

            for index, item in enumerate(
                chunks,
                start=1,
            ):

                duration = item["end"] - item["start"]

                log_callback(
                    f"{index}. [{duration:.1f}s] {item['text']}"
                )

            log_callback("-" * 60)

            log_callback(
                f"Total editing chunks: {len(chunks)}"
            )

        return chunks

    # --------------------------------------------------
    # Transcribe
    # --------------------------------------------------

    def transcribe(
        self,
        audio_path,
        progress_callback=None,
        log_callback=None,
    ):

        if log_callback:

            log_callback(
                "Loading Whisper model..."
            )

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
        )

        segments = list(
            segments
        )

        if log_callback:

            log_callback("")
            log_callback("Raw Whisper chunks:")
            log_callback("-" * 60)

            for segment in segments:

                text = self.clean_text(
                    segment.text
                )

                if text:

                    log_callback(
                        text
                    )

            log_callback("-" * 60)

        words = self.collect_words(
            segments
        )

        if progress_callback:

            progress_callback(
                100
            )

        editing_chunks = self.merge_into_editing_chunks(
            words,
            log_callback,
        )

        return editing_chunks

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

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
            encoding="utf8",
        ) as f:

            json.dump(
                transcript,
                f,
                indent=4,
                ensure_ascii=False,
            )