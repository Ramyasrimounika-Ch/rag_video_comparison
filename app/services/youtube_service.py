from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import requests
from apify_client import ApifyClient
from app.config import APIFY_API_TOKEN,YOUTUBE_API_KEY

client = ApifyClient(APIFY_API_TOKEN)

TRANSCRIPT_ACTOR_ID = "pintostudio/youtube-transcript-scraper"

def get_youtube_transcript(url: str):

    print("Fetching transcript from Apify:", url)

    run_input = {
       "videoUrl": url
    }

    run = client.actor(
        TRANSCRIPT_ACTOR_ID
    ).call(
        run_input=run_input
    )

    dataset_id = run.default_dataset_id

    items = list(
        client.dataset(dataset_id).iterate_items()
    )

    if not items:
        return ""

    transcript_chunks = items[0].get("data", [])

    transcript = " ".join(
        chunk.get("text", "")
        for chunk in transcript_chunks
    )

    print("TRANSCRIPT LENGTH:", len(transcript))

    return transcript

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
            return parsed.path.split("/shorts/")[1].split("?")[0]
        
    return None

def get_youtube_metadata(url: str):

    video_id = extract_video_id(url)

    # Video info
    video_url = (
        "https://www.googleapis.com/youtube/v3/videos"
    )

    video_response = requests.get(
        video_url,
        params={
            "part": "snippet,statistics",
            "id": video_id,
            "key": YOUTUBE_API_KEY
        }
    )

    video_data = video_response.json()

    if not video_data.get("items"):
        raise Exception("Video not found or API key invalid")
    
    item = video_data["items"][0]

    snippet = item["snippet"]
    stats = item["statistics"]

    channel_id = snippet["channelId"]

    # Channel info
    channel_url = (
        "https://www.googleapis.com/youtube/v3/channels"
    )

    channel_response = requests.get(
        channel_url,
        params={
            "part": "statistics",
            "id": channel_id,
            "key": YOUTUBE_API_KEY
        }
    )

    channel_data = channel_response.json()

    subscriber_count = int(
        channel_data["items"][0]["statistics"].get(
            "subscriberCount",
            0
        )
    )

    return {
        "platform": "youtube",
        "video_id": video_id,
        "title": snippet.get("title"),
        "creator": snippet.get("channelTitle"),
        "channel_id": channel_id,
        "subscribers": subscriber_count,
        "views": int(stats.get("viewCount", 0)),
        "likes": int(stats.get("likeCount", 0)),
        "comments": int(stats.get("commentCount", 0)),
        "upload_date": snippet.get("publishedAt"),
        "hashtags": snippet.get("tags", [])
    }


def process_youtube_video(url: str):

    metadata = get_youtube_metadata(url)

    transcript = get_youtube_transcript(url)

    return {
        "metadata": metadata,
        "transcript": transcript
    }