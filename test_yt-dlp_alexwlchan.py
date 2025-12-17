import json
import os
import subprocess
from typing import Any


def download_video(url: str) -> Any:
    output = subprocess.check_output(["python3", "yt-dlp_alexwlchan.py", url])
    video_info = json.loads(output)

    return video_info


def test_youtube_video() -> None:
    """
    Download a YouTube video and check we get the expected output.
    """
    video_info = download_video("https://www.youtube.com/watch?v=TUQaGhPdlxs")

    assert (
        video_info["title"]
        == '"new york city, manhattan, people" - Free Public Domain Video'
    )
    assert os.path.exists(video_info["video_path"])
    assert os.path.exists(video_info["thumbnail_path"])
    assert video_info["subtitle_path"] is None
    assert os.path.exists(video_info["uploader"]["avatar_path"])

    assert video_info["id"] == "TUQaGhPdlxs"
    assert video_info["date_uploaded"] == "2022-03-25T01:10:38Z"

    assert video_info["video_path"].endswith(" [TUQaGhPdlxs].mp4")


def test_youtube_path_is_cleaned_up() -> None:
    """
    Paths of YouTube videos get cleaned up during the download.
    """
    video = download_video("https://www.youtube.com/shorts/eso8JB7q0a0")
    assert (
        video["title"]
        == "3D Printing Everyday for 365 Days 176/365  #stem #3dprinting #3dprint #ideas #useful"
    )
    assert (
        os.path.basename(video["video_path"])
        == "3D Printing Everyday for 365 Days 176-365 stem 3dprinting 3dprint ideas useful [eso8JB7q0a0].mp4"
    )


def test_instagram_video() -> None:
    """
    Download an Instagram video and check we get the expected output.
    """
    video_info = download_video("https://www.instagram.com/reel/DMWY8KkOS0n/")

    assert os.path.exists(video_info["video_path"])
    assert os.path.exists(video_info["thumbnail_path"])
    assert video_info["subtitle_path"] is None

    assert video_info["uploader"]["id"] == "52716733233"
    assert video_info["uploader"]["name"] == "Public Domain Gems"
    assert (
        video_info["uploader"]["url"] == "https://www.instagram.com/publicdomaingems/"
    )
    assert os.path.exists(video_info["uploader"]["avatar_path"])

    assert video_info["id"] == "DMWY8KkOS0n"
    assert video_info["date_uploaded"] == "2025-07-21T00:34:41Z"

    assert video_info["video_path"].endswith(" [DMWY8KkOS0n].mp4")
