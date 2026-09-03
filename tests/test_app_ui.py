import unittest
import os


class TestAppUINoEmojiNoYouTube(unittest.TestCase):
    def test_no_thunder_bolt_emoji_in_app(self):
        """Verify thunder bolt emoji is removed from sample meeting button in app.py."""
        app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("⚡", content, "⚡ emoji must be removed from app.py")
        self.assertIn('"Load Sample Meeting"', content, "Button must be labeled 'Load Sample Meeting'")

    def test_no_youtube_input_in_app(self):
        """Verify YouTube URL input and expander are purged from app.py."""
        app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("YouTube URL", content, "YouTube URL input must be removed from app.py")
        self.assertNotIn("youtube_url", content, "youtube_url variable must be removed from app.py")

    def test_no_youtube_prompt_in_main(self):
        """Verify YouTube URL prompt is removed from main.py."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "main.py")
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("YouTube", content, "YouTube prompt must be removed from main.py")


if __name__ == "__main__":
    unittest.main()
