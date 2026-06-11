video_store = {}

def save_video_data(video_id,transcript,metadata,segments):
    video_store[video_id] = {
        "transcript": transcript,
        "metadata": metadata,
        "segments":segments
    }
    print("Saved:", video_id)
    print("Current store keys:", video_store.keys())

def get_video_data(video_id):
    return video_store.get(video_id, {})

#why this? 
"""
Your Qdrant stores:

chunk_text
chunk_index
vector

But some operations require the entire video.

For example:

Metadata queries
Who is creator of Video B?

You don't need embeddings.

You simply do:

video = get_video_data("B")

creator = video["metadata"]["creator"]

Time-based queries
Compare first 10 seconds

You need:

video["segments"]

to find:

0s → 10s

portion.

Qdrant doesn't store timestamp segments.

So you use:

video_store

instead.
"""