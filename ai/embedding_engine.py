import torch

from PIL import Image

from sentence_transformers import SentenceTransformer
from sentence_transformers import util


class EmbeddingEngine:

    def __init__(self):

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.model = SentenceTransformer(
            "clip-ViT-B-32",
            device=self.device,
        )

    def image_embedding(
        self,
        image_path,
    ):

        image = Image.open(image_path)

        return self.model.encode(
            image,
            convert_to_tensor=True,
            device=self.device,
        )

    def text_embedding(
        self,
        text,
    ):

        return self.model.encode(
            text,
            convert_to_tensor=True,
            device=self.device,
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