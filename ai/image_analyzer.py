from pathlib import Path

from ai.embedding_engine import EmbeddingEngine
from ai.image_database import ImageDatabase


class ImageAnalyzer:

    def __init__(self):

        self.embedding = EmbeddingEngine()

        self.database = ImageDatabase()

    def analyze(
        self,
        image_path,
    ):

        cached = self.database.load(
            image_path
        )

        if cached is not None:

            return cached

        embedding = self.embedding.image_embedding(
            image_path
        )

        result = {

            "hash": self.database.image_hash(
                image_path
            ),

            "file": str(
                Path(image_path).name
            ),

            "path": str(
                Path(image_path)
            ),

            "embedding": embedding.tolist(),
        }

        self.database.save(
            image_path,
            result,
        )

        return result