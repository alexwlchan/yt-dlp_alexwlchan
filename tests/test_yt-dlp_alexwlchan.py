import json
import os
import subprocess


def test_public_domain_video() -> None:
    """
    Download a public domain video and check we get the expected output.
    """
    output = subprocess.check_output(
        [
            "python3",
            "yt-dlp_alexwlchan.py",
            "https://www.youtube.com/watch?v=TUQaGhPdlxs",
        ]
    )
    video_info = json.loads(output)

    assert (
        video_info["title"]
        == '"new york city, manhattan, people" - Free Public Domain Video'
    )
    assert os.path.exists(video_info["video_path"])
    assert os.path.exists(video_info["thumbnail_path"])
    assert video_info["subtitle_path"] is None
