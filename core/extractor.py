import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

load_dotenv()


def get_llm():
    """Prefer Groq Llama-3.3-70b-versatile for fast extraction; fallback to Mistral if Groq key missing."""
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.2,
        )

    mistral_key = os.getenv("MISTRAL_API_KEY")
    if mistral_key:
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model="mistral-small-latest",
            mistral_api_key=mistral_key,
            temperature=0.2,
        )

    raise RuntimeError("Neither GROQ_API_KEY nor MISTRAL_API_KEY is configured.")


def build_chain(system_prompt: str):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{text}"),
        ]
    )
    return (
        RunnablePassthrough()
        | RunnableLambda(lambda x: {"text": x})
        | prompt
        | llm
        | StrOutputParser()
    )


def extract_action_items(transcript: str) -> str:
    if not transcript or not transcript.strip():
        return "No action items found (empty transcript)."
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each item provide:\n"
        "- Task description\n"
        "- Owner (who is responsible, or 'Unassigned')\n"
        "- Deadline (if mentioned, else 'Not specified')\n\n"
        "Format as a clean markdown numbered list. If none found, write 'No action items found.'"
    )
    return chain.invoke(transcript)


def extract_key_decisions(transcript: str) -> str:
    if not transcript or not transcript.strip():
        return "No key decisions found (empty transcript)."
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions agreed upon. Format as a clean markdown numbered list. "
        "If none found, write 'No key decisions found.'"
    )
    return chain.invoke(transcript)


def extract_questions(transcript: str) -> str:
    if not transcript or not transcript.strip():
        return "No open questions found (empty transcript)."
    chain = build_chain(
        "From the meeting transcript, extract all unresolved questions, blockers, "
        "or topics requiring follow-up. Format as a clean markdown numbered list. "
        "If none found, write 'No open questions found.'"
    )
    return chain.invoke(transcript)
