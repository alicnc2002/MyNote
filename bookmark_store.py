"""
Per-file, per-line bookmark persistence.

Bookmarks live in a "bookmarks.json" sidecar stored in the same place the
bookmarked file itself lives:
  - local files  -> bookmarks.json next to the file, in the same folder
  - server files -> bookmarks.json in the same server folder (saved/ or
                    temp/) for the logged-in account, via the same
                    files/load.php + files/save.php endpoints used for
                    regular files -- no separate bookmark API needed

That's what makes bookmarks follow the file across machines: open the same
local folder (e.g. a synced or shared drive) or log into the same server
account from anywhere, and the bookmarks come back with it -- nothing is
tied to one computer's local settings.

A bookmarks.json in a folder isn't necessarily ours -- the user (or some
other tool) could already have a file with that exact name. Every sidecar
this module writes carries a signature key, and that signature is checked
before this module ever reads OR overwrites a discovered bookmarks.json. If
it's missing, the file is left completely untouched, and that particular
file's bookmarks quietly fall back to a private local store in the app's
config directory instead -- so nothing of the user's is ever clobbered.
"""

import json
import os

import config
from api_client import ApiClient, ApiError

SIGNATURE_KEY = "__pynotepad_bookmark_store__"
SIGNATURE_VALUE = 1
SIDECAR_FILENAME = "bookmarks.json"

FALLBACK_FILE = "bookmarks_fallback.json"  # app config dir -- only used for
                                            # a file whose folder already has
                                            # an unrecognized bookmarks.json


# ---- location adapters ------------------------------------------------------
# Both expose the same tiny interface (read/write/identity_key), so the
# merge-and-verify logic below doesn't care whether the sidecar lives on
# disk or on the server.

class LocalLocation:
    def __init__(self, folder: str):
        self.folder = folder
        self.path = os.path.join(folder, SIDECAR_FILENAME)

    def read(self):
        if not os.path.isfile(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return None

    def write(self, text: str):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, self.path)

    def identity_key(self, entry_key: str) -> str:
        return "local::" + os.path.normcase(os.path.join(self.folder, entry_key))


class ServerLocation:
    def __init__(self, client: ApiClient, folder: str):
        self.client = client
        self.folder = folder

    def read(self):
        try:
            return self.client.load_file(SIDECAR_FILENAME, folder=self.folder)
        except ApiError:
            return None  # not found, or unreachable -- treated as "no sidecar yet"

    def write(self, text: str):
        self.client.save_file(SIDECAR_FILENAME, text, folder=self.folder)

    def identity_key(self, entry_key: str) -> str:
        return f"server::{self.client.base_url.rstrip('/')}::{self.folder}/{entry_key}"


# ---- sidecar parse/serialize -------------------------------------------------

def _parse_sidecar(text):
    """Returns the {filename: {line: cat}} map if text is a recognizably-
    ours sidecar, or None if it's missing, foreign, or corrupt (all three
    are handled identically: don't touch it)."""
    if not text:
        return None
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict) or data.get(SIGNATURE_KEY) != SIGNATURE_VALUE:
        return None
    files = data.get("files")
    return files if isinstance(files, dict) else {}


def _serialize_sidecar(files: dict) -> str:
    return json.dumps({SIGNATURE_KEY: SIGNATURE_VALUE, "files": files}, indent=2)


# ---- private fallback store (local app config dir) ---------------------------

def _fallback_all() -> dict:
    return config.load_json(FALLBACK_FILE, {})


def _fallback_load(identity: str) -> dict:
    raw = _fallback_all().get(identity, {})
    return {int(line): cat for line, cat in raw.items()}


def _fallback_save(identity: str, bookmarks: dict) -> None:
    all_data = _fallback_all()
    if bookmarks:
        all_data[identity] = {str(line): cat for line, cat in bookmarks.items()}
    else:
        all_data.pop(identity, None)
    config.save_json(FALLBACK_FILE, all_data)


# ---- public API ---------------------------------------------------------------

def load_bookmarks(location, entry_key: str) -> dict:
    """{line: category} for entry_key at this location."""
    files = _parse_sidecar(location.read())
    if files is None:
        # No sidecar yet, or an unrecognized one -- nothing of ours to read
        # from the shared file either way; check the private fallback.
        return _fallback_load(location.identity_key(entry_key))
    return {int(line): cat for line, cat in files.get(entry_key, {}).items()}


def save_bookmarks(location, entry_key: str, bookmarks: dict) -> None:
    """Persists entry_key's bookmarks at this location. An empty dict
    clears them."""
    text = location.read()
    files = _parse_sidecar(text)

    if files is None and text:
        # Something's already there and it isn't ours -- never overwrite a
        # file we don't recognize. Keep this file's bookmarks private
        # instead.
        _fallback_save(location.identity_key(entry_key), bookmarks)
        return

    files = dict(files or {})
    if bookmarks:
        files[entry_key] = {str(line): cat for line, cat in bookmarks.items()}
    else:
        files.pop(entry_key, None)

    try:
        location.write(_serialize_sidecar(files))
    except (OSError, ApiError):
        # Couldn't reach disk/server right now -- don't lose the bookmarks,
        # keep them in the fallback store until the next successful save.
        _fallback_save(location.identity_key(entry_key), bookmarks)


def rekey(old_location, old_entry_key, new_location, new_entry_key) -> None:
    """Moves an entry's bookmarks from one (location, entry_key) to
    another -- used when a buffer's identity changes (first save, Save As,
    first save-to-server)."""
    if old_location is None or old_entry_key is None:
        return

    old_id = old_location.identity_key(old_entry_key)
    new_id = new_location.identity_key(new_entry_key) if new_location else None
    if old_id == new_id:
        return  # same slot -- nothing to move

    bookmarks = load_bookmarks(old_location, old_entry_key)
    if not bookmarks:
        return
    if new_location is not None:
        save_bookmarks(new_location, new_entry_key, bookmarks)
    save_bookmarks(old_location, old_entry_key, {})
