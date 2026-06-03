from dotenv import load_dotenv
import os

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
ASSEMBLYAI_API_KEY=os.getenv("ASSEMBLYAI_API_KEY")