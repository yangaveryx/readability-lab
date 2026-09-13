import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from pydantic import BaseModel, Field

from readability import analyze_readability

load_dotenv()

class RewriteResult(BaseModel):
    rewritten_text: str = Field(
        description=(
            "Only the adjusted passage, without labels, explanations, "
            "analysis, bullet points, or commentary."
        )
    )

def create_model():
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        return ChatOllama(model="llama3.2", temperature=0,)

    if provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0,)

    raise ValueError(f"Unsupported LLM provider: {provider}")

model = create_model()
structured_model = model.with_structured_output(RewriteResult)

def get_direction_description(direction: str) -> str:
    if direction == "simplify":
        return "too complex, so simplify it further"

    if direction == "elevate":
        return (
            "too simple, so increase its precision and structural "
            "complexity without adding information"
        )

    return "at the requested level"

def get_maximum_sentence_words(target_grade: int) -> int:
    if target_grade <= 5:
        return 8

    if target_grade <= 8:
        return 12

    return 16

def get_direction(
    current_grade: float,
    target_grade: int,
    tolerance: float,
) -> str:
    if current_grade > target_grade + tolerance:
        return "simplify"

    if current_grade < target_grade - tolerance:
        return "elevate"

    return "matched"

def get_direction_instructions(
    direction: str,
    target_grade: int,
) -> str:
    if direction == "simplify":
        maximum_words = get_maximum_sentence_words(target_grade)

        return f"""
        Make the text easier to read:
        - Prefer short, direct sentences.
        - Aim for no more than {maximum_words} words per sentence.
        - Split sentences with multiple clauses.
        - Replace difficult words with familiar words when meaning is preserved.
        - Explain essential technical terms simply.
        - Remove unnecessary repetition.
        """

    if direction == "elevate":
        return """
        Make the writing more sophisticated:
        - Use more precise vocabulary when it improves the meaning.
        - Combine closely related short sentences when the result remains clear.
        - Use transitions to clarify relationships between ideas.
        - Vary sentence structure and allow moderate syntactic complexity.
        - Preserve the original ideas without adding facts, arguments, or examples.
        - Do not create complexity through repetition, filler, or run-on sentences.
        """

    return ""

initial_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You adjust writing to a requested reading grade level.

            General rules:
            - Preserve every important fact and the original meaning.
            - Do not add facts, opinions, examples, or unsupported nuance.
            - Do not remove information merely to change the readability score.
            - Keep specific names, quantities, dates, and scientific terms accurate.
            - Proofread for grammar, spelling, punctuation, and missing spaces.
            - Your entire response must contain only the rewritten passage.
            - Do not include a title, label, introduction, or explanation.

            The requested direction is mandatory:
            - If the direction is "simplify," make the passage easier.
            - If the direction is "elevate," make the passage more sophisticated.
            - Never simplify when the requested direction is "elevate."
            - Never elevate when the requested direction is "simplify."

            Requested direction:
            {direction}

            Direction-specific instructions:
            {direction_instructions}
            """,
        ),
        (
            "human",
            """
            Requested operation: {direction}

            Adjust the passage from its current measured grade level of
            {current_grade} to approximately grade {target_grade}.

            Perform the requested operation exactly. Return one adjusted
            passage and nothing else.

            Original passage:
            {text}
            """,
        ),
    ]
)

revision_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You revise writing until it approaches a requested reading grade level.

            General rules:
            - Preserve every important fact and the original meaning.
            - Use the original passage to prevent factual drift.
            - Do not add facts, opinions, examples, or unsupported nuance.
            - Do not manipulate the score using filler or awkward sentences.
            - Keep specific names, quantities, dates, and technical terms accurate.
            - Make a meaningful revision instead of returning the same text.
            - Proofread for grammar, spelling, punctuation, and missing spaces.
            - Return only the revised passage.

            The requested direction is mandatory:
            - If the direction is "simplify," make the passage easier.
            - If the direction is "elevate," make the passage more sophisticated.
            - Never simplify when the requested direction is "elevate."
            - Never elevate when the requested direction is "simplify."

            Requested direction:
            {direction}

            Direction-specific instructions:
            {direction_instructions}
            """,
        ),
        (
            "human",
            """
            The current rewrite has these measurements:

            - Current Flesch-Kincaid grade: {current_grade}
            - Target grade: {target_grade}
            - Average sentence length: {average_sentence_length} words
            - Maximum dependency depth: {maximum_dependency_depth}

            The current text is still {direction_description}.

            Original passage:
            {original_text}

            Current rewrite:
            {current_text}
            """,
        ),
    ]
)

initial_chain = initial_prompt | structured_model
revision_chain = revision_prompt | structured_model

def adjust_text(
    text: str,
    target_grade: int,
    max_attempts: int = 3,
    tolerance: float = 0.5,
) -> dict:
    if not text.strip():
        raise ValueError("Text cannot be empty.")

    if target_grade < 1:
        raise ValueError("Target grade must be at least 1.")

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    original_metrics = analyze_readability(text)
    original_grade = original_metrics["flesch_kincaid_grade"]

    initial_direction = get_direction(
        current_grade=original_grade,
        target_grade=target_grade,
        tolerance=tolerance,
    )

    if initial_direction == "matched":
        return {
            "text": text.strip(),
            "metrics": original_metrics,
            "attempt_count": 0,
            "attempts": [],
            "direction": "matched",
        }

    initial_result = initial_chain.invoke(
        {
            "text": text,
            "current_grade": original_grade,
            "target_grade": target_grade,
            "direction": initial_direction,
            "direction_instructions": get_direction_instructions(initial_direction, target_grade),
        }
    )

    current_text = initial_result.rewritten_text.strip()

    attempts = []

    for attempt_number in range(1, max_attempts + 1):
        current_metrics = analyze_readability(current_text)
        current_grade = current_metrics["flesch_kincaid_grade"]

        attempts.append(
            {
                "attempt": attempt_number,
                "text": current_text,
                "metrics": current_metrics,
            }
        )

        distance_from_target = abs(current_grade - target_grade)

        if distance_from_target <= tolerance:
            break

        if attempt_number == max_attempts:
            break

        revision_direction = get_direction(
            current_grade=current_grade,
            target_grade=target_grade,
            tolerance=tolerance,
        )

        revision_result = revision_chain.invoke(
            {
                "original_text": text,
                "current_text": current_text,
                "current_grade": current_grade,
                "target_grade": target_grade,
                "average_sentence_length": current_metrics["average_sentence_length"],
                "maximum_dependency_depth": current_metrics["maximum_dependency_depth"],
                "direction": revision_direction,
                "direction_description": get_direction_description(revision_direction),
                "direction_instructions": get_direction_instructions(revision_direction, target_grade),
            }
        )

        revised_text = revision_result.rewritten_text.strip()

        if revised_text == current_text:
            break

        current_text = revised_text

    best_attempt = min(
        attempts,
        key=lambda attempt: abs(attempt["metrics"]["flesch_kincaid_grade"] - target_grade),
    )

    return {
        "text": best_attempt["text"],
        "metrics": best_attempt["metrics"],
        "attempt_count": len(attempts),
        "attempts": attempts,
        "direction": initial_direction,
    }