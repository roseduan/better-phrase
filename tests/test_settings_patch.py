"""Tests for tools.settings_patch — the JSON editor used by install/uninstall."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

# Make tools/ importable from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import settings_patch  # noqa: E402


class SettingsPatchInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self.cmd = "/usr/local/bin/better-phrase.sh"

    def tearDown(self):
        self.tmp.cleanup()

    def _read(self):
        with self.settings.open() as f:
            return json.load(f)

    def _write(self, data):
        with self.settings.open("w") as f:
            json.dump(data, f)

    def _commands(self):
        entries = self._read()["hooks"]["UserPromptSubmit"]
        result = []
        for e in entries:
            if "hooks" in e:
                result.extend(h["command"] for h in e["hooks"])
            else:
                result.append(e["command"])
        return result

    def test_creates_file_when_missing(self):
        self.assertFalse(self.settings.exists())
        settings_patch.install(self.settings, self.cmd)
        self.assertTrue(self.settings.exists())
        self.assertEqual(self._commands(), [self.cmd])

    def test_preserves_unrelated_top_level_keys(self):
        self._write({"other": "value", "hooks": {"OtherEvent": []}})
        settings_patch.install(self.settings, self.cmd)
        data = self._read()
        self.assertEqual(data["other"], "value")
        self.assertIn("OtherEvent", data["hooks"])

    def test_purges_previous_better_phrase_entry(self):
        self._write({
            "hooks": {
                "UserPromptSubmit": [
                    {"matcher": "", "hooks": [
                        {"type": "command", "command": "/old/path/better-phrase.sh", "timeout": 10}
                    ]}
                ]
            }
        })
        settings_patch.install(self.settings, self.cmd)
        self.assertEqual(self._commands(), [self.cmd])

    def test_keeps_unrelated_hooks_in_same_event(self):
        self._write({
            "hooks": {
                "UserPromptSubmit": [
                    {"matcher": "", "hooks": [
                        {"type": "command", "command": "/usr/local/bin/some-other-hook.sh", "timeout": 5}
                    ]}
                ]
            }
        })
        settings_patch.install(self.settings, self.cmd)
        self.assertEqual(
            sorted(self._commands()),
            sorted([self.cmd, "/usr/local/bin/some-other-hook.sh"]),
        )

    def test_idempotent_on_rerun(self):
        settings_patch.install(self.settings, self.cmd)
        settings_patch.install(self.settings, self.cmd)
        self.assertEqual(self._commands(), [self.cmd])

    def test_flat_form_entry_purged_correctly(self):
        # Some Claude Code versions use flat entries (no matcher wrapper).
        self._write({
            "hooks": {
                "UserPromptSubmit": [
                    {"type": "command", "command": "/old/better-phrase.sh", "timeout": 10},
                    {"type": "command", "command": "/usr/local/bin/keep-me.sh", "timeout": 5},
                ]
            }
        })
        settings_patch.install(self.settings, self.cmd)
        # The flat keep-me entry should stay; only the new BP entry is appended.
        cmds = self._commands()
        self.assertIn("/usr/local/bin/keep-me.sh", cmds)
        self.assertIn(self.cmd, cmds)
        self.assertNotIn("/old/better-phrase.sh", cmds)


class SettingsPatchUninstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.settings = Path(self.tmp.name) / "settings.json"
        self.cmd = "/usr/local/bin/better-phrase.sh"

    def tearDown(self):
        self.tmp.cleanup()

    def _read(self):
        with self.settings.open() as f:
            return json.load(f)

    def _write(self, data):
        with self.settings.open("w") as f:
            json.dump(data, f)

    def test_removes_only_better_phrase_hook(self):
        self._write({
            "hooks": {
                "UserPromptSubmit": [
                    {"matcher": "", "hooks": [
                        {"type": "command", "command": self.cmd, "timeout": 10},
                        {"type": "command", "command": "/usr/local/bin/other.sh", "timeout": 5},
                    ]}
                ]
            }
        })
        settings_patch.uninstall(self.settings)
        entries = self._read()["hooks"]["UserPromptSubmit"]
        cmds = [h["command"] for e in entries for h in e["hooks"]]
        self.assertEqual(cmds, ["/usr/local/bin/other.sh"])

    def test_drops_event_key_when_no_entries_left(self):
        self._write({
            "hooks": {
                "UserPromptSubmit": [
                    {"matcher": "", "hooks": [
                        {"type": "command", "command": self.cmd, "timeout": 10}
                    ]}
                ]
            }
        })
        settings_patch.uninstall(self.settings)
        data = self._read()
        self.assertNotIn("UserPromptSubmit", data.get("hooks", {}))

    def test_drops_hooks_key_when_empty(self):
        self._write({
            "hooks": {
                "UserPromptSubmit": [
                    {"matcher": "", "hooks": [
                        {"type": "command", "command": self.cmd, "timeout": 10}
                    ]}
                ]
            }
        })
        settings_patch.uninstall(self.settings)
        self.assertNotIn("hooks", self._read())

    def test_no_op_when_file_missing(self):
        # Should NOT raise.
        settings_patch.uninstall(self.settings)
        self.assertFalse(self.settings.exists())

    def test_preserves_unrelated_top_level_keys(self):
        self._write({
            "other": "thing",
            "hooks": {
                "UserPromptSubmit": [
                    {"matcher": "", "hooks": [
                        {"type": "command", "command": self.cmd, "timeout": 10}
                    ]}
                ]
            }
        })
        settings_patch.uninstall(self.settings)
        self.assertEqual(self._read().get("other"), "thing")


if __name__ == "__main__":
    unittest.main()
