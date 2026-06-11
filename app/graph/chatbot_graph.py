from typing import TypedDict,Annotated
from operator import add
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
    chat_history:Annotated[list,add]
    last_video: str

def resolve_video_from_history(question,state):
    video_id = extract_video_filter(question)
    if video_id:
        return video_id
    return state.get("last_video", "A")

def extract_seconds(question: str):
    match = re.search(r"(\d+)\s*seconds?",question.lower())
    if match:
        return int(match.group(1))
    return None

def detect_metadata_query(question: str):
    q = question.lower()
    metadata_questions = [
        "how many followers",
        "how many views",
        "how many likes",
        "how many comments",
        "how many subscribers",
        "who is the creator",
        "who created",
        "engagement rate"
    ]
    return any(word in q for word in metadata_questions)

def extract_video_filter(question: str):
    q = question.lower()
    if "video a" in q:
        return "A"
    if "video b" in q:
        return "B"
    return None

def metadata_node(state):
    question = state["question"]
    video_id = resolve_video_from_history(question,state)
    video = get_video_data(video_id)
    metadata = video.get("metadata",{})
    q = question.lower()
    if "follower" in q:
        answer = (
            f"Video {video_id} has "
            f"{metadata.get('followers',0)} followers."
        )
    elif "view" in q:
        answer = (
            f"Video {video_id} has "
            f"{metadata.get('views',0)} views."
        )
    elif "like" in q:
        answer = (
            f"Video {video_id} has "
            f"{metadata.get('likes',0)} likes."
        )
    elif "comment" in q:
        answer = (
            f"Video {video_id} has "
            f"{metadata.get('comments',0)} comments."
        )
    elif ("creator" in q or "channel" in q):
        answer = (
            f"The creator of Video {video_id} is "
            f"{metadata.get('creator','Unknown')}."
        )
    else:
        answer = str(metadata)
    new_history = state.get("chat_history",[]) + [
        {"role":"user","content":question},
        {"role":"assistant","content":answer}
    ]
    return {
        "answer": answer,
        "chat_history": new_history,
        "last_video": video_id
    }

def enrich_question(question,state):
    q = question.lower()
    pronouns = ["he","she","it","its","his","her"]
    if not any(p in q for p in pronouns):
        return question
    video_id = resolve_video_from_history(question,state)
    return (f"{question} "f"(referring to Video {video_id})")

def retrieve_node(state):
    question = enrich_question(state["question"],state)
    docs = retrieve_chunks(question)
    return {"retrieved_docs": docs}

def detect_time_query(question: str):
    q = question.lower()
    patterns = [
        "first", "beginning", "start",
        "last", "end",
        "hook", "intro",
        "timeline",
        "early", "later","seconds"
    ]
    return any(p in q for p in patterns)

def route_node(state):
    question = state["question"]
    if detect_metadata_query(question):
        state["mode"] = "metadata"
    elif detect_time_query(question):
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
    return any(text.startswith(g) for g in greetings)

def generate_node(state:GraphState):
    question = state["question"]
    chat_history = state.get("chat_history", [])
    # 🚨 HARD BLOCK GREETINGS (NO LLM, NO SOURCES)
    if is_greeting(question):
        response = llm.invoke(question)
        return {"answer": response.content}
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
    history = state.get("chat_history", [])[-6:]
    history_text = ""
    for msg in history:
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
        {"role": "assistant", "content": response.content}
    ][-5:]
    video_id = extract_video_filter(question)

    if video_id is None:
        video_id = state.get("last_video","A")
    return {
        "answer": final_answer,
        "chat_history": new_history,
        "last_video": video_id
    }

def get_text_until_time(segments,seconds):
    texts = []
    for seg in segments:
        if seg["end"] <= seconds:
            texts.append(seg["text"])
    return " ".join(texts)

def get_last_seconds(segments,seconds):
    if not segments:
        return ""
    video_end = max(seg["end"] for seg in segments)
    start_time = (video_end - seconds)
    texts = []
    for seg in segments:
        if seg["start"] >= start_time:
            texts.append(seg["text"])
    return " ".join(texts)

def time_node(state):
    
    question = state["question"].lower()
    video_a = get_video_data("A")
    video_b = get_video_data("B")
    segments_a = video_a.get("segments",[])
    segments_b = video_b.get("segments",[])
    seconds = extract_seconds(question)
    if "hook" in question:
        seconds = 5
    elif "intro" in question:
        seconds = 10
    elif seconds is None:
        seconds = 10
    docs = []
    compare_mode = (
        "compare" in question
        or "which" in question
        or "better" in question
    )
    ending_query = (
        "last" in question
        or "end" in question
        or "ending" in question
    )
    if compare_mode:
        if ending_query:
            text_a = get_last_seconds(segments_a,seconds)
            text_b = get_last_seconds(segments_b,seconds)
        else:
            text_a = get_text_until_time(segments_a,seconds)
            text_b = get_text_until_time(segments_b,seconds)
        docs = [{
                "video_id": "A",
                "text": text_a,
                "platform": "youtube",
                "chunk_index": 0,
                "creator":
                    video_a["metadata"].get(
                        "creator"
                    )
            },
            {
                "video_id": "B",
                "text": text_b,
                "platform": "instagram",
                "chunk_index": 0,
                "creator":
                    video_b["metadata"].get(
                        "creator"
                    )
            }
        ]
    else:
        video_id = resolve_video_from_history(question,state)
        video = get_video_data(video_id)
        segments = video.get("segments",[])
        if ending_query:
            text = get_last_seconds(segments,seconds)
        else:
            text = get_text_until_time(segments,seconds)
        docs = [{
                "video_id": video_id,
                "text": text,
                "platform": "direct",
                "chunk_index": 0,
                "creator":
                    video["metadata"].get(
                        "creator"
                    )
            }
        ]
    if compare_mode:
        return {"retrieved_docs": docs}
    return {"retrieved_docs": docs,"last_video": video_id}

graph = StateGraph(GraphState)
graph.add_node("retrieve",retrieve_node)
graph.add_node("generate",generate_node)
graph.add_node("route", route_node)
graph.add_node("time_node", time_node)
graph.add_node("metadata", metadata_node)
graph.set_entry_point("route")
graph.add_conditional_edges(
    "route",
    lambda x: x["mode"],
    {
        "metadata": "metadata",
        "time": "time_node",
        "rag": "retrieve"
    }
)
graph.add_edge("metadata",END)
graph.add_edge("time_node", "generate")
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)
chatbot_graph = graph.compile(checkpointer=memory)