"""Persistent, local-only operator settings for ROOTWISE."""

import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_SETTINGS = {
    "color_enabled": True,
    "network_mode": "offline",
}
VALID_NETWORK_MODES = frozenset({"offline", "online"})


def settings_path() -> Path:
    """Return an absolute user configuration path."""
    configured_base = os.environ.get("XDG_CONFIG_HOME", "").strip()
    base = Path(configured_base).expanduser() if configured_base else Path("~/.config").expanduser()

    # Ignore empty or relative XDG paths to avoid writing settings into
    # whichever project directory happens to be the current working directory.
    if not base.is_absolute():
        base = Path("~/.config").expanduser()

    return base / "rootwise" / "settings.json"


def load_settings() -> dict:
    """Load settings, using safe defaults when the file is absent or invalid."""
    result = dict(DEFAULT_SETTINGS)
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return result

    if not isinstance(data, dict):
        return result

    if isinstance(data.get("color_enabled"), bool):
        result["color_enabled"] = data["color_enabled"]

    mode = data.get("network_mode")
    if isinstance(mode, str) and mode.lower() in VALID_NETWORK_MODES:
        result["network_mode"] = mode.lower()

    return result


def save_settings(settings: dict) -> Path:
    """Validate and atomically save settings outside the project."""
    if not isinstance(settings, dict):
        raise ValueError("Settings must be a dictionary.")

    color = settings.get("color_enabled", True)
    mode = settings.get("network_mode", "offline")

    if not isinstance(color, bool):
        raise ValueError("color_enabled must be true or false.")
    if not isinstance(mode, str) or mode.lower() not in VALID_NETWORK_MODES:
        raise ValueError("network_mode must be 'offline' or 'online'.")

    clean = {"color_enabled": color, "network_mode": mode.lower()}
    destination = settings_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=destination.parent,
            prefix=".settings-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(clean, temporary, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())

        os.replace(temporary_name, destination)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)

    return destination


def is_remote_repository(repository: str) -> bool:
    """Identify common remote Git URL formats."""
    source = repository.strip()
    if not source or source.lower().startswith("file://"):
        return False

    if re.match(r"^[A-Za-z]:[\\/]", source):
        return False

    parsed = urlparse(source)
    if parsed.scheme:
        return True

    return bool(re.match(r"^[^/\\\s]+@[^/\\\s:]+:.+", source))


def require_network_access(repository: str) -> None:
    """Block remote clones unless the operator explicitly enables online mode."""
    if is_remote_repository(repository):
        if load_settings()["network_mode"] != "online":
            raise ValueError(
                "Remote cloning is blocked in OFFLINE mode. "
                "Change Network mode to ONLINE in Operator Settings to allow "
                "this explicitly requested remote operation. "
                "Local repository paths remain available."
            )
