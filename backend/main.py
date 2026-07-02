import os
import sys
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

core_path = os.path.join(os.path.dirname(__file__), "core")
sys.path.insert(0, core_path)

try:
    from pipeline import process_youtube_video, ask_question
    from database import init_db
except ImportError as e:
    logger.error("Failed to import core modules: %s", e)
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Walki-Talkie YouTube API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProcessVideoRequest(BaseModel):
    url: str


@app.post("/api/process-video")
async def process_video(request: ProcessVideoRequest):
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    try:
        result = process_youtube_video(url)
        return {
            "video_id":     result.video_id,
            "title":        result.title,
            "author":       result.author,
            "segment_count": result.segment_count,
            "status":       result.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error in /api/process-video:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")


class AskRequest(BaseModel):
    question: str
    video_id: Optional[str] = None


@app.post("/api/ask")
async def ask_video(request: AskRequest):
    try:
        result = ask_question(request.question, video_id=request.video_id)
        return {"answer": result.answer}
    except Exception as e:
        # Log the FULL traceback — this is what makes silent 500s debuggable
        logger.error("Error in /api/ask:\n%s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)