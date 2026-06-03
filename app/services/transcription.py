import os
import tempfile
import requests

from faster_whisper import WhisperModel


# Use existing HuggingFace cache
os.environ["HF_HOME"] = r"/tmp/huggingface"


print("Loading Whisper Model...")

model = None

def get_model():
    global model
    if model is None:
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return model


def download_video(video_url: str):

    print("Downloading video...")

    response = requests.get(
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

        model=get_model()

        print("before whisper")
        segments, info = model.transcribe(
            video_path,
            beam_size=5
        )
        print("after whisper")

        transcript_parts = []

        for segment in segments:
            transcript_parts.append(
                segment.text
            )

        transcript = " ".join(
            transcript_parts
        )

        print(
            f"Transcript Length: {len(transcript)}"
        )

        return transcript

    except Exception as e:

        print(
            f"Whisper Error: {e}"
        )

        raise

    finally:

        if os.path.exists(
            video_path
        ):
            os.remove(
                video_path
            )

            print(
                f"Deleted temp file: {video_path}"
            )