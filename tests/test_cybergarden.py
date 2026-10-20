"""Tests for the CYBERGARDEN presentation layer."""

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from rootwise.cybergarden import (
    MENU_FRAME_WIDTH,
    Neon,
    ask_path,
    dashboard_header,
    line,
    menu_frame_bottom,
    menu_frame_text,
    menu_frame_top,
    menu_item,
    menu_zone,
    neon_print,
    section,
)


class TestNeonPrint(unittest.TestCase):
    def test_plain_text_is_printed(self):
        output = io.StringIO()
        with redirect_stdout(output):
            neon_print("ROOTWISE", Neon.LIME)
        self.assertIn("ROOTWISE", output.getvalue())

    def test_no_color_output_contains_no_ansi_codes(self):
        output = io.StringIO()
        fake_sys = SimpleNamespace(
            stdout=Mock(isatty=Mock(return_value=True))
        )
        with (
            patch("rootwise.cybergarden.sys", fake_sys),
            patch.dict(
                "os.environ",
                {"NO_COLOR": "1", "TERM": "xterm-256color"},
                clear=True,
            ),
            redirect_stdout(output),
        ):
            neon_print("ROOTWISE", Neon.LIME)

        self.assertIn("ROOTWISE", output.getvalue())
        self.assertNotIn("\033[", output.getvalue())


class TestNeonEnabled(unittest.TestCase):
    def test_color_is_enabled_for_terminal_output(self):
        fake_sys = SimpleNamespace(
            stdout=Mock(isatty=Mock(return_value=True))
        )
        with (
            patch("rootwise.cybergarden.sys", fake_sys),
            patch.dict(
                "os.environ",
                {"TERM": "xterm-256color"},
                clear=True,
            ),
        ):
            self.assertTrue(Neon.enabled())

    def test_color_is_disabled_for_non_terminal_output(self):
        fake_sys = SimpleNamespace(
            stdout=Mock(isatty=Mock(return_value=False))
        )
        with (
            patch("rootwise.cybergarden.sys", fake_sys),
            patch.dict(
                "os.environ",
                {"TERM": "xterm-256color"},
                clear=True,
            ),
        ):
            self.assertFalse(Neon.enabled())

    def test_color_is_disabled_when_term_is_dumb(self):
        fake_sys = SimpleNamespace(
            stdout=Mock(isatty=Mock(return_value=True))
        )
        with (
            patch("rootwise.cybergarden.sys", fake_sys),
            patch.dict(
                "os.environ",
                {"TERM": "dumb"},
                clear=True,
            ),
        ):
            self.assertFalse(Neon.enabled())


class TestDashboardHeader(unittest.TestCase):
    def test_dashboard_header_runs_without_arguments(self):
        output = io.StringIO()
        with redirect_stdout(output):
            dashboard_header()
        self.assertTrue(output.getvalue().strip())

    def test_dashboard_header_preserves_rootwise_identity(self):
        output = io.StringIO()
        with redirect_stdout(output):
            dashboard_header()

        rendered = output.getvalue()
        self.assertIn("ROOTWISE://LOCAL", rendered)
        self.assertIn("REPOSITORY CARE // DIGITAL PRESERVATION", rendered)
        self.assertIn("INSPECT / PRESERVE / GROW", rendered)
        self.assertIn("LOCAL BY DESIGN // YOURS TO DIRECT", rendered)


class TestLine(unittest.TestCase):
    def test_line_prints_requested_character(self):
        output = io.StringIO()
        with redirect_stdout(output):
            line()
        self.assertTrue(output.getvalue().strip())

    def test_line_accepts_custom_character(self):
        output = io.StringIO()
        with redirect_stdout(output):
            line(char="=")
        self.assertIn("=", output.getvalue())


class TestSection(unittest.TestCase):
    def test_section_displays_uppercase_title(self):
        output = io.StringIO()
        with redirect_stdout(output):
            section("Repository Scan")
        self.assertIn("REPOSITORY SCAN", output.getvalue())


class TestMenuFrame(unittest.TestCase):
    def test_menu_frame_top_has_expected_borders(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_frame_top()
        self.assertIn("┌", output.getvalue())
        self.assertIn("┐", output.getvalue())

    def test_menu_frame_bottom_has_expected_borders(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_frame_bottom()
        self.assertIn("└", output.getvalue())
        self.assertIn("┘", output.getvalue())

    def test_menu_frame_edges_have_matching_width(self):
        top = io.StringIO()
        bottom = io.StringIO()

        with redirect_stdout(top):
            menu_frame_top()
        with redirect_stdout(bottom):
            menu_frame_bottom()

        top_line = top.getvalue().rstrip("\n")
        bottom_line = bottom.getvalue().rstrip("\n")

        self.assertEqual(len(top_line), len(bottom_line))
        self.assertEqual(len(top_line), MENU_FRAME_WIDTH + 6)

    def test_menu_frame_text_keeps_consistent_width(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_frame_text("ROOTWISE CONSOLE")

        self.assertEqual(
            len(output.getvalue().rstrip("\n")),
            MENU_FRAME_WIDTH + 6,
        )

    def test_menu_frame_text_displays_content_and_borders(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_frame_text("ROOTWISE")

        rendered = output.getvalue()
        self.assertIn("ROOTWISE", rendered)
        self.assertIn("│", rendered)

    def test_menu_zone_displays_uppercase_title(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_zone("Tend the Garden", Neon.LIME)

        self.assertIn("TEND THE GARDEN", output.getvalue())

    def test_menu_item_displays_key_and_label(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_item("1", "Repository scan")

        rendered = output.getvalue()
        self.assertIn("[1]", rendered)
        self.assertIn("Repository scan", rendered)

    def test_menu_item_line_has_expected_width(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_item("1", "Repository scan")

        self.assertEqual(
            len(output.getvalue().rstrip("\n")),
            MENU_FRAME_WIDTH + 6,
        )

    def test_menu_item_truncates_long_labels_to_preserve_frame(self):
        output = io.StringIO()
        with redirect_stdout(output):
            menu_item("1", "Repository scan " * 10)

        rendered = output.getvalue().rstrip("\n")
        self.assertEqual(len(rendered), MENU_FRAME_WIDTH + 6)
        self.assertIn("…", rendered)
        self.assertTrue(rendered.endswith(" │"))


class TestAskPath(unittest.TestCase):
    def test_ask_path_returns_path_object(self):
        with patch("builtins.input", return_value="/tmp/example"):
            result = ask_path("Repository path")

        self.assertEqual(result, Path("/tmp/example"))
        self.assertIsInstance(result, Path)


if __name__ == "__main__":
    unittest.main()
