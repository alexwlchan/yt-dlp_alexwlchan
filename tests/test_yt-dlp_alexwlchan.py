import json
import os
import subprocess


def download_video(url):
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

    assert video_info["id"] == "TUQaGhPdlxs"


def test_instagram_video() -> None:
    """
    Download an Instagram video and check we get the expected output.
    """
    video_info = download_video("https://www.instagram.com/reel/DMWY8KkOS0n/")

    assert os.path.exists(video_info["video_path"])
    assert os.path.exists(video_info["thumbnail_path"])
    assert video_info["subtitle_path"] is None

    assert video_info["channel"]["id"] == "52716733233"
    assert video_info["channel"]["name"] == "Public Domain Gems"
    assert (
        video_info["channel"]["channel_url"]
        == "https://www.instagram.com/publicdomaingems/"
    )

    assert video_info["id"] == "DMWY8KkOS0n"
