from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str):

    parsed = urlparse(url)

    if parsed.hostname == "youtu.be":
        return parsed.path[1:]

    if parsed.hostname in (
        "www.youtube.com",
        "youtube.com"
    ):

        # Normal videos
        if parsed.path == "/watch":
            return parse_qs(
                parsed.query
            ).get(
                "v",
                [None]
            )[0]

        # Shorts
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[1]

    return None
def get_youtube_metadata(url: str):

    ydl_opts = {
        "quiet": True,
        "extract_flat": False
    }

    with YoutubeDL(ydl_opts) as ydl:

        info = ydl.extract_info(
            url,
            download=False
        )

        return {
            "platform": "youtube",
            "video_id": info.get("id"),
            "title": info.get("title"),
            "creator": info.get("uploader"),
            "channel_id": info.get("channel_id"),
            "channel_url": info.get("channel_url"),
            "subscribers": info.get("channel_follower_count", 0),
            "views": info.get("view_count", 0),
            "likes": info.get("like_count", 0),
            "comments": info.get("comment_count", 0),
            "upload_date": info.get("upload_date"),
            "duration": info.get("duration", 0),
            "hashtags": info.get("tags", [])
        }


def get_youtube_transcript(url: str):

    video_id = extract_video_id(url)

    transcript = YouTubeTranscriptApi().fetch(
        video_id
    )

    full_text = " ".join(
        item.text
        for item in transcript
    )

    return full_text


def process_youtube_video(url: str):

    metadata = get_youtube_metadata(url)

    transcript = get_youtube_transcript(url)

    return {
        "metadata": metadata,
        "transcript": transcript
    }