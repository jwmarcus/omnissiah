"""Tests for the shell-alias installer in omnissiah.cli.

Stdlib unittest. No network, writes only to a tempdir.
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from omnissiah.cli import (
    _ALIAS_BEGIN,
    _ALIAS_END,
    alias_block,
    detect_rc_file,
    install_aliases,
)


class AliasBlockTests(unittest.TestCase):
    def test_block_has_markers_and_both_aliases(self):
        block = alias_block()
        self.assertIn(_ALIAS_BEGIN, block)
        self.assertIn(_ALIAS_END, block)
        self.assertIn("alias claudex=", block)
        self.assertIn("alias claudexrc=", block)
        self.assertIn("--dangerously-skip-permissions", block)
        self.assertIn("--rc", block)
        self.assertNotIn("\u2014", block)  # no em dash


class InstallAliasesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.rc = Path(self._tmp.name) / ".zshrc"

    def tearDown(self):
        self._tmp.cleanup()

    def test_added_to_missing_file(self):
        msg = install_aliases(self.rc)
        self.assertTrue(self.rc.exists())
        text = self.rc.read_text(encoding="utf-8")
        self.assertIn("alias claudex=", text)
        self.assertIn("Added", msg)

    def test_preserves_existing_content(self):
        self.rc.write_text("export FOO=bar\n", encoding="utf-8")
        install_aliases(self.rc)
        text = self.rc.read_text(encoding="utf-8")
        self.assertIn("export FOO=bar", text)
        self.assertIn(_ALIAS_BEGIN, text)

    def test_idempotent_no_duplicate(self):
        install_aliases(self.rc)
        msg2 = install_aliases(self.rc)
        text = self.rc.read_text(encoding="utf-8")
        self.assertEqual(text.count(_ALIAS_BEGIN), 1)
        self.assertEqual(text.count(_ALIAS_END), 1)
        self.assertEqual(text.count("alias claudex="), 1)
        self.assertIn("Updated", msg2)

    def test_update_replaces_stale_block(self):
        self.rc.write_text(
            f"{_ALIAS_BEGIN}\nalias claudex=\"old-command\"\n{_ALIAS_END}\n",
            encoding="utf-8",
        )
        install_aliases(self.rc)
        text = self.rc.read_text(encoding="utf-8")
        self.assertNotIn("old-command", text)
        self.assertEqual(text.count(_ALIAS_BEGIN), 1)


class DetectRcFileTests(unittest.TestCase):
    def test_zsh(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.dict("os.environ", {"SHELL": "/usr/bin/zsh"}), mock.patch(
                "omnissiah.cli.Path.home", return_value=Path(d)
            ):
                self.assertEqual(detect_rc_file().name, ".zshrc")

    def test_bash(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.dict("os.environ", {"SHELL": "/bin/bash"}), mock.patch(
                "omnissiah.cli.Path.home", return_value=Path(d)
            ):
                self.assertEqual(detect_rc_file().name, ".bashrc")


if __name__ == "__main__":
    unittest.main()
