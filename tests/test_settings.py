"""Tests for ROOTWISE operator settings."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rootwise import settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(
            os.environ, {"XDG_CONFIG_HOME": self.temp.name}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_defaults_are_offline(self):
        self.assertEqual(
            settings.load_settings(),
            {"color_enabled": True, "network_mode": "offline"},
        )

    def test_empty_xdg_config_home_uses_user_config_directory(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}):
            self.assertEqual(
                settings.settings_path(),
                Path.home() / ".config" / "rootwise" / "settings.json",
            )

    def test_relative_xdg_config_home_uses_user_config_directory(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "relative-config"}):
            self.assertEqual(
                settings.settings_path(),
                Path.home() / ".config" / "rootwise" / "settings.json",
            )

    def test_settings_persist(self):
        settings.save_settings({
            "color_enabled": False,
            "network_mode": "online",
        })
        self.assertEqual(
            settings.load_settings(),
            {"color_enabled": False, "network_mode": "online"},
        )

    def test_invalid_settings_are_rejected(self):
        with self.assertRaises(ValueError):
            settings.save_settings({
                "color_enabled": "yes", "network_mode": "offline"
            })
        with self.assertRaises(ValueError):
            settings.save_settings({
                "color_enabled": True, "network_mode": "sometimes"
            })

    def test_malformed_file_uses_defaults(self):
        path = settings.settings_path()
        path.parent.mkdir(parents=True)
        path.write_text("{invalid", encoding="utf-8")
        self.assertEqual(settings.load_settings(), settings.DEFAULT_SETTINGS)

    def test_local_paths_are_not_remote(self):
        for source in (".", "../repo", "/tmp/repo", "file:///tmp/repo"):
            with self.subTest(source=source):
                self.assertFalse(settings.is_remote_repository(source))

    def test_remote_urls_are_detected(self):
        for source in (
            "https://example.com/repo.git",
            "ssh://git@example.com/repo.git",
            "git@example.com:team/repo.git",
        ):
            with self.subTest(source=source):
                self.assertTrue(settings.is_remote_repository(source))

    def test_remote_clone_is_blocked_offline(self):
        with self.assertRaisesRegex(ValueError, "OFFLINE"):
            settings.require_network_access("https://example.com/repo.git")

    def test_remote_clone_is_allowed_online(self):
        settings.save_settings({
            "color_enabled": True, "network_mode": "online"
        })
        settings.require_network_access("https://example.com/repo.git")


if __name__ == "__main__":
    unittest.main()
