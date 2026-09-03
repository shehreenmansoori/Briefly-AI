from dotenv import load_dotenv
from core.audio_processor import process_input, cleanup_audio_files
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()


def run_pipeline(source: str, language: str = "english") -> dict:
    print("Starting AI video assistant...")

    chunks, temp_files = process_input(source)
    try:
        transcript = transcribe_all(chunks, language)
        print(f"Raw transcription (first 300 characters):\n{transcript[:300]}...")

        title = generate_title(transcript)
        summary = summarize(transcript)
        action_item = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)
        rag_chain = build_rag_chain(transcript)

        return {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_item,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }
    finally:
        cleanup_audio_files(temp_files)


if __name__ == "__main__":
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"Title: {result['title']}")
    print(f"\nSummary:\n{result['summary']}")
    print(f"\nAction Items:\n{result['action_items']}")
    print(f"\nKey Decisions:\n{result['key_decisions']}")
    print(f"\nOpen Questions:\n{result['open_questions']}")
    print("=" * 60)

    # Phase 2 — Chat with your meeting via RAG
    print("\nChat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    history = []
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question, history)
        history.append(("user", question))
        history.append(("assistant", answer))
        print(f"\nAssistant: {answer}\n")
