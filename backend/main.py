import os
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from readability import analyze_readability
from adjuster import adjust_text

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

logger = logging.getLogger(__name__)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

frontend_url = os.getenv("FRONTEND_URL")

if frontend_url:
    allowed_origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AdjustRequest(BaseModel):
    text: str = Field(min_length=1)
    target_level: int = Field(ge=1, le=16)

class ReadabilityMetrics(BaseModel):
    flesch_kincaid_grade: float
    syllable_count: int
    average_sentence_length: float
    average_dependency_depth: float
    maximum_dependency_depth: int

class AdjustResponse(BaseModel):
    original_metrics: ReadabilityMetrics
    rewritten_text: str
    rewritten_metrics: ReadabilityMetrics
    iterations: int
    direction: str

@app.post("/api/adjust", response_model=AdjustResponse)
def adjust(request: AdjustRequest):
    if not request.text.strip():
        raise HTTPException(
            status_code=422,
            detail="Text cannot be blank.",
        )

    original_metrics = analyze_readability(request.text)

    try:
        result = adjust_text(
            text=request.text,
            target_grade=request.target_level,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        logger.exception("Text adjustment failed")

        raise HTTPException(
            status_code=500,
            detail=f"Text adjustment failed: {type(error).__name__}",
        ) from error

    return {
        "original_metrics": original_metrics,
        "rewritten_text": result["text"],
        "rewritten_metrics": result["metrics"],
        "iterations": result["attempt_count"],
        "direction": result["direction"],
    }