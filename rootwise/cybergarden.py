"""CYBERGARDEN terminal presentation layer for ROOTWISE.

This module owns visual presentation only. It does not inspect repositories,
create snapshots, make decisions, or modify project files.
"""

import os
import sys
from pathlib import Path


class Neon:
    """Cyberpunk botanical palette with a plain-text fallback."""

    # Core palette
    BACKGROUND = "#080D0C"
    LIME_HEX = "#B6FF4A"
    PINK_HEX = "#FF35B8"
    YELLOW_HEX = "#F8FF38"
    CYAN_HEX = "#43E8FF"
    ORANGE_HEX = "#FF9138"
    PURPLE_HEX = "#C77DFF"

    # ANSI terminal equivalents
    CYAN = "\033[38;5;51m"
    MAGENTA = "\033[38;5;201m"
    LIME = "\033[38;5;118m"
    PURPLE = "\033[38;5;141m"
    BLUE = "\033[38;5;39m"
    PINK = "\033[38;5;213m"
    AMBER = "\033[38;5;220m"
    RED = "\033[38;5;196m"
    DIM = "\033[38;5;244m"
    WHITE = "\033[38;5;255m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def enabled(cls) -> bool:
        """Enable ANSI styling only when the output supports it."""
        return (
            sys.stdout.isatty()
            and "NO_COLOR" not in os.environ
            and os.environ.get("TERM") != "dumb"
        )

    @classmethod
    def paint(cls, text: str, *styles: str) -> str:
        """Apply terminal styles when color output is available."""
        if not cls.enabled():
            return text
        return "".join(styles) + text + cls.RESET


def neon_print(
    text: str = "",
    *styles: str,
    end: str = "\n",
) -> None:
    """Print text with optional CYBERGARDEN styling."""
    print(Neon.paint(text, *styles), end=end)


def line(char: str = "━", color: str | None = None) -> None:
    """Draw a consistent terminal divider."""
    neon_print("  " + char * 46, color or Neon.DIM)


def _dashboard_line(text: str, color: str, *styles: str) -> None:
    """Print one dashboard line aligned to the 52-character banner."""
    inner_width = 48
    content = f"  {text}"[:inner_width].ljust(inner_width)
    neon_print(f"  |{content}|", color, *styles)


def dashboard_header() -> None:
    """Display the ROOTWISE identity in the local terminal dashboard."""
    neon_print()
    neon_print("  +------------------------------------------------+", Neon.PURPLE)
    _dashboard_line("ROOTWISE://LOCAL", Neon.CYAN, Neon.BOLD)
    _dashboard_line("REPOSITORY CARE // DIGITAL PRESERVATION", Neon.PINK)
    _dashboard_line("INSPECT / PRESERVE / GROW", Neon.LIME, Neon.BOLD)
    _dashboard_line("LOCAL BY DESIGN // YOURS TO DIRECT", Neon.CYAN)
    neon_print("  +------------------------------------------------+", Neon.PURPLE)
    neon_print()


def section(title: str) -> None:
    """Display a consistent section heading."""
    neon_print()
    neon_print(f"  ◈ {title.upper()}", Neon.PINK, Neon.BOLD)
    line("─", Neon.PURPLE)


MENU_FRAME_WIDTH = 46


def menu_frame_top() -> None:
    """Draw the top edge of the lime-green menu frame."""
    neon_print(
        "  ┌" + "─" * (MENU_FRAME_WIDTH + 2) + "┐",
        Neon.LIME,
        Neon.BOLD,
    )


def menu_frame_bottom() -> None:
    """Draw the bottom edge of the lime-green menu frame."""
    neon_print(
        "  └" + "─" * (MENU_FRAME_WIDTH + 2) + "┘",
        Neon.LIME,
        Neon.BOLD,
    )


def menu_frame_text(text: str = "", *styles: str) -> None:
    """Print a padded line inside the menu frame."""
    content = (" " + text)[:MENU_FRAME_WIDTH].ljust(MENU_FRAME_WIDTH)
    neon_print("  │ ", Neon.LIME, end="")
    neon_print(content, *styles, end="")
    neon_print(" │", Neon.LIME)


def menu_zone(title: str, color: str = Neon.PINK) -> None:
    """Display a named group inside the terminal menu frame."""
    menu_frame_text(f"◈ {title.upper()}", color, Neon.BOLD)
    menu_frame_text("─" * (MENU_FRAME_WIDTH - 1), color)


def menu_item(
    key: str,
    label: str,
    key_color: str = Neon.MAGENTA,
    label_color: str = Neon.WHITE,
) -> None:
    """Display a framed menu choice without breaking the frame width."""
    available_label_width = MENU_FRAME_WIDTH - len(key) - 4

    if len(label) > available_label_width:
        label = label[: available_label_width - 1] + "…"

    content = f" [{key}] {label}"
    padding = max(0, MENU_FRAME_WIDTH - len(content))
    neon_print("  │ ", Neon.LIME, end="")
    neon_print(" ", end="")
    neon_print(f"[{key}] ", key_color, Neon.BOLD, end="")
    neon_print(label, label_color, end="")
    neon_print(" " * padding, end="")
    neon_print(" │", Neon.LIME)


def ask_path(prompt: str, default: str | None = None) -> Path:
    """Prompt for a filesystem path."""
    hint = f" [{default}]" if default else ""
    answer = input(
        Neon.paint(f"  > {prompt}{hint}: ", Neon.CYAN, Neon.BOLD)
    ).strip()

    if not answer and default is not None:
        answer = default

    if not answer:
        raise ValueError("A path is required.")

    return Path(answer).expanduser()
