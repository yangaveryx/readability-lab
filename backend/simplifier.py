import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

from readability import analyze_readability


load_dotenv()

def create_model():
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        return ChatOllama(model="llama3.2", temperature=0,)

    if provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0,)

    raise ValueError(f"Unsupported LLM provider: {provider}")

model = create_model()
output_parser = StrOutputParser()

initial_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You rewrite text for readers at a requested grade level.

            Follow these rules:
            - Preserve every important fact and the original meaning.
            - Do not replace precise terms with inaccurate or vague alternatives.
            - Keep essential terms, but explain them simply when needed.
            - Use vocabulary appropriate for the requested grade level.
            - Break complicated sentences into shorter sentences when helpful.
            - Do not add facts, opinions, or claims.
            - Proofread for spelling, grammar, and missing spaces.
            - Return only the rewritten text. Do not include a title, label, introduction, explanation, or phrases.
            """,
        ),
        (
            "human",
            """
            Rewrite this text for a reader at grade level {target_grade}.

            Original text:
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
            You revise text to meet a target reading grade.

            Rules:
            - Preserve every important fact in the original.
            - Keep the names of specific scientific substances and concepts.
            - Do not replace a specific term with a vague or inaccurate term.
            - Use short sentences with no more than {maximum_sentence_words} words.
            - Split sentences instead of removing important information.
            - Check carefully for missing spaces, spelling errors, and grammar errors.
            - Make a meaningful revision rather than returning the current rewrite unchanged.
            - Return only the revised text. Do not include a title, label, introduction, explanation, or phrases.
            """,
        ),
        (
            "human",
            """
            The current rewrite has these measurements:

            - Flesch-Kincaid grade: {current_grade}
            - Average sentence length: {average_sentence_length} words
            - Maximum dependency depth: {maximum_dependency_depth}
            - Target grade: {target_grade}

            The measured grade is still too high. Simplify the text further,
            especially by shortening its sentences.

            Original text:
            {original_text}

            Current rewrite:
            {current_text}
            """,
        ),
    ]
)

initial_chain = initial_prompt | model | output_parser
revision_chain = revision_prompt | model | output_parser

def get_maximum_sentence_words(target_grade: int) -> int:
    if target_grade <= 5:
        return 8

    if target_grade <= 8:
        return 12

    return 16

def simplify_text(
    text: str,
    target_grade: int,
    max_attempts: int = 3,
    tolerance: float = 0.5,
) -> dict:
    """
    Rewrite text toward a target grade level.

    max_attempts includes the initial rewrite, so a value of 3 permits:
    - 1 initial rewrite
    - up to 2 revisions
    """
    if not text.strip():
        raise ValueError("Text cannot be empty.")

    if target_grade < 1:
        raise ValueError("Target grade must be at least 1.")

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    current_text = str(
        initial_chain.invoke(
            {
                "text": text,
                "target_grade": target_grade,
            }
        )
    ).strip()

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

        if current_grade <= target_grade + tolerance:
            break

        if attempt_number == max_attempts:
            break

        revised_text = str(
            revision_chain.invoke(
                {
                    "original_text": text,
                    "current_text": current_text,
                    "current_grade": current_grade,
                    "average_sentence_length": current_metrics["average_sentence_length"],
                    "maximum_dependency_depth": current_metrics["maximum_dependency_depth"],
                    "target_grade": target_grade,
                    "maximum_sentence_words": get_maximum_sentence_words(target_grade),
                }
            )
        ).strip()

        if revised_text == current_text:
            break

        current_text = revised_text

    best_attempt = min(
        attempts,
        key=lambda attempt: abs(
            attempt["metrics"]["flesch_kincaid_grade"] - target_grade
        ),
    )

    return {
        "text": best_attempt["text"],
        "metrics": best_attempt["metrics"],
        "attempt_count": len(attempts),
        "attempts": attempts,
    }