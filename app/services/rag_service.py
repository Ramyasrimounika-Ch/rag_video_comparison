from uuid import uuid4

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)
print("RAG STEP 2")
from app.services.embeddings import get_embedding_model
print("RAG STEP 3")
from app.services.qdrant_service import (
    client,
    COLLECTION_NAME,
    create_collection
)
print("RAG STEP 4")
create_collection()
print("RAG STEP 5")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)


def chunk_transcript(
    transcript: str
):
    return text_splitter.split_text(
        transcript
    )


def store_video_chunks(
    transcript: str,
    metadata: dict,
    video_id: str
):

    print("=" * 50)
    print("VIDEO:", video_id)

    print("Transcript length:", len(transcript))

    chunks = chunk_transcript(transcript)

    print("Chunks created:", len(chunks))

    if not chunks:
        raise Exception(
            f"No chunks generated for video {video_id}"
        )

    engagement_rate = 0

    views = metadata.get("views", 0)
    likes = metadata.get("likes", 0)
    comments = metadata.get("comments", 0)

    if views > 0:
        engagement_rate = round(
            ((likes + comments) / views) * 100,
            2
        )

    points = []

    embedding_model = get_embedding_model()

    for idx, chunk in enumerate(chunks):

        print(f"Embedding chunk {idx}")

        vector = embedding_model.embed_query(chunk)

        if not vector:
            print("EMPTY VECTOR")
            continue

        points.append(
            {
                "id": str(uuid4()),
                "vector": vector,
                "payload": {
                    "video_id": video_id,
                    "platform": metadata.get("platform"),
                    "source_video_id": metadata.get("video_id"),
                    "creator": metadata.get("creator"),
                    "followers": metadata.get("followers")
                    or metadata.get("subscribers", 0),
                    "views": metadata.get("views", 0),
                    "likes": metadata.get("likes", 0),
                    "comments": metadata.get("comments", 0),
                    "upload_date": metadata.get("upload_date"),
                    "duration": metadata.get("duration", 0),
                    "hashtags": metadata.get("hashtags", []),
                    "engagement_rate": engagement_rate,
                    "chunk_index": idx,
                    "chunk_text": chunk
                }
            }
        )

    print("Points created:", len(points))

    if not points:
        raise Exception(
            f"No vectors generated for video {video_id}"
        )

    print("Vector size:", len(points[0]["vector"]))

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=False
    )

    return len(chunks)

def retrieve_chunks(query: str, limit: int = 8):

    embedding_model=get_embedding_model()
    query_vector = embedding_model.embed_query(query)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit * 3
    )

    seen = set()
    video_a = []
    video_b = []

    for item in results.points:

        payload = item.payload
        key = (payload["video_id"], payload["chunk_index"])

        if key in seen:
            continue

        seen.add(key)

        data = {
            "score": item.score,
            "text": payload["chunk_text"],
            "video_id": payload["video_id"],
            "platform": payload.get("platform") or "unknown",
            "creator": payload.get("creator"),
            "followers": payload.get("followers", 0),
            "views": payload.get("views", 0),
            "likes": payload.get("likes", 0),
            "comments": payload.get("comments", 0),
            "engagement_rate": payload.get("engagement_rate", 0),
            "chunk_index": payload["chunk_index"],
        }

        if payload["video_id"] == "A":
            video_a.append(data)
        else:
            video_b.append(data)

    final = video_a[:limit // 2] + video_b[:limit // 2]

    if len(final) < 3:
        final = (video_a + video_b)[:limit]

    return final