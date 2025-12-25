import sys
import types
import unittest

from settings_manager import SettingsManager


class FakeOllamaManager:
    def __init__(self):
        self.ollama_ready = True

    def chat(self, model, messages, options=None):
        content = f"{model}::{messages[-1]['content'][:20]}"
        return {"message": {"content": content}}


class DummyAppState:
    def __init__(self):
        self.settings_manager = SettingsManager()
        self.ollama_manager = FakeOllamaManager()
        self.root = None
        self.status_bar = None

    def set_active_model(self, model_type):
        return None


main_mod = types.ModuleType("main")
main_mod.app_state = DummyAppState()
sys.modules["main"] = main_mod

import processing_functions as pf


class TestPipeline(unittest.TestCase):
    def test_run_full_pipeline(self):
        phases = []

        def cb(phase, message, content):
            phases.append(phase)

        results = pf.run_full_pipeline("test prompt", progress_cb=cb)
        for key in ["analysis", "generation", "vetting", "final", "enhanced", "comprehensive"]:
            self.assertIn(key, results)
            self.assertTrue(results[key])

        self.assertEqual(phases[0], "start")
        self.assertIn("complete", phases)

if __name__ == "__main__":
    unittest.main()
