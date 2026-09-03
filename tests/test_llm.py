import unittest
import os
from dotenv import load_dotenv

load_dotenv()


class TestLLMModelConfiguration(unittest.TestCase):
    def test_get_llm_invokes_successfully_without_404(self):
        """Verify get_llm does not request non-existent model (like llama-3.3-70b-versatile)."""
        from core.extractor import get_llm
        llm = get_llm()
        # Verify model name is NOT the invalid llama-3.3-70b-versatile
        self.assertNotEqual(
            getattr(llm, "model_name", getattr(llm, "model", "")),
            "llama-3.3-70b-versatile",
            "Model should not be hardcoded to inaccessible llama-3.3-70b-versatile"
        )
        # Test real invocation
        response = llm.invoke("Say test")
        self.assertTrue(len(response.content) > 0)


if __name__ == "__main__":
    unittest.main()
