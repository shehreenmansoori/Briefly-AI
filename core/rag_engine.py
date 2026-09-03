import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.vector_store import build_vector_store, load_vector_store, get_retreiver

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

    raise RuntimeError(
        "Neither GROQ_API_KEY nor MISTRAL_API_KEY is configured. "
        "Set GROQ_API_KEY in .env for fast LPU inference."
    )


def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])


def normalize_input(val):
    """Ensure both string inputs and dict inputs work seamlessly."""
    if isinstance(val, str):
        return {"question": val, "chat_history": "None"}
    return {
        "question": val.get("question", ""),
        "chat_history": val.get("chat_history", "None") or "None",
    }


def build_rag_chain(transcript: str):
    vector_store = build_vector_store(transcript)
    retriever = get_retreiver(vector_store)
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert meeting assistant. Answer the user's question 
based on the meeting transcript context provided below and the recent chat history.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Always be concise, factual, and direct. If quoting someone, mention it clearly.

Recent Chat History:
{chat_history}

Context from meeting transcript:
{context}""",
            ),
            ("human", "{question}"),
        ]
    )

    rag_chain = (
        RunnableLambda(normalize_input)
        | {
            "context": RunnableLambda(lambda x: x["question"]) | retriever | RunnableLambda(format_docs),
            "question": RunnableLambda(lambda x: x["question"]),
            "chat_history": RunnableLambda(lambda x: x["chat_history"]),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


def load_rag_chain():
    vector_store = load_vector_store()
    retriever = get_retreiver(vector_store)
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert meeting assistant. Answer the user's question 
based on the meeting transcript context provided below.

If the answer is not found in the context, say: 
"I could not find this information in the meeting transcript."

Context from meeting transcript:
{context}""",
            ),
            ("human", "{question}"),
        ]
    )

    rag_chain = (
        RunnableLambda(normalize_input)
        | {
            "context": RunnableLambda(lambda x: x["question"]) | retriever | RunnableLambda(format_docs),
            "question": RunnableLambda(lambda x: x["question"]),
            "chat_history": RunnableLambda(lambda x: x["chat_history"]),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


def ask_question(rag_chain, question: str, chat_history: list = None) -> str:
    """Invoke RAG chain and return full answer string."""
    formatted_history = "None"
    if chat_history:
        recent_turns = chat_history[-6:]
        formatted_history = "\n".join([f"{role.capitalize()}: {msg}" for role, msg in recent_turns])

    payload = {"question": question, "chat_history": formatted_history}
    return rag_chain.invoke(payload)


def stream_answer(rag_chain, question: str, chat_history: list = None):
    """Generator yielding answer tokens live for Streamlit st.write_stream."""
    formatted_history = "None"
    if chat_history:
        recent_turns = chat_history[-6:]
        formatted_history = "\n".join([f"{role.capitalize()}: {msg}" for role, msg in recent_turns])

    payload = {"question": question, "chat_history": formatted_history}
    for chunk in rag_chain.stream(payload):
        yield chunk