"""Tests for the interactive ROOTWISE operator settings screen."""

import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from rootwise.cybergarden import Neon
from rootwise.menu import run_menu, show_settings
from rootwise.settings import load_settings


class MenuSettingsTests(unittest.TestCase):
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

    def run_settings_screen(self, answers):
        output = StringIO()
        with patch("builtins.input", side_effect=answers):
            with redirect_stdout(output):
                show_settings()
        return output.getvalue()

    def test_settings_screen_displays_current_preferences(self):
        output = self.run_settings_screen([""])

        self.assertIn("Color styling: ON", output)
        self.assertIn("Network mode:  OFFLINE", output)

    def test_settings_screen_saves_color_preference(self):
        output = self.run_settings_screen(["c", "off"])

        self.assertIn("Settings saved locally:", output)
        self.assertFalse(load_settings()["color_enabled"])

    def test_settings_screen_saves_network_preference(self):
        output = self.run_settings_screen(["n", "online"])

        self.assertIn("Settings saved locally:", output)
        self.assertEqual(load_settings()["network_mode"], "online")

    def test_invalid_setting_does_not_change_preferences(self):
        output = self.run_settings_screen(["n", "sometimes"])

        self.assertIn("No change: enter offline or online.", output)
        self.assertEqual(load_settings()["network_mode"], "offline")

    def test_color_preference_disables_ansi_styling(self):
        with patch(
            "rootwise.cybergarden.load_settings",
            return_value={
                "color_enabled": False,
                "network_mode": "offline",
            },
        ), patch("rootwise.cybergarden.sys.stdout") as stdout:
            stdout.isatty.return_value = True
            self.assertFalse(Neon.enabled())
            self.assertEqual(Neon.paint("ROOTWISE", Neon.PINK), "ROOTWISE")

    def test_menu_lists_operator_settings(self):
        output = StringIO()

        with patch("builtins.input", side_effect=["q"]):
            with redirect_stdout(output):
                run_menu()

        self.assertIn("[11] Operator Settings", output.getvalue())


if __name__ == "__main__":
    unittest.main()
