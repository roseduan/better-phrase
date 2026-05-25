from __future__ import annotations

import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        os.environ["BETTER_PHRASE_HOME"] = self._tmpdir.name
        # Reload the module so its _config_dir() picks up the new env var.
        from better_phrase import config

        importlib.reload(config)
        self.config = config

    def tearDown(self):
        self._tmpdir.cleanup()
        os.environ.pop("BETTER_PHRASE_HOME", None)

    def test_defaults_when_no_file(self):
        self.assertTrue(self.config.get_translate_enabled())
        self.assertTrue(self.config.should_show_hint())

    def test_set_and_get_translate(self):
        self.config.set_translate_enabled(False)
        self.assertFalse(self.config.get_translate_enabled())

        self.config.set_translate_enabled(True)
        self.assertTrue(self.config.get_translate_enabled())

    def test_invalid_json_falls_back_to_defaults(self):
        cfg_path = Path(self._tmpdir.name) / "config.json"
        cfg_path.write_text("not json {", encoding="utf-8")
        self.assertTrue(self.config.get_translate_enabled())

    def test_hint_counter_stops_at_limit(self):
        for _ in range(self.config.HINT_LIMIT):
            self.assertTrue(self.config.should_show_hint())
            self.config.increment_hint_count()
        self.assertFalse(self.config.should_show_hint())

    def test_partial_config_preserves_defaults(self):
        cfg_path = Path(self._tmpdir.name) / "config.json"
        cfg_path.write_text(json.dumps({"translate_enabled": False}), encoding="utf-8")
        # hint_shown_count not in file, but should default to 0.
        self.assertTrue(self.config.should_show_hint())
        self.assertFalse(self.config.get_translate_enabled())

    def test_set_translate_preserves_hint_count(self):
        self.config.increment_hint_count()
        self.config.increment_hint_count()
        self.config.set_translate_enabled(False)
        # hint count should still be 2
        cfg = self.config.load()
        self.assertEqual(cfg["hint_shown_count"], 2)

if __name__ == "__main__":
    unittest.main()
