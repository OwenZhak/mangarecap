import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape


class ResolveXMLExporter:

    def __init__(self, logger=None):

        self.logger = logger

        self.fps = 30

        self.width = 1080

        self.height = 1920

    def seconds_to_frames(self, seconds):

        return int(round(float(seconds) * self.fps))

    def path_url(self, path):

        return Path(path).resolve().as_uri()

    def rate_xml(self):

        return f"""
                    <rate>
                        <timebase>{self.fps}</timebase>
                        <ntsc>FALSE</ntsc>
                    </rate>"""

    def letter_name(self, index):

        letters = "abcdefghijklmnopqrstuvwxyz"

        name = ""

        index = index + 1

        while index > 0:

            index -= 1

            name = letters[index % 26] + name

            index //= 26

        return name.rjust(4, "a")

    def copy_image_to_media_folder(
        self,
        source_path,
        media_folder,
        index,
    ):

        source_path = Path(source_path).resolve()

        extension = source_path.suffix.lower()

        safe_letters = self.letter_name(index)

        safe_name = f"manga_{safe_letters}{extension}"

        target_path = media_folder / safe_name

        shutil.copy2(
            source_path,
            target_path,
        )

        return target_path

    def prepare_video_clips(
        self,
        timeline,
        media_folder,
        total_frames,
    ):

        prepared = []

        for index, clip in enumerate(timeline):

            source_image_path = clip.get("image_path")

            if not source_image_path:

                raise ValueError(
                    "timeline.json is missing image_path."
                )

            source_image_path = Path(
                source_image_path
            ).resolve()

            if not source_image_path.exists():

                raise FileNotFoundError(
                    f"Image file not found: {source_image_path}"
                )

            safe_image_path = self.copy_image_to_media_folder(
                source_image_path,
                media_folder,
                index,
            )

            start_frame = self.seconds_to_frames(
                clip["start"]
            )

            if index + 1 < len(timeline):

                end_frame = self.seconds_to_frames(
                    timeline[index + 1]["start"]
                )

            else:

                end_frame = total_frames

            if index == 0:

                start_frame = 0

            if end_frame <= start_frame:

                end_frame = start_frame + 1

            duration_frames = end_frame - start_frame

            prepared.append(
                {
                    "index": index + 1,
                    "path": safe_image_path,
                    "name": safe_image_path.name,
                    "start": start_frame,
                    "end": end_frame,
                    "duration": duration_frames,
                }
            )

        return prepared

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

        audio_path = Path(audio_path).resolve()

        if not audio_path.exists():

            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        output_file = Path(output_path)

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        media_folder = output_file.parent / "media"

        media_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        total_frames = self.seconds_to_frames(
            max(float(clip["end"]) for clip in timeline)
        )

        prepared_clips = self.prepare_video_clips(
            timeline,
            media_folder,
            total_frames,
        )

        video_clips_xml = []

        for clip in prepared_clips:

            image_path = clip["path"]

            image_name = escape(
                clip["name"]
            )

            file_id = f"file-image-{clip['index']}"

            video_clips_xml.append(
                f"""
                    <clipitem id="video-clip-{clip['index']}">
                        <name>{image_name}</name>
                        <duration>{clip['duration']}</duration>
{self.rate_xml()}
                        <start>{clip['start']}</start>
                        <end>{clip['end']}</end>
                        <in>0</in>
                        <out>{clip['duration']}</out>
                        <stillframe>TRUE</stillframe>
                        <file id="{file_id}">
                            <name>{image_name}</name>
                            <pathurl>{self.path_url(image_path)}</pathurl>
{self.rate_xml()}
                            <duration>1</duration>
                            <media>
                                <video>
                                    <samplecharacteristics>
{self.rate_xml()}
                                        <width>{self.width}</width>
                                        <height>{self.height}</height>
                                        <anamorphic>FALSE</anamorphic>
                                        <pixelaspectratio>square</pixelaspectratio>
                                        <fielddominance>none</fielddominance>
                                    </samplecharacteristics>
                                </video>
                            </media>
                        </file>
                    </clipitem>"""
            )

        audio_name = escape(
            audio_path.name
        )

        audio_clip_xml = f"""
                    <clipitem id="audio-clip-1">
                        <name>{audio_name}</name>
                        <duration>{total_frames}</duration>
{self.rate_xml()}
                        <start>0</start>
                        <end>{total_frames}</end>
                        <in>0</in>
                        <out>{total_frames}</out>
                        <file id="file-audio-1">
                            <name>{audio_name}</name>
                            <pathurl>{self.path_url(audio_path)}</pathurl>
{self.rate_xml()}
                            <duration>{total_frames}</duration>
                            <media>
                                <audio>
                                    <samplecharacteristics>
                                        <depth>16</depth>
                                        <samplerate>48000</samplerate>
                                    </samplecharacteristics>
                                    <channelcount>2</channelcount>
                                </audio>
                            </media>
                        </file>
                    </clipitem>"""

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="5">
    <sequence id="manga-recap-sequence">
        <name>Manga Recap Project</name>
        <duration>{total_frames}</duration>
{self.rate_xml()}
        <timecode>
{self.rate_xml()}
            <string>00:00:00:00</string>
            <frame>0</frame>
            <displayformat>NDF</displayformat>
        </timecode>
        <media>
            <video>
                <format>
                    <samplecharacteristics>
{self.rate_xml()}
                        <width>{self.width}</width>
                        <height>{self.height}</height>
                        <anamorphic>FALSE</anamorphic>
                        <pixelaspectratio>square</pixelaspectratio>
                        <fielddominance>none</fielddominance>
                    </samplecharacteristics>
                </format>
                <track>
{''.join(video_clips_xml)}
                </track>
            </video>
            <audio>
                <numOutputChannels>2</numOutputChannels>
                <track>
{audio_clip_xml}
                </track>
            </audio>
        </media>
    </sequence>
</xmeml>
"""

        with open(
            output_file,
            "w",
            encoding="utf8",
        ) as f:

            f.write(xml)

        if self.logger:

            self.logger(
                f"Copied media to: {media_folder}"
            )

            self.logger(
                f"Resolve XML exported: {output_file}"
            )