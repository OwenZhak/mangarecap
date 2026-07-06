import json
from pathlib import Path
from xml.sax.saxutils import escape


class FCPXMLExporter:

    def __init__(self, logger=None):

        self.logger = logger

        self.fps = 30

    def seconds_to_time(self, seconds):

        frames = round(float(seconds) * self.fps)

        return f"{frames}/{self.fps}s"

    def file_uri(self, path):

        fixed_path = Path(path).resolve()

        return fixed_path.as_uri()

    def export(
        self,
        audio_path,
        timeline_path,
        output_path,
    ):

        timeline_file = Path(timeline_path)

        if not timeline_file.exists():

            raise FileNotFoundError(
                f"Timeline not found: {timeline_path}"
            )

        with open(
            timeline_file,
            "r",
            encoding="utf8",
        ) as f:

            timeline = json.load(f)

        if not timeline:

            raise ValueError("Timeline is empty.")

        output_file = Path(output_path)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        audio_path = Path(audio_path).resolve()

        if not audio_path.exists():

            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        audio_duration = max(
            float(clip["end"])
            for clip in timeline
        )

        resources = []

        resources.append(
            f'''
        <format id="r1" name="FFVideoFormat1080x1920p30" frameDuration="1/30s" width="1080" height="1920" colorSpace="1-1-1 (Rec. 709)"/>'''
        )

        resources.append(
            f'''
        <asset id="audio1" name="{escape(audio_path.name)}" src="{self.file_uri(audio_path)}" start="0s" duration="{self.seconds_to_time(audio_duration)}" hasAudio="1" audioSources="1" audioChannels="2" audioRate="48000"/>'''
        )

        image_asset_ids = []

        for index, clip in enumerate(timeline, start=1):

            image_path = clip.get("image_path")

            if not image_path:

                raise ValueError(
                    "timeline.json is missing image_path. Run the project again after updating timeline_builder.py."
                )

            image_path = Path(image_path).resolve()

            if not image_path.exists():

                raise FileNotFoundError(
                    f"Image file not found: {image_path}"
                )

            asset_id = f"image{index}"

            image_asset_ids.append(asset_id)

            duration = self.seconds_to_time(
                float(clip["end"]) - float(clip["start"])
            )

            resources.append(
                f'''
        <asset id="{asset_id}" name="{escape(image_path.name)}" src="{self.file_uri(image_path)}" start="0s" duration="{duration}" hasVideo="1" format="r1"/>'''
            )

        spine_items = []

        spine_items.append(
            f'''
                        <asset-clip name="{escape(audio_path.stem)}" ref="audio1" offset="0s" start="0s" duration="{self.seconds_to_time(audio_duration)}" lane="-1"/>'''
        )

        for index, clip in enumerate(timeline):

            asset_id = image_asset_ids[index]

            image_path = Path(
                clip["image_path"]
            ).resolve()

            start = self.seconds_to_time(
                float(clip["start"])
            )

            duration = self.seconds_to_time(
                float(clip["end"]) - float(clip["start"])
            )

            spine_items.append(
                f'''
                        <asset-clip name="{escape(image_path.name)}" ref="{asset_id}" offset="{start}" start="0s" duration="{duration}"/>'''
            )

        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.10">
    <resources>
{''.join(resources)}
    </resources>
    <library>
        <event name="Manga Recap">
            <project name="Manga Recap Project">
                <sequence format="r1" duration="{self.seconds_to_time(audio_duration)}" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
                    <spine>
{''.join(spine_items)}
                    </spine>
                </sequence>
            </project>
        </event>
    </library>
</fcpxml>
'''

        with open(
            output_file,
            "w",
            encoding="utf8",
        ) as f:

            f.write(xml)

        if self.logger:

            self.logger(
                f"FCPXML exported: {output_file}"
            )