from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
import os


load_dotenv()

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You rewrite text for readers at a requested grade level.

Follow these rules:
- Preserve the original meaning and important facts.
- Use vocabulary appropriate for the requested grade level.
- Shorten complicated sentences when helpful.
- Explain necessary technical terms in simple language.
- Do not add new facts or opinions.
- Return only the rewritten text, with no introduction or commentary.
""",
        ),
        (
            "human",
            """
Rewrite the following text for a reader at grade level {target_grade}:

{text}
""",
        ),
    ]
)

def create_model():
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        return ChatOllama(model="llama3.2", temperature=0)

    if provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    raise ValueError(f"Unsupported LLM provider: {provider}")

model = create_model()

output_parser = StrOutputParser()

simplification_chain = prompt | model | output_parser


def simplify_text(text: str, target_grade: int) -> str:
    simplified_text = simplification_chain.invoke(
        {
            "text": text,
            "target_grade": target_grade,
        }
    )

    return str(simplified_text)