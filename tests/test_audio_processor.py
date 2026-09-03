import unittest
import os
import core.audio_processor as ap


class TestAudioProcessorNoYouTube(unittest.TestCase):
    def test_no_yt_dlp_in_audio_processor(self):
        """Verify yt-dlp is completely purged from audio_processor."""
        self.assertFalse(hasattr(ap, "yt_dlp"), "yt_dlp should not be imported in audio_processor")
        self.assertFalse(hasattr(ap, "download_youtube_audio"), "download_youtube_audio should be deleted")

    def test_no_yt_dlp_in_requirements(self):
        """Verify yt-dlp is purged from requirements.txt."""
        req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("yt-dlp", content.lower(), "yt-dlp must not be present in requirements.txt")

    def test_process_input_rejects_urls(self):
        """Verify process_input rejects URLs and strictly handles files."""
        with self.assertRaises(ValueError):
            ap.process_input("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


if __name__ == "__main__":
    unittest.main()
