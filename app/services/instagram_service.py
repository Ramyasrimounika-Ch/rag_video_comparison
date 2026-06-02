from apify_client import ApifyClient
from app.config import APIFY_API_TOKEN

client = ApifyClient(APIFY_API_TOKEN)

ACTOR_ID = "apify/instagram-scraper"
PROFILE_ACTOR_ID = "apify/instagram-profile-scraper"

def get_instagram_followers(username: str):
    run_input = {
        "usernames": [username]
    }

    run = client.actor(PROFILE_ACTOR_ID).call(
        run_input=run_input
    )

    dataset_id = run.default_dataset_id

    items = list(
        client.dataset(dataset_id).iterate_items()
    )

    if not items:
        return 0

    profile = items[0]


    return profile.get("followersCount", 0)

def get_instagram_reel_data(reel_url: str):
    run_input = {
        "directUrls": [reel_url],
        "resultsLimit": 1,
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)

    dataset_id = run.default_dataset_id

    items = list(
        client.dataset(dataset_id).iterate_items()
    )

    if not items:
        raise Exception("No Instagram data found")

    reel = items[0]

    username = reel.get("ownerUsername")

    followers = 0
    if username:
        followers = get_instagram_followers(username)

    return {
    "platform": "instagram",   
    "video_id": reel.get("id"),
    "creator": reel.get("ownerUsername"),
    "creator_name": reel.get("ownerFullName"),
    "creator_id": reel.get("ownerId"),
    "followers": followers,
    "likes": reel.get("likesCount", 0),
    "comments": reel.get("commentsCount", 0),
    "views": reel.get("videoPlayCount", 0),
    "caption": reel.get("caption", ""),
    "hashtags": reel.get("hashtags", []),
    "duration": reel.get("videoDuration", 0),
    "video_url": reel.get("videoUrl"),
    "upload_date": reel.get("timestamp"),
}