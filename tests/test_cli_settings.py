"""Tests for ROOTWISE operator settings CLI."""

import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from rootwise.cli import main
from rootwise.settings import load_settings


class SettingsCliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(
            os.environ,
            {"XDG_CONFIG_HOME": self.temp_dir.name},
        )
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def run_settings(self, *args):
        output = StringIO()
        with redirect_stdout(output):
            result = main(["settings", *args])
        return result, output.getvalue()

    def test_settings_command_displays_defaults(self):
        result, output = self.run_settings()

        self.assertEqual(result, 0)
        self.assertIn("Color styling: ON", output)
        self.assertIn("Network mode:  OFFLINE", output)

    def test_color_preference_can_be_disabled_and_persisted(self):
        result, output = self.run_settings("--color", "off")

        self.assertEqual(result, 0)
        self.assertIn("Settings saved locally:", output)
        self.assertFalse(load_settings()["color_enabled"])

        _, output = self.run_settings()
        self.assertIn("Color styling: OFF", output)

    def test_network_mode_can_be_changed_and_persisted(self):
        result, output = self.run_settings("--network", "online")

        self.assertEqual(result, 0)
        self.assertEqual(load_settings()["network_mode"], "online")

        _, output = self.run_settings()
        self.assertIn("Network mode:  ONLINE", output)

    def test_both_settings_can_be_changed_together(self):
        result, _ = self.run_settings(
            "--color", "off",
            "--network", "online",
        )

        self.assertEqual(result, 0)
        settings = load_settings()
        self.assertFalse(settings["color_enabled"])
        self.assertEqual(settings["network_mode"], "online")


if __name__ == "__main__":
    unittest.main()
