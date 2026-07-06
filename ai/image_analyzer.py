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
            image_path,
            ocr,
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

        self.logger("=" * 60)

        self.logger("Scene Summary:")
        self.logger(scene["summary"])

        self.logger("")

        self.logger("Possible Event:")
        self.logger(scene["possible_event"])

        self.logger("")

        self.logger("People:")
        for person in scene["visible_people"]:
            self.logger(f" - {person}")

        self.logger("")

        self.logger("Actions:")
        for action in scene["visible_actions"]:
            self.logger(f" - {action}")

        self.logger("")

        self.logger("Objects:")
        for obj in scene["visible_objects"]:
            self.logger(f" - {obj}")

        self.logger("")

        self.logger(f"Location: {scene['location']}")
        self.logger(f"Emotion: {scene['emotion']}")
        self.logger(f"Confidence: {scene['confidence']}")

        self.logger("")

        self.logger("OCR:")
        self.logger(ocr)

        self.logger("=" * 60)

        self.logger("Saved to cache.")

        return result