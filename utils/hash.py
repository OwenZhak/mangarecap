import hashlib
from pathlib import Path


def sha256_file(file_path):

    sha = hashlib.sha256()

    with open(file_path, "rb") as f:

        while True:

            data = f.read(1024 * 1024)

            if not data:
                break

            sha.update(data)

    return sha.hexdigest()