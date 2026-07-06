import json
from pathlib import Path

from utils.hash import sha256_file


class ImageDatabase:

    def __init__(self):

        self.cache_folder = Path("cache/images")

        self.cache_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

    def image_hash(
        self,
        image_path,
    ):

        return sha256_file(image_path)

    def cache_file(
        self,
        image_path,
    ):

        return (
            self.cache_folder
            / f"{self.image_hash(image_path)}.json"
        )

    def exists(
        self,
        image_path,
    ):

        return self.cache_file(
            image_path
        ).exists()

    def load(
        self,
        image_path,
    ):

        file = self.cache_file(
            image_path
        )

        if not file.exists():
            return None

        with open(
            file,
            "r",
            encoding="utf8",
        ) as f:

            return json.load(f)

    def save(
        self,
        image_path,
        data,
    ):

        with open(
            self.cache_file(image_path),
            "w",
            encoding="utf8",
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False,
            )