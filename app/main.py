from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
print("STEP 1")
from app.routes.ingest import router as ingest_router

print("STEP 2")
from app.routes.chat import router as chat_router

print("STEP 3")

app = FastAPI(
    title="CompiSMART",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "https://rag-video-comparison-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    ingest_router,
    prefix="/api"
)

app.include_router(
    chat_router,
    prefix="/api"
)


@app.get("/")
def root():
    return {
        "status": "running"
    }