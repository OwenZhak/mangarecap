import cv2
import numpy as np


class ImagePreprocessor:

    def preprocess_for_ocr(self, image_path):

        image = cv2.imread(str(image_path))

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.GaussianBlur(
            gray,
            (3, 3),
            0
        )

        gray = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )[1]

        return gray