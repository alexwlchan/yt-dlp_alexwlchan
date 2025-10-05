# yt-dlp_alexwlchan

This is a personal wrapper around [yt-dlp](https://github.com/yt-dlp/yt-dlp) that downloads a video with thumbnails and subtitles, converts to my preferred formats, then prints some key information in a consistent JSON format.

```console
$ yt-dlp_alexwlchan.py "https://www.youtube.com/watch?v=TUQaGhPdlxs"
{
  "url": "https://www.youtube.com/watch?v=TUQaGhPdlxs",
  "title": "\"new york city, manhattan, people\" - Free Public Domain Video",
  "description": "All videos uploaded to this channel are in the Public Domain: Free for use by anyone for any purpose without restriction. #PublicDomain",
  "video_path": "\uff02new york city, manhattan, people\uff02 - Free Public Domain Video [TUQaGhPdlxs].mp4",
  "thumbnail_path": "\uff02new york city, manhattan, people\uff02 - Free Public Domain Video [TUQaGhPdlxs].jpg",
  "subtitle_path": null,
  "channel": {
    "id": "UCDeqps8f3hoHm6DHJoseDlg",
    "name": "Public Domain Archive",
    "url": "https://www.youtube.com/channel/UCDeqps8f3hoHm6DHJoseDlg",
    "avatar_url": "https://yt3.googleusercontent.com/ytc/AIdro_kbeCfc5KrnLmdASZQ9u649IxrxEUXsUaxdSUR_jA_4SZQ=s0"
  }
}
```

I have other scripts that know how to read this format, and it allows me to consolidate all my YouTube-handling logic in one place.
Other scripts can call this script and get the title or description "for free".

## What it does

*   Downloads the video, thumbnail, and subtitles to a temporary directory
*   Convert the video to MP4 and the thumbnail to JPEG (my preferred formats)
*   Gets some info about the video (title, description) and channel (name, URL, avatar URL)
*   Prints all that info in a convenient JSON object
