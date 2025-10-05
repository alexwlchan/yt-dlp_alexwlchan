#!/usr/bin/env python3

import json
import os
import sys
import tempfile

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


def get_avatar_url(channel_url: str) -> str:
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


if __name__ == "__main__":
    try:
        url = sys.argv[1]
    except IndexError:
        sys.exit(f"Usage: {__file__} URL")

    tmp_dir = tempfile.mkdtemp()

    os.chdir(tmp_dir)

    with YoutubeDL(ydl_opts) as ydl:
        video_info = ydl.extract_info(url)

    downloaded_files = os.listdir(tmp_dir)

    video_path = next(p for p in downloaded_files if p.endswith(".mp4"))
    thumbnail_path = next(p for p in downloaded_files if p.endswith(".jpg"))
    try:
        subtitle_path = next(p for p in downloaded_files if p.endswith(".vtt"))
    except StopIteration:
        subtitle_path = None

    channel = {
        "id": video_info["channel_id"],
        "name": video_info["channel"],
        "url": video_info["channel_url"],
        "avatar_url": get_avatar_url(video_info["channel_url"]),
    }

    result = {
        "url": url,
        "title": video_info["title"],
        "description": video_info["description"],
        "video_path": video_path,
        "thumbnail_path": thumbnail_path,
        "subtitle_path": subtitle_path,
        "channel": channel,
    }

    print(json.dumps(result, indent=2))
