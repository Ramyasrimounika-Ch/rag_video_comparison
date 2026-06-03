from fastapi import APIRouter
from app.models.schemas import ChatRequest
print("CHAT IMPORT 1")
from app.graph.chatbot_graph import chatbot_graph
print("CHAT IMPORT 2")
router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):

    result = chatbot_graph.invoke(
    {"question": request.question,"chat_history": [] },
    config={
        "configurable": {
            "thread_id": request.session_id
        }
    }
)
    return {
        "answer":result["answer"]
    }