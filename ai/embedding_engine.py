from pathlib import Path

from PIL import Image

from sentence_transformers import SentenceTransformer
from sentence_transformers import util


class EmbeddingEngine:

    def __init__(self):

        self.model = SentenceTransformer(
            "clip-ViT-B-32"
        )

    def image_embedding(
        self,
        image_path,
    ):

        image = Image.open(image_path)

        return self.model.encode(
            image,
            convert_to_tensor=True,
        )

    def text_embedding(
        self,
        text,
    ):

        return self.model.encode(
            text,
            convert_to_tensor=True,
        )

    def similarity(
        self,
        image_embedding,
        text_embedding,
    ):

        score = util.cos_sim(
            image_embedding,
            text_embedding,
        )

        return float(score)