import os
import tempfile
import requests

from faster_whisper import WhisperModel
import gc 

# Use existing HuggingFace cache
os.environ["HF_HOME"] = r"/tmp/huggingface"


print("Loading Whisper Model...")


def download_video(video_url: str):

    print("Downloading video...")

    response = requests.get(#downloads video from url in bytes format
        video_url,
        stream=True,
        timeout=120
    )

    response.raise_for_status()

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )

    total_size = 0

    for chunk in response.iter_content(
        chunk_size=8192
    ):
        temp_file.write(chunk)
        total_size += len(chunk)

    temp_file.close()

    print(
        f"Downloaded: {round(total_size/(1024*1024),2)} MB"
    )

    return temp_file.name


def transcribe_video(
    video_url: str
):

    video_path = download_video(
        video_url
    )


    try:

        print(
            f"Transcribing: {video_path}"
        )

        model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        print("before whisper")
        segments, info = model.transcribe(
            video_path,
            beam_size=1
        )
        print("after whisper")

        segment_data = []

        for segment in segments:
            segment_data.append(
                {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                }
            )

        return {
            "segments": segment_data
        }

    except Exception as e:

        print(
            f"Whisper Error: {e}"
        )

        raise

    finally:
        if model is not None:
            del model
            gc.collect()
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"Deleted temp file: {video_path}")