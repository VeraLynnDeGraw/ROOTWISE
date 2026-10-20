"""Tests for the standalone ROOTWISE neon terminal menu."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from rootwise.menu import run_menu


class MenuFlowTests(unittest.TestCase):
    def test_menu_displays_neon_dashboard_and_options(self):
        output = io.StringIO()

        with patch("builtins.input", side_effect=["q"]):
            with redirect_stdout(output):
                run_menu()

        rendered = output.getvalue()

        self.assertIn("ROOTWISE://LOCAL", rendered)
        self.assertIn("REPOSITORY CARE // DIGITAL PRESERVATION", rendered)
        self.assertIn("LOCAL BY DESIGN", rendered)
        self.assertIn("YOURS TO DIRECT", rendered)
        self.assertIn("ROOTWISE CONSOLE", rendered)
        self.assertIn("TEND THE GARDEN", rendered)
        self.assertIn("PRESERVE", rendered)
        self.assertIn("OBSERVE CHANGE", rendered)
        self.assertIn("FIELD GUIDE", rendered)

        for option in (
            "[1] Repository scan",
            "[2] Create snapshot",
            "[3] Verify snapshot",
            "[4] Restore snapshot",
            "[5] Sync observation",
            "[6] Repository health report",
            "[7] Operator reference",
            "[q] Disconnect",
        ):
            self.assertIn(option, rendered)

        self.assertIn(
            "SESSION CLOSED // YOUR FILES REMAIN YOURS",
            rendered,
        )

    def test_menu_handles_end_of_input_cleanly(self):
        output = io.StringIO()

        with patch("builtins.input", side_effect=EOFError):
            with redirect_stdout(output):
                run_menu()

        self.assertIn(
            "SESSION CLOSED // YOUR FILES REMAIN YOURS",
            output.getvalue(),
        )

    def test_menu_handles_keyboard_interrupt_at_prompt(self):
        output = io.StringIO()

        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with redirect_stdout(output):
                run_menu()

        self.assertIn(
            "SESSION CLOSED // YOUR FILES REMAIN YOURS",
            output.getvalue(),
        )

    def test_invalid_choice_returns_to_menu(self):
        output = io.StringIO()

        with patch("builtins.input", side_effect=["x", "", "q"]):
            with redirect_stdout(output):
                run_menu()

        rendered = output.getvalue()

        self.assertIn("[INVALID INPUT] Select 1-7 or q.", rendered)
        self.assertGreaterEqual(
            rendered.count("ROOTWISE://LOCAL"),
            2,
        )
        self.assertIn(
            "SESSION CLOSED // YOUR FILES REMAIN YOURS",
            rendered,
        )

    def test_menu_uses_local_presentation_module(self):
        import rootwise.menu as menu_module
        import rootwise.cybergarden as presentation_module

        self.assertIs(menu_module.Neon, presentation_module.Neon)
        self.assertTrue(callable(menu_module.dashboard_header))


if __name__ == "__main__":
    unittest.main()
