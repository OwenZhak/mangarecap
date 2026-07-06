from datetime import datetime
from pathlib import Path


class Logger:

    def __init__(self):

        self.log_folder = Path("logs")

        self.log_folder.mkdir(exist_ok=True)

        self.log_file = (
            self.log_folder
            / "application.log"
        )

    def _write(
        self,
        level: str,
        message: str,
    ):

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        line = (
            f"[{timestamp}] "
            f"[{level}] "
            f"{message}\n"
        )

        with open(
            self.log_file,
            "a",
            encoding="utf8",
        ) as f:

            f.write(line)

        print(line, end="")

    def info(self, message):

        self._write(
            "INFO",
            message,
        )

    def warning(self, message):

        self._write(
            "WARNING",
            message,
        )

    def error(self, message):

        self._write(
            "ERROR",
            message,
        )