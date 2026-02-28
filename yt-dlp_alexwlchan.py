#!/usr/bin/env python3

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, TypedDict

from chives.media import create_video_entity, VideoEntity
import httpx
import hyperlink
from yt_dlp import YoutubeDL
from yt_dlp.networking.exceptions import HTTPError as YouTubeDLHTTPError
from yt_dlp.utils import DownloadError


ydl_opts: Any = {
    # Print progress output to stderr, not stdout
    "logtostderr": True,
    #
    # Download the thumbnail
    "writethumbnail": True,
    #
    # Download subtitles, or YouTube's automatic subtitles if there
    # aren't any.
    "writesubtitles": True,
    #
    # Ignore AI-upscaled videos from YouTube.
    # See https://alexwlchan.net/til/2025/ignore-ai-scaled-videos/
    "format": "bestvideo*[format_id!*=-sr]+bestaudio/best[format_id!*=-sr]",
    #
    # Download video files as MP4 and thumbnails as JPEG, or convert
    # to those formats if they aren't the best available.
    "format_sort": ["res", "ext:mp4:m4a"],
    "postprocessors": [
        {
            "key": "FFmpegVideoConvertor",
            "preferedformat": "mp4",
        },
        {
            "key": "FFmpegThumbnailsConvertor",
            "format": "jpg",
            "when": "before_dl",
        },
    ],
}


def _choose_filename_suffix(content_type: str) -> str:
    """
    Given an HTTP Content-Type header, choose the correct suffix for
    the downloaded file.
    """
    if content_type == "image/png":
        return ".png"
    elif content_type == "image/jpeg":
        return ".jpg"
    else:
        raise ValueError(f"Unrecognised content-type: {content_type}")


def download_file(out_dir: Path, url: str, basename: str) -> Path:
    """
    Download an image, and pick a file extension based on the image type.
    """
    # Download the bytes, and save them to a file.
    resp = httpx.get(url)
    resp.raise_for_status()

    suffix = _choose_filename_suffix(resp.headers["content-type"])

    out_path = out_dir / (basename + suffix)

    with open(out_path, "xb") as out_file:
        out_file.write(resp.content)

    return out_path


def get_youtube_avatar(tmp_dir: Path, channel_url: str) -> Path:
    """
    Download the avatar of a YouTube channel.
    """
    ydl_opts: Any = {
        # Print progress output to stderr, not stdout
        "logtostderr": True,
        #
        # Don't download every page of results for the channel.
        #
        # This tells yt-dlp that we're only interested in the first video,
        # which is technically a lie because we don't care about any videos,
        # but it has the desired effect.
        "playlist_items": "0",
    }

    # Get the URL of the YouTube avatar.
    with YoutubeDL(ydl_opts) as ydl:
        channel_info: Any = ydl.extract_info(channel_url, download=False)

    thumbnails = channel_info["thumbnails"]
    best_thumbnail = next(t for t in thumbnails if t["id"] == "avatar_uncropped")
    thumbnail_url = best_thumbnail["url"]

    # Work out the base filename, e.g. "https://www.youtube.com/@networkrail"
    # becomes "networkrail"
    u = hyperlink.parse(channel_url)
    basename = u.path[0].replace("@", "")

    return download_file(tmp_dir, url=thumbnail_url, basename=basename)


def get_instagram_avatar(tmp_dir: Path, uploader_name: str) -> Path:
    """
    Download the avatar of an Instagram channel.
    """
    output = subprocess.check_output(
        [
            "gallery-dl",
            "--get-urls",
            f"https://www.instagram.com/{uploader_name}/avatar",
            "--cookies-from-browser",
            "firefox",
        ]
    )
    avatar_url = output.strip().decode("utf8")

    return download_file(tmp_dir, url=avatar_url, basename=uploader_name)


class UploaderInfo(TypedDict):
    id: str
    name: str
    url: str
    avatar_path: Path


class VideoInfo(TypedDict):
    id: str
    url: str
    title: str
    description: str
    date_uploaded: str
    video_path: Path
    thumbnail_path: Path
    subtitle_path: Path | None
    folder_path: Path
    uploader: UploaderInfo
    entity: VideoEntity
    site: str


def cleanup_paths(dir_path: Path) -> None:
    """
    For every file in `dir_path`, remove URL-unsafe characters from
    the filenames.
    """
    for p in dir_path.iterdir():
        old_name = p.name
        new_name = p.name

        for old, new in [
            ("#", " "),
            ("？", " "),
            ("⧸", "-"),
            ("：", "-"),
            ("｜", "-"),
            ("＂", ""),
        ]:
            new_name = new_name.replace(old, new)

        new_name = re.sub(r"\s+", " ", new_name).strip()

        if old_name == new_name:
            continue

        assert not (dir_path / new_name).exists(), new_name
        p.move(dir_path / new_name)


def download_video(url: str) -> VideoInfo:
    # Download all the videos to a temp directory; this allows the caller
    # to decide exactly where they want the video later.
    tmp_dir = Path(tempfile.mkdtemp())
    ydl_opts["outtmpl"] = str(tmp_dir / "%(title)s [%(id)s].%(ext)s")

    with YoutubeDL(ydl_opts) as ydl:
        video_info: Any = ydl.extract_info(url)

    # Try to download automatic subtitles for a YouTube video.
    #
    # If you try to download autosubs for a video which doesn't have any,
    # YouTube rturns an HTTP 429 "Too Many Requests" error. Ignore this
    # error, but raise all others.
    if video_info["extractor"] == "youtube" and not any(
        p.suffix == ".vtt" for p in tmp_dir.iterdir()
    ):
        ydl_auto_subtitle_opts: Any = {
            "logtostderr": True,
            "writeautomaticsub": True,
            "skip_download": True,
            "outtmpl": ydl_opts["outtmpl"],
        }
        with YoutubeDL(ydl_auto_subtitle_opts) as ydl:
            try:
                ydl.extract_info(url)
            except DownloadError as e:
                if (
                    isinstance(e.exc_info[1], YouTubeDLHTTPError)
                    and e.exc_info[1].status == 429
                ):
                    pass
                else:
                    raise

    cleanup_paths(tmp_dir)

    video_path = next(p for p in tmp_dir.iterdir() if p.suffix == ".mp4")
    thumbnail_path = next(p for p in tmp_dir.iterdir() if p.suffix == ".jpg")
    try:
        subtitle_path = next(p for p in tmp_dir.iterdir() if p.suffix == ".vtt")
    except StopIteration:
        subtitle_path = None

    uploader: UploaderInfo

    if video_info["extractor"] == "youtube":
        site = "youtube"
        uploader = {
            "id": video_info["uploader_id"],
            "name": video_info["uploader"],
            "url": video_info["uploader_url"],
            "avatar_path": get_youtube_avatar(tmp_dir, video_info["uploader_url"]),
        }
    elif video_info["extractor"] == "Instagram":
        site = "instagram"
        uploader = {
            "id": video_info["uploader_id"],
            "name": video_info["uploader"],
            "url": f"https://www.instagram.com/{video_info['channel']}/",
            "avatar_path": get_instagram_avatar(
                tmp_dir, uploader_name=video_info["channel"]
            ),
        }
    else:
        sys.exit(f"Unsupported extractor: {video_info['extractor']}")

    date_uploaded = datetime.fromtimestamp(video_info["timestamp"], tz=timezone.utc)

    return {
        "id": video_info["id"],
        "url": url,
        "title": video_info["title"],
        "description": video_info["description"],
        "date_uploaded": date_uploaded.isoformat().replace("+00:00", "Z"),
        "video_path": video_path,
        "thumbnail_path": thumbnail_path,
        "subtitle_path": subtitle_path,
        "uploader": uploader,
        "entity": create_video_entity(
            video_path,
            poster_path=thumbnail_path,
            subtitles_path=subtitle_path,
            source_url=url,
            background="#222222",
        ),
        "folder_path": tmp_dir,
        "site": site,
    }


class PathEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that encodes paths as a string.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, Path):
            return str(o.absolute())
        else:
            return super().default(o)


if __name__ == "__main__":
    try:
        url = sys.argv[1]
    except IndexError:
        sys.exit(f"Usage: {__file__} URL")

    video_info = download_video(url)

    json_string = json.dumps(video_info, indent=2, cls=PathEncoder)

    print(json_string)
