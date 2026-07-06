import json
from pathlib import Path


class SceneDatabase:

    def __init__(self):

        self.folder = Path("cache/scenes")

        self.folder.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        image_hash,
        data,
    ):

        with open(
            self.folder / f"{image_hash}.json",
            "w",
            encoding="utf8",
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False,
            )