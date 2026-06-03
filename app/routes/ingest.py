from fastapi import APIRouter
from app.models.schemas import IngestRequest
print("IMPORT 1")
from app.services.video_store import save_video_data

print("IMPORT 2")
from app.services.youtube_service import process_youtube_video

print("IMPORT 3")
from app.services.instagram_service import get_instagram_reel_data

print("IMPORT 4")
from app.services.transcription import transcribe_video

print("IMPORT 5")
from app.services.rag_service import store_video_chunks

from app.services.qdrant_service import (
    client,
    COLLECTION_NAME,
    create_collection
)


print("IMPORT 6")
router = APIRouter()


@router.post("/ingest")
async def ingest_videos(request: IngestRequest):

    try:
        client.delete_collection(COLLECTION_NAME)
        print("Old collection deleted")
    except Exception as e:
        print("Collection not found:", e)

    # Create fresh collection
    create_collection()

    # Continue with ingestion...

    print("=" * 50)
    print("STEP 1: PROCESSING YOUTUBE")
    print("=" * 50)

    youtube_data = process_youtube_video(
        request.youtube_url
    )

    print("STEP 2: STORING YOUTUBE CHUNKS")

    store_video_chunks(
        transcript=youtube_data["transcript"],
        metadata=youtube_data["metadata"],
        video_id="A"
    )

    print("STEP 3: FETCHING INSTAGRAM METADATA")

    instagram_metadata = get_instagram_reel_data(
        request.instagram_url
    )

    print("STEP 4: INSTAGRAM METADATA RECEIVED")

    print(instagram_metadata)

    print("STEP 5: STARTING TRANSCRIPTION")

    instagram_transcript = transcribe_video(
        instagram_metadata["video_url"]
    )
    print("STEP 6: TRANSCRIPTION FINISHED")

    print(
        "Transcript Length:",
        len(instagram_transcript)
    )

    print("STEP 7: STORING INSTAGRAM CHUNKS")

    store_video_chunks(
        transcript=instagram_transcript,
        metadata=instagram_metadata,
        video_id="B"
    )

    print("STEP 8: COMPLETED")

    save_video_data(
    "A",
      youtube_data["transcript"],
    youtube_data["metadata"]
    )

    save_video_data(
        "B",
        instagram_transcript,
        instagram_metadata
    )

    return {
        "video_a": {
            "video_id": "A",
            "platform": "youtube",
            "creator":
                youtube_data["metadata"].get("creator"),
            "title":
                youtube_data["metadata"].get("title"),
            "followers":
                youtube_data["metadata"].get("subscribers",0),      
            "views":
                youtube_data["metadata"].get("views", 0),
            "likes":
                youtube_data["metadata"].get("likes", 0)
        },
        "video_b": {
            "video_id": "B",
            "platform": "instagram",
            "creator":
                instagram_metadata.get("creator"),
            "followers":
                instagram_metadata.get("followers",0),    
            "views":
                instagram_metadata.get("views", 0),
            "likes":
                instagram_metadata.get("likes", 0)
        }
    }