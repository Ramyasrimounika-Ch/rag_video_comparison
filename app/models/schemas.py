from pydantic import BaseModel


class IngestRequest(BaseModel):
    youtube_url: str
    instagram_url: str


class ChatRequest(BaseModel):
    session_id: str
    question: str