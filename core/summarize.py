import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()


def get_llm():
    """Return configured LLM: Groq (default: openai/gpt-oss-120b) or fallback to Mistral."""
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        from langchain_groq import ChatGroq
        model_name = os.getenv("GROQ_CHAT_MODEL", "openai/gpt-oss-120b")
        return ChatGroq(
            model=model_name,
            api_key=groq_key,
            temperature=0.3,
        )

    mistral_key = os.getenv("MISTRAL_API_KEY")
    if mistral_key:
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model="mistral-small-latest",
            mistral_api_key=mistral_key,
            temperature=0.3,
        )

    raise RuntimeError("Neither GROQ_API_KEY nor MISTRAL_API_KEY is configured.")


def split_transcript(transcript: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=16000,
        chunk_overlap=500,
    )
    return splitter.split_text(transcript)


def summarize(transcript: str) -> str:
    """Summarize transcript. Fast, single-pass with 16k chunking."""
    if not transcript or not transcript.strip():
        return "No transcript content available to summarize."

    llm = get_llm()
    chunks = split_transcript(transcript)

    if len(chunks) == 1:
        direct_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert meeting analyst. Produce a comprehensive, professional "
                    "executive summary of this meeting transcript using structured bullet points "
                    "grouped by topics discussed.",
                ),
                ("human", "{text}"),
            ]
        )
        chain = direct_prompt | llm | StrOutputParser()
        return chain.invoke({"text": chunks[0]})

    # Map-reduce for ultra-long transcripts
    map_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Summarize this portion of a meeting transcript concisely in bullet points."),
            ("human", "{text}"),
        ]
    )
    map_chain = map_prompt | llm | StrOutputParser()
    chunk_summaries = [map_chain.invoke({"text": chunk}) for chunk in chunks]
    combined = "\n\n".join(chunk_summaries)

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. Combine these partial meeting notes "
                "into one final, well-structured executive meeting summary with clear sections and bullet points.",
            ),
            ("human", "{text}"),
        ]
    )
    combined_chain = combined_prompt | llm | StrOutputParser()
    return combined_chain.invoke({"text": combined})


def generate_title(transcript: str) -> str:
    """Generate a clean, punchy professional title (max 8 words)."""
    if not transcript or not transcript.strip():
        return "Meeting Notes"

    llm = get_llm()
    title_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Based on the meeting transcript excerpt, generate a concise, professional meeting title "
                "(max 8 words). Return ONLY the title text, with no quotes or prefixes.",
            ),
            ("human", "{text}"),
        ]
    )
    title_chain = title_prompt | llm | StrOutputParser()
    return title_chain.invoke({"text": transcript[:3000]}).strip(' "\'')