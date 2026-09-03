import os
from gtts import gTTS

SAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SAMPLE_DIR, "sample_meeting.mp3")

text = (
    "Welcome everyone to our weekly product sync. First, Alice confirmed that our Q3 "
    "marketing campaign is approved with a fifteen thousand dollar budget. Second, "
    "Bob will finalize the backend API deployment by this Thursday, and Carol will "
    "complete the frontend UI testing by Friday. Please make sure all security reviews "
    "are logged before our production release next Monday. Does anyone have open "
    "questions regarding the database migration? If not, let us wrap up."
)

if __name__ == "__main__":
    print("Generating demo meeting audio...")
    tts = gTTS(text=text, lang="en")
    tts.save(OUTPUT_FILE)
    print(f"Generated: {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE)} bytes)")
