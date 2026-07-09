import copy
import json
import shutil
import uuid
import wave
import subprocess
from pathlib import Path
from datetime import datetime


class CapCutExporter:

    def __init__(
        self,
        logger=None,
    ):

        self.logger = logger

        self.capcut_root = (
            Path.home()
            / "AppData"
            / "Local"
            / "CapCut"
            / "User Data"
            / "Projects"
            / "com.lveditor.draft"
        )

        self.template_name = "MangaRecapTemplate"

        self.width = 1080

        self.height = 1920

    # --------------------------------------------------
    # Logging
    # --------------------------------------------------

    def log(
        self,
        message,
    ):

        if self.logger:

            self.logger(
                message
            )

    # --------------------------------------------------
    # Basic helpers
    # --------------------------------------------------

    def make_id(
        self,
    ):

        return str(
            uuid.uuid4()
        ).upper()

    def seconds_to_microseconds(
        self,
        seconds,
    ):

        return int(
            round(
                float(seconds) * 1000000
            )
        )

    def safe_project_name(
        self,
    ):

        timestamp = datetime.now().strftime(
            "%Y_%m_%d_%H_%M_%S"
        )

        return f"MangaRecap_{timestamp}"

    def audio_duration_seconds(
        self,
        audio_path,
    ):

        audio_path = Path(
            audio_path
        )

        if audio_path.suffix.lower() == ".wav":

            try:

                with wave.open(
                    str(audio_path),
                    "rb",
                ) as wav_file:

                    frames = wav_file.getnframes()

                    rate = wav_file.getframerate()

                    return frames / float(rate)

            except Exception:

                pass

        try:

            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            return float(
                result.stdout.strip()
            )

        except Exception:

            self.log(
                "Could not read audio duration with ffprobe. Using 180 seconds."
            )

            return 180.0

    # --------------------------------------------------
    # Template project
    # --------------------------------------------------

    def find_template_project(
        self,
    ):

        if not self.capcut_root.exists():

            raise FileNotFoundError(
                f"CapCut project folder not found: {self.capcut_root}"
            )

        for folder in self.capcut_root.iterdir():

            if not folder.is_dir():

                continue

            if self.template_name.lower() in folder.name.lower():

                return folder

            draft_file = folder / "draft_content.json"

            if not draft_file.exists():

                continue

            try:

                with open(
                    draft_file,
                    "r",
                    encoding="utf8",
                ) as f:

                    data = json.load(
                        f
                    )

                project_name = str(
                    data.get(
                        "name",
                        "",
                    )
                )

                if self.template_name.lower() in project_name.lower():

                    return folder

            except Exception:

                continue

        raise FileNotFoundError(
            "Could not find CapCut template project named MangaRecapTemplate."
        )

    def copy_template_project(
        self,
        output_name,
    ):

        template_folder = self.find_template_project()

        new_project_folder = (
            self.capcut_root
            / output_name
        )

        if new_project_folder.exists():

            shutil.rmtree(
                new_project_folder
            )

        shutil.copytree(
            template_folder,
            new_project_folder,
        )

        self.log(
            f"Copied template: {template_folder.name}"
        )

        self.log(
            f"New CapCut project: {new_project_folder}"
        )

        return new_project_folder

    # --------------------------------------------------
    # Media
    # --------------------------------------------------

    def prepare_media_folder(
        self,
        project_folder,
    ):

        media_folder = (
            project_folder
            / "mangarecap_media"
        )

        if media_folder.exists():

            shutil.rmtree(
                media_folder
            )

        media_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        return media_folder

    def copy_media_from_timeline(
        self,
        audio_path,
        timeline,
        project_folder,
    ):

        media_folder = self.prepare_media_folder(
            project_folder
        )

        source_to_copied = {}

        copied_timeline = []

        for index, item in enumerate(
            timeline,
            start=1,
        ):

            source_image = Path(
                item["image_path"]
            ).resolve()

            if not source_image.exists():

                raise FileNotFoundError(
                    f"Timeline image not found: {source_image}"
                )

            source_key = str(
                source_image
            )

            if source_key not in source_to_copied:

                extension = source_image.suffix.lower()

                new_name = f"image_{len(source_to_copied) + 1:04d}{extension}"

                new_path = media_folder / new_name

                shutil.copy2(
                    source_image,
                    new_path,
                )

                source_to_copied[source_key] = new_path

            copied_item = dict(
                item
            )

            copied_item["image_path"] = str(
                source_to_copied[source_key]
            )

            copied_timeline.append(
                copied_item
            )

        audio_path = Path(
            audio_path
        ).resolve()

        audio_extension = audio_path.suffix.lower()

        copied_audio = (
            media_folder
            / f"voiceover{audio_extension}"
        )

        shutil.copy2(
            audio_path,
            copied_audio,
        )

        self.log(
            f"Copied {len(source_to_copied)} unique timeline images."
        )

        self.log(
            f"Copied audio: {copied_audio.name}"
        )

        return copied_audio, copied_timeline

    def copy_media_simple(
        self,
        audio_path,
        image_paths,
        project_folder,
    ):

        media_folder = self.prepare_media_folder(
            project_folder
        )

        copied_images = []

        for index, image_path in enumerate(
            image_paths,
            start=1,
        ):

            image_path = Path(
                image_path
            ).resolve()

            extension = image_path.suffix.lower()

            new_name = f"image_{index:04d}{extension}"

            new_path = media_folder / new_name

            shutil.copy2(
                image_path,
                new_path,
            )

            copied_images.append(
                new_path
            )

        audio_path = Path(
            audio_path
        ).resolve()

        audio_extension = audio_path.suffix.lower()

        copied_audio = (
            media_folder
            / f"voiceover{audio_extension}"
        )

        shutil.copy2(
            audio_path,
            copied_audio,
        )

        self.log(
            f"Copied {len(copied_images)} images."
        )

        self.log(
            f"Copied audio: {copied_audio.name}"
        )

        return copied_audio, copied_images

    # --------------------------------------------------
    # Draft loading
    # --------------------------------------------------

    def load_draft(
        self,
        project_folder,
    ):

        draft_file = (
            project_folder
            / "draft_content.json"
        )

        if not draft_file.exists():

            raise FileNotFoundError(
                f"draft_content.json not found: {draft_file}"
            )

        with open(
            draft_file,
            "r",
            encoding="utf8",
        ) as f:

            data = json.load(
                f
            )

        return draft_file, data

    def save_draft(
        self,
        draft_file,
        data,
    ):

        with open(
            draft_file,
            "w",
            encoding="utf8",
        ) as f:

            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False,
            )

    # --------------------------------------------------
    # Template extraction
    # --------------------------------------------------

    def get_tracks(
        self,
        data,
    ):

        tracks = data.get(
            "tracks",
            [],
        )

        video_track = None

        audio_track = None

        for track in tracks:

            track_type = track.get(
                "type",
                "",
            )

            segments = track.get(
                "segments",
                [],
            )

            if not segments:

                continue

            if track_type == "video" and video_track is None:

                video_track = track

            if track_type == "audio" and audio_track is None:

                audio_track = track

        if video_track is None:

            raise ValueError(
                "Template project has no video track with a clip."
            )

        if audio_track is None:

            raise ValueError(
                "Template project has no audio track with a clip. Add one audio file to MangaRecapTemplate."
            )

        return video_track, audio_track

    def ensure_materials(
        self,
        data,
    ):

        if "materials" not in data:

            data["materials"] = {}

        materials = data["materials"]

        if "videos" not in materials:

            materials["videos"] = []

        if "audios" not in materials:

            materials["audios"] = []

        return materials

    def find_material(
        self,
        materials_list,
        material_id,
    ):

        for material in materials_list:

            if material.get("id") == material_id:

                return material

        raise ValueError(
            f"Template material not found: {material_id}"
        )

    def get_template_parts(
        self,
        data,
    ):

        materials = self.ensure_materials(
            data
        )

        video_track, audio_track = self.get_tracks(
            data
        )

        video_segment = copy.deepcopy(
            video_track["segments"][0]
        )

        audio_segment = copy.deepcopy(
            audio_track["segments"][0]
        )

        video_material_id = video_segment.get(
            "material_id"
        )

        audio_material_id = audio_segment.get(
            "material_id"
        )

        video_material = copy.deepcopy(
            self.find_material(
                materials["videos"],
                video_material_id,
            )
        )

        audio_material = copy.deepcopy(
            self.find_material(
                materials["audios"],
                audio_material_id,
            )
        )

        return {
            "video_track": copy.deepcopy(video_track),
            "audio_track": copy.deepcopy(audio_track),
            "video_segment": video_segment,
            "audio_segment": audio_segment,
            "video_material": video_material,
            "audio_material": audio_material,
        }

    # --------------------------------------------------
    # Recursive update helpers
    # --------------------------------------------------

    def update_paths_recursive(
        self,
        value,
        new_path,
        new_name,
    ):

        path_keys = {
            "path",
            "file_path",
            "filepath",
            "local_path",
            "music_path",
            "audio_path",
            "video_path",
            "source_path",
            "material_path",
        }

        name_keys = {
            "name",
            "material_name",
            "file_name",
            "filename",
            "display_name",
        }

        if isinstance(value, dict):

            for key in list(value.keys()):

                lowered = str(key).lower()

                if lowered in path_keys:

                    value[key] = str(
                        new_path
                    )

                elif lowered in name_keys:

                    value[key] = str(
                        new_name
                    )

                else:

                    self.update_paths_recursive(
                        value[key],
                        new_path,
                        new_name,
                    )

        elif isinstance(value, list):

            for item in value:

                self.update_paths_recursive(
                    item,
                    new_path,
                    new_name,
                )

    def update_duration_recursive(
        self,
        value,
        duration_us,
    ):

        if isinstance(value, dict):

            for key in list(value.keys()):

                lowered = str(key).lower()

                if lowered == "duration":

                    value[key] = duration_us

                else:

                    self.update_duration_recursive(
                        value[key],
                        duration_us,
                    )

        elif isinstance(value, list):

            for item in value:

                self.update_duration_recursive(
                    item,
                    duration_us,
                )

    # --------------------------------------------------
    # Build materials
    # --------------------------------------------------

    def make_video_material_from_template(
        self,
        template_material,
        image_path,
        duration_us,
    ):

        material = copy.deepcopy(
            template_material
        )

        new_id = self.make_id()

        material["id"] = new_id

        if "local_material_id" in material:

            material["local_material_id"] = new_id

        self.update_paths_recursive(
            material,
            image_path,
            image_path.name,
        )

        self.update_duration_recursive(
            material,
            duration_us,
        )

        return new_id, material

    def make_audio_material_from_template(
        self,
        template_material,
        audio_path,
        duration_us,
    ):

        material = copy.deepcopy(
            template_material
        )

        new_id = self.make_id()

        material["id"] = new_id

        if "local_material_id" in material:

            material["local_material_id"] = new_id

        self.update_paths_recursive(
            material,
            audio_path,
            audio_path.name,
        )

        self.update_duration_recursive(
            material,
            duration_us,
        )

        return new_id, material

    # --------------------------------------------------
    # Build segments
    # --------------------------------------------------

    def make_segment_from_template(
        self,
        template_segment,
        material_id,
        start_us,
        duration_us,
    ):

        segment = copy.deepcopy(
            template_segment
        )

        segment["id"] = self.make_id()

        segment["material_id"] = material_id

        segment["target_timerange"] = {
            "start": start_us,
            "duration": duration_us,
        }

        segment["source_timerange"] = {
            "start": 0,
            "duration": duration_us,
        }

        if "extra_material_refs" not in segment:

            segment["extra_material_refs"] = []

        return segment

    # --------------------------------------------------
    # Timeline replacement
    # --------------------------------------------------

    def replace_with_timeline(
        self,
        data,
        audio_path,
        timeline,
        audio_duration_seconds,
    ):

        parts = self.get_template_parts(
            data
        )

        materials = self.ensure_materials(
            data
        )

        project_duration_us = self.seconds_to_microseconds(
            audio_duration_seconds
        )

        new_video_materials = []

        video_segments = []

        for index, item in enumerate(
            timeline
        ):

            image_path = Path(
                item["image_path"]
            ).resolve()

            start_us = self.seconds_to_microseconds(
                item["start"]
            )

            if index + 1 < len(timeline):

                end_time = float(
                    timeline[index + 1]["start"]
                )

            else:

                end_time = float(
                    item["end"]
                )

            duration_us = self.seconds_to_microseconds(
                end_time - float(item["start"])
            )

            if duration_us <= 0:

                duration_us = 100000

            material_id, material = self.make_video_material_from_template(
                parts["video_material"],
                image_path,
                duration_us,
            )

            new_video_materials.append(
                material
            )

            segment = self.make_segment_from_template(
                parts["video_segment"],
                material_id,
                start_us,
                duration_us,
            )

            video_segments.append(
                segment
            )

        audio_material_id, audio_material = self.make_audio_material_from_template(
            parts["audio_material"],
            audio_path,
            project_duration_us,
        )

        audio_segment = self.make_segment_from_template(
            parts["audio_segment"],
            audio_material_id,
            0,
            project_duration_us,
        )

        new_video_track = copy.deepcopy(
            parts["video_track"]
        )

        new_audio_track = copy.deepcopy(
            parts["audio_track"]
        )

        new_video_track["id"] = self.make_id()

        new_audio_track["id"] = self.make_id()

        new_video_track["segments"] = video_segments

        new_audio_track["segments"] = [
            audio_segment
        ]

        materials["videos"] = new_video_materials

        materials["audios"] = [
            audio_material
        ]

        data["tracks"] = [
            new_video_track,
            new_audio_track,
        ]

        data["duration"] = project_duration_us

        if "canvas_config" not in data:

            data["canvas_config"] = {}

        data["canvas_config"]["ratio"] = "9:16"

        data["canvas_config"]["width"] = self.width

        data["canvas_config"]["height"] = self.height

        return data

    def replace_simple_ordered(
        self,
        data,
        audio_path,
        image_paths,
        audio_duration_seconds,
    ):

        parts = self.get_template_parts(
            data
        )

        materials = self.ensure_materials(
            data
        )

        duration_us = self.seconds_to_microseconds(
            audio_duration_seconds
        )

        image_duration_us = int(
            duration_us / max(
                1,
                len(image_paths),
            )
        )

        new_video_materials = []

        video_segments = []

        current_start = 0

        for index, image_path in enumerate(
            image_paths
        ):

            if index == len(image_paths) - 1:

                clip_duration = (
                    duration_us
                    - current_start
                )

            else:

                clip_duration = image_duration_us

            material_id, material = self.make_video_material_from_template(
                parts["video_material"],
                image_path,
                clip_duration,
            )

            new_video_materials.append(
                material
            )

            segment = self.make_segment_from_template(
                parts["video_segment"],
                material_id,
                current_start,
                clip_duration,
            )

            video_segments.append(
                segment
            )

            current_start += clip_duration

        audio_material_id, audio_material = self.make_audio_material_from_template(
            parts["audio_material"],
            audio_path,
            duration_us,
        )

        audio_segment = self.make_segment_from_template(
            parts["audio_segment"],
            audio_material_id,
            0,
            duration_us,
        )

        new_video_track = copy.deepcopy(
            parts["video_track"]
        )

        new_audio_track = copy.deepcopy(
            parts["audio_track"]
        )

        new_video_track["id"] = self.make_id()

        new_audio_track["id"] = self.make_id()

        new_video_track["segments"] = video_segments

        new_audio_track["segments"] = [
            audio_segment
        ]

        materials["videos"] = new_video_materials

        materials["audios"] = [
            audio_material
        ]

        data["tracks"] = [
            new_video_track,
            new_audio_track,
        ]

        data["duration"] = duration_us

        if "canvas_config" not in data:

            data["canvas_config"] = {}

        data["canvas_config"]["ratio"] = "9:16"

        data["canvas_config"]["width"] = self.width

        data["canvas_config"]["height"] = self.height

        return data

    # --------------------------------------------------
    # Public export methods
    # --------------------------------------------------

    def export_from_timeline(
        self,
        audio_path,
        timeline_path,
    ):

        timeline_file = Path(
            timeline_path
        )

        if not timeline_file.exists():

            raise FileNotFoundError(
                f"Timeline file not found: {timeline_path}"
            )

        with open(
            timeline_file,
            "r",
            encoding="utf8",
        ) as f:

            timeline = json.load(
                f
            )

        if not timeline:

            raise ValueError(
                "Timeline is empty."
            )

        output_name = self.safe_project_name()

        project_folder = self.copy_template_project(
            output_name
        )

        copied_audio, copied_timeline = self.copy_media_from_timeline(
            audio_path,
            timeline,
            project_folder,
        )

        audio_duration = self.audio_duration_seconds(
            copied_audio
        )

        self.log(
            f"Audio duration: {audio_duration:.2f}s"
        )

        draft_file, data = self.load_draft(
            project_folder
        )

        data = self.replace_with_timeline(
            data,
            copied_audio,
            copied_timeline,
            audio_duration,
        )

        self.save_draft(
            draft_file,
            data,
        )

        self.log(
            "CapCut draft_content.json updated from matched timeline."
        )

        self.log(
            f"Open this project in CapCut: {output_name}"
        )

        return project_folder

    def export(
        self,
        audio_path,
        image_paths,
    ):

        if not image_paths:

            raise ValueError(
                "No images found for CapCut export."
            )

        output_name = self.safe_project_name()

        project_folder = self.copy_template_project(
            output_name
        )

        copied_audio, copied_images = self.copy_media_simple(
            audio_path,
            image_paths,
            project_folder,
        )

        audio_duration = self.audio_duration_seconds(
            copied_audio
        )

        self.log(
            f"Audio duration: {audio_duration:.2f}s"
        )

        draft_file, data = self.load_draft(
            project_folder
        )

        data = self.replace_simple_ordered(
            data,
            copied_audio,
            copied_images,
            audio_duration,
        )

        self.save_draft(
            draft_file,
            data,
        )

        self.log(
            "CapCut draft_content.json updated."
        )

        self.log(
            f"Open this project in CapCut: {output_name}"
        )

        return project_folder