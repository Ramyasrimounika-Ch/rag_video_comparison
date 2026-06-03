from typing import TypedDict
from langgraph.graph import StateGraph,END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.prompt import ANALYST_PROMPT
from app.services.video_store import get_video_data
from app.services.rag_service import retrieve_chunks
import re
from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0.3
)
memory=MemorySaver()
class GraphState(TypedDict):
    question: str
    retrieved_docs: list
    answer: str
    mode:str
    chat_history:list

def history_node(state: GraphState):

    history = []

    if "chat_history" in state:
        history = state["chat_history"]

    return {
        "chat_history": history
    }

def retrieve_node(state: GraphState):
    docs = retrieve_chunks(state["question"])
    return {"retrieved_docs": docs}

def detect_time_query(question: str):

    q = question.lower()

    patterns = [
        "first", "beginning", "start",
        "last", "end",
        "5 seconds", "10 seconds",
        "hook", "intro",
        "timeline",
        "early", "later"
    ]

    return any(p in q for p in patterns)

def route_node(state: GraphState):
    if detect_time_query(state["question"]):
        state["mode"] = "time"
    else:
        state["mode"] = "rag"
    return state

def is_greeting(text: str):
    text = text.lower().strip()
    greetings = [
        "hi", "hello", "hey",
        "good morning", "good evening",
        "how are you", "yo"
    ]
    return text in greetings

def extract_video_id(question: str):
    q = question.lower()

    if "video a" in q or "a " in q:
        return "A"
    if "video b" in q or "b " in q:
        return "B"

    return "A"  # default

def generate_node(state:GraphState):
    question = state["question"]
    chat_history = state.get("chat_history", [])
    # 🚨 HARD BLOCK GREETINGS (NO LLM, NO SOURCES)
    if is_greeting(question):
        response = llm.invoke(question)

        return {
            "answer": response.content
        }
    docs = state["retrieved_docs"]

    context = ""
    citations = []
    seen = set()

    for doc in docs:

        key = (doc["video_id"], doc["chunk_index"])
        if key in seen:
            continue
        seen.add(key)

        platform = (doc.get("platform") or "unknown").capitalize()

        context += f"""
Video {doc['video_id']}
Platform: {platform}
Creator: {doc.get('creator')}
Followers: {doc.get('followers', 0)}
Views: {doc.get('views', 0)}
Likes: {doc.get('likes', 0)}
Comments: {doc.get('comments', 0)}
Chunk: {doc['chunk_index']}
{doc['text']}
"""

        citations.append(
            f"- [{doc['video_id']} | {platform} | {doc.get('creator')} | Chunk {doc['chunk_index']}]"
        )

    history_text = ""

    for msg in state.get(
        "chat_history",
        []
    ):
        history_text += (
            f"{msg['role']}: "
            f"{msg['content']}\n"
        )    

    prompt = ANALYST_PROMPT.format(
        question=state["question"],
        context=context,
        history_text=history_text
    )

    response = llm.invoke(prompt)

    # ONLY ONE SOURCE SYSTEM (NO DUPLICATION POSSIBLE)
    final_answer = response.content.strip()

    if citations:
        final_answer += "\n\nSources:\n" + "\n".join(citations)
    else:
        final_answer += "\n\nSources:\n- None"

    new_history = chat_history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": final_answer}
    ]
    

    return {"answer": final_answer,"chat_history":new_history}

def time_node(state: GraphState):

    question = state["question"].lower()

    video_a = get_video_data("A")
    video_b = get_video_data("B")

    transcript_a = video_a.get(
    "transcript",
    ""
    )

    transcript_b = video_b.get(
    "transcript",
    ""
    )

    first_a = transcript_a[:1000]
    first_b = transcript_b[:1000]

    last_a = transcript_a[-1000:]
    last_b = transcript_b[-1000:]

    docs = []

    if "compare" in question:

        if (
            "first" in question
            or "hook" in question
            or "beginning" in question
            or "start" in question
        ):
            docs = [
                {
                    "video_id": "A",
                    "text": first_a,
                    "platform": "youtube",
                    "chunk_index": 0,
                    "creator": "video_a"
                },
                {
                    "video_id": "B",
                    "text": first_b,
                    "platform": "instagram",
                    "chunk_index": 0,
                    "creator": "video_b"
                }
            ]

        elif (
            "last" in question
            or "end" in question
        ):
            docs = [
                {
                    "video_id": "A",
                    "text": last_a,
                    "platform": "youtube",
                    "chunk_index": 0,
                    "creator": "video_a"
                },
                {
                    "video_id": "B",
                    "text": last_b,
                    "platform": "instagram",
                    "chunk_index": 0,
                    "creator": "video_b"
                }
            ]

    else:

        video_id = extract_video_id(question)
        video = get_video_data(video_id)
        transcript = video.get("transcript", "")

        if (
            "first" in question
            or "hook" in question
            or "beginning" in question
            or "start" in question
        ):
            text = transcript[:1000]

        elif (
            "last" in question
            or "end" in question
        ):
            text = transcript[-1000:]

        else:
            text = transcript[:1000]

        docs = [
            {
                "video_id": video_id,
                "text": text,
                "platform": "direct",
                "chunk_index": 0,
                "creator": "system"
            }
        ]

    return {
        "retrieved_docs": docs
    }
graph = StateGraph(GraphState)
graph.add_node("retrieve",retrieve_node)
graph.add_node("generate",generate_node)
graph.add_node("route", route_node)
graph.add_node("time_node", time_node)

graph.set_entry_point("route")
graph.add_conditional_edges(
    "route",
    lambda x: x["mode"],
    {
        "time": "time_node",
        "rag": "retrieve"
    }
)

graph.add_edge("time_node", "generate")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)
chatbot_graph = graph.compile(checkpointer=memory)