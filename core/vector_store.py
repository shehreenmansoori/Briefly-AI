import os
from dotenv import load_dotenv
from langchain_mistralai import MistralAIEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()


def get_embeddings():
    """Use Mistral API embeddings - 0 MB local RAM, fast, high semantic quality."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY is not set in environment / .env")
    return MistralAIEmbeddings(model="mistral-embed", mistral_api_key=api_key)


def build_vector_store(transcript: str) -> InMemoryVectorStore:
    """
    Build an in-memory vector store strictly isolated to this meeting session.
    Zero global mutable state: prevents race conditions across concurrent users.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={"chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    vector_store = InMemoryVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
    )
    return vector_store


def load_vector_store() -> InMemoryVectorStore:
    """Return a fresh empty in-memory vector store."""
    embeddings = get_embeddings()
    return InMemoryVectorStore(embedding=embeddings)


def get_retreiver(vector_store, k: int = 4):
    """Return retriever from vector store with top-k similarity search."""
    return vector_store.as_retriever(
        search_kwargs={"k": k}
    )
