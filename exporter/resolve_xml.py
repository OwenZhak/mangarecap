from pathlib import Path


class ResolveXMLExporter:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

    def export(
        self,
        project,
        output_file,
    ):

        Path(output_file).parent.mkdir(
            exist_ok=True
        )

        with open(
            output_file,
            "w",
            encoding="utf8",
        ) as f:

            f.write(
                "<?xml version='1.0'?>\n"
            )

            f.write(
                "<!-- Resolve exporter coming next -->"
            )

        if self.logger:

            self.logger(
                f"Exported {output_file}"
            )