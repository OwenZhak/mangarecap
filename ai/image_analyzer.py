from pathlib import Path

from ai.embedding_engine import EmbeddingEngine
from ai.image_database import ImageDatabase
from ai.ocr_engine import OCREngine
from ai.vision_engine import VisionEngine


class ImageAnalyzer:

    def __init__(self, logger=None):

        self.logger = logger

        if logger:
            logger("Loading CLIP...")

        self.embedding = EmbeddingEngine()

        if logger:
            logger("CLIP Ready.")

        if logger:
            logger("Loading OCR...")

        self.ocr = OCREngine()

        if logger:
            logger("OCR Ready.")

        self.vision = VisionEngine(logger)

        self.database = ImageDatabase()

    def analyze(self, image_path):

        cached = self.database.load(image_path)

        if cached:

            if self.logger:
                self.logger(
                    f"Cache hit: {Path(image_path).name}"
                )

            return cached

        self.logger(
            f"Analyzing: {Path(image_path).name}"
        )

        embedding = self.embedding.image_embedding(
            image_path
        )

        ocr = self.ocr.extract_text(
            image_path
        )

        scene = self.vision.describe(
            image_path
        )

        result = {

            "hash":
                self.database.image_hash(
                    image_path
                ),

            "file":
                Path(image_path).name,

            "path":
                str(image_path),

            "ocr":
                ocr,

            "scene":
                scene,

            "embedding":
                embedding.tolist(),

        }

        self.database.save(
            image_path,
            result,
        )

        self.logger("Scene")

        self.logger(
            scene["summary"]
        )

        self.logger("OCR")

        self.logger(ocr)

        self.logger(
            "Saved to cache."
        )

        return result