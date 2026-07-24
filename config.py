"""
Local app configuration: where settings/session live on disk, and small
JSON load/save helpers used by the rest of the app.

Nothing here talks to the network -- this is purely local state:
- bookmark category names (the 6 color labels the user sets in Settings)
- the last-used server URL + a saved session token (after one-time login)
- small UI preferences (theme, last window size, etc. -- extend as needed)
"""

import json
import os
import sys

APP_NAME = "MyNote"


def config_dir() -> str:
    """
    Per-user config directory, created if missing.
    Windows: %APPDATA%\\MyNote
    Other OSes: ~/.pynotepad (kept simple; this app targets Windows first)
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(base, APP_NAME)
    else:
        path = os.path.expanduser(f"~/.{APP_NAME.lower()}")

    os.makedirs(path, exist_ok=True)
    return path


def config_file(name: str) -> str:
    return os.path.join(config_dir(), name)


def load_json(name: str, default):
    path = config_file(name)
    if not os.path.isfile(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        # Corrupt or unreadable config shouldn't crash the app -- fall back
        # to defaults, the user can re-save from Settings.
        return default


def save_json(name: str, data) -> None:
    path = config_file(name)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)  # atomic on both Windows and POSIX
