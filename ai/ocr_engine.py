import easyocr


class OCREngine:

    def __init__(self):

        self.reader = easyocr.Reader(
            ["en", "ja"],
            gpu=True,
        )

    def extract_text(self, image_path):

        result = self.reader.readtext(
            str(image_path),   # <-- convert Path to string
            detail=0,
            paragraph=True,
        )

        return " ".join(result).strip()