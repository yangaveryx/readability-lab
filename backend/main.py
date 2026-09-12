from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from readability import analyze_readability
from simplifier import simplify_text


app = FastAPI()

class SimplifyRequest(BaseModel):
    text: str = Field(min_length=1)
    target_level: int = Field(ge=1, le=16)

class ReadabilityMetrics(BaseModel):
    flesch_kincaid_grade: float
    syllable_count: int
    average_sentence_length: float
    average_dependency_depth: float
    maximum_dependency_depth: int

class SimplifyResponse(BaseModel):
    original_metrics: ReadabilityMetrics
    rewritten_text: str
    rewritten_metrics: ReadabilityMetrics
    iterations: int

@app.post("/api/simplify", response_model=SimplifyResponse)
def simplify(request: SimplifyRequest):
    if not request.text.strip():
        raise HTTPException(
            status_code=422,
            detail="Text cannot be blank.",
        )

    original_metrics = analyze_readability(request.text)

    try:
        result = simplify_text(
            text=request.text,
            target_grade=request.target_level,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return {
        "original_metrics": original_metrics,
        "rewritten_text": result["text"],
        "rewritten_metrics": result["metrics"],
        "iterations": result["attempt_count"],
    }