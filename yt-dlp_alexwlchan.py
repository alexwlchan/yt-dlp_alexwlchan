#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import TypedDict

from yt_dlp import YoutubeDL


ydl_opts = {
    # Print progress output to stderr, not stdout
    "logtostderr": True,
    #
    # Download the thumbnail
    "writethumbnail": True,
    #
    # Download subtitles, or YouTube's automatic subtitles if there
    # aren't any.
    "writesubtitles": True,
    "writeautomaticsub": True,
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


def get_youtube_avatar_url(channel_url: str) -> str:
    """
    Returns the avatar URL of a YouTube channel.
    """
    ydl_opts = {
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

    with YoutubeDL(ydl_opts) as ydl:
        channel_info = ydl.extract_info(channel_url, download=False)

    thumbnails = channel_info["thumbnails"]
    best_thumbnail = next(t for t in thumbnails if t["id"] == "avatar_uncropped")
    return best_thumbnail["url"]


def get_instagram_avatar_url(channel_name: str) -> str:
    """
    Returns the avatar URL of an Instagram channel.
    """
    output = subprocess.check_output(
        ["gallery-dl", "--get-urls", f"https://www.instagram.com/{channel_name}/avatar"]
    )
    avatar_url = output.strip().decode("utf8")

    return avatar_url


class ChannelInfo(TypedDict):
    id: str
    name: str
    url: str
    avatar_url: str


class VideoInfo(TypedDict):
    id: str
    url: str
    title: str
    description: str
    video_path: Path
    thumbnail_path: Path
    subtitle_path: Path
    channel: ChannelInfo
    site: str


def download_video(url: str) -> VideoInfo:
    # Download all the videos to a temp directory; this allows the caller
    # to decide exactly where they want the video later.
    tmp_dir = Path(tempfile.mkdtemp())
    ydl_opts["outtmpl"] = str(tmp_dir / "%(title)s.%(ext)s")

    with YoutubeDL(ydl_opts) as ydl:
        video_info = ydl.extract_info(url)

    video_path = next(p for p in tmp_dir.iterdir() if p.suffix == ".mp4")
    thumbnail_path = next(p for p in tmp_dir.iterdir() if p.suffix == ".jpg")
    try:
        subtitle_path = next(p for p in tmp_dir.iterdir() if p.suffix == ".vtt")
    except StopIteration:
        subtitle_path = None

    if video_info["extractor"] == "youtube":
        site = "youtube"
        channel = {
            "id": video_info["channel_id"],
            "name": video_info["channel"],
            "url": video_info["channel_url"],
            "avatar_url": get_youtube_avatar_url(video_info["channel_url"]),
        }
    elif video_info["extractor"] == "Instagram":
        with open("out.json", "w") as of:
            of.write(str(video_info))
        site = "instagram"
        channel = {
            "id": video_info["uploader_id"],
            "name": video_info["uploader"],
            "channel_url": f"https://www.instagram.com/{video_info['channel']}/",
            "avatar_url": get_instagram_avatar_url(channel_name=video_info["channel"]),
        }
    else:
        sys.exit(f"Unsupported extractor: {video_info['extractor']}")

    return {
        "id": video_info["id"],
        "url": url,
        "title": video_info["title"],
        "description": video_info["description"],
        "video_path": video_path,
        "thumbnail_path": thumbnail_path,
        "subtitle_path": subtitle_path,
        "channel": channel,
        "site": site,
    }


class PathEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that encodes paths as a string.
    """

    def default(self, o):
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
