video_store = {}

def save_video_data(
    video_id,
    transcript,
    metadata
):
    video_store[video_id] = {
        "transcript": transcript,
        "metadata": metadata
    }

def get_video_data(video_id):
    return video_store.get(video_id, {})