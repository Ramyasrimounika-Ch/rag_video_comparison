from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")