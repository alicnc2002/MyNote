"""
Thin REST client for the MyNote PHP backend (see server/ folder) --
plain HTTPS + JSON, bearer-token auth after login. base_url should point at
wherever you uploaded the server/ folder, e.g. "https://yourdomain.com/api".

Server contract (implemented in server/login.php, server/setup.php, and
server/files/*.php):
    POST {base_url}/setup.php
        body: {"username": ..., "password": ..., "storage_dir": ... (optional)}
        200 -> {"success": true, "token": "...", "username": "..."}
        409 -> {"error": "..."}  (already configured -- runs once only)

    POST {base_url}/login.php
        body: {"username": ..., "password": ...}
        200 -> {"token": "..."}

    POST {base_url}/files/save.php
        header: Authorization: Bearer <token>
        body: {"filename": ..., "content": ..., "folder": "saved" | "temp"}
        200 -> {"id": ..., "filename": ...}

    GET {base_url}/files/list.php?folder=saved|temp
        header: Authorization: Bearer <token>
        200 -> {"files": [{"filename": ..., "size": ..., "modified": ...}, ...]}

    GET {base_url}/files/load.php?filename=...&folder=saved|temp
        header: Authorization: Bearer <token>
        200 -> {"filename": ..., "folder": ..., "content": "..."}

    POST {base_url}/files/delete.php
        header: Authorization: Bearer <token>
        body: {"filename": ..., "folder": "saved" | "temp" | <custom>}
        200 -> {"success": true}

    POST {base_url}/files/create_folder.php
        header: Authorization: Bearer <token>
        body: {"folder": ...}
        200 -> {"success": true, "folder": ...}

    GET {base_url}/files/list_folders.php
        header: Authorization: Bearer <token>
        200 -> {"folders": ["saved", "temp", ...]}

Every call here can raise ApiError -- callers should catch it and show a
message box rather than letting the app crash if the server is unreachable
or the session expired.
"""

import requests


class ApiError(Exception):
    pass


class ApiClient:
    def __init__(self, base_url: str, token: str = None, timeout: int = 15):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def setup_account(self, username: str, password: str, storage_dir: str = None) -> str:
        """One-time account creation against a freshly-uploaded server/
        folder -- no login required (there's nothing to log into yet). The
        server refuses this once an account already exists, so it's safe
        to call speculatively; a 409 means someone already set this server
        up (possibly the user themself, previously)."""
        body = {"username": username, "password": password}
        if storage_dir:
            body["storage_dir"] = storage_dir

        try:
            resp = requests.post(
                f"{self.base_url}/setup.php",
                json=body,
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code == 409:
            raise ApiError("This server is already set up. Use Log in instead, or delete config.local.php on the server to reset it.")
        if resp.status_code != 200:
            try:
                message = resp.json().get("error")
            except ValueError:
                message = None
            raise ApiError(message or f"Setup failed ({resp.status_code}): {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiError("Server returned an unexpected (non-JSON) response") from e

        token = data.get("token")
        if not token:
            raise ApiError("Server response did not include a session token")

        self.token = token
        return token

    def login(self, username: str, password: str) -> str:
        try:
            resp = requests.post(
                f"{self.base_url}/login.php",
                json={"username": username, "password": password},
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code != 200:
            raise ApiError(f"Login failed ({resp.status_code}): {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiError("Server returned an unexpected (non-JSON) response") from e

        token = data.get("token")
        if not token:
            raise ApiError("Server response did not include a session token")

        self.token = token
        return token

    def save_file(self, filename: str, content: str, folder: str = "saved") -> dict:
        if not self.token:
            raise ApiError("Not logged in")

        try:
            resp = requests.post(
                f"{self.base_url}/files/save.php",
                json={"filename": filename, "content": content, "folder": folder},
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code == 401:
            raise ApiError("Session expired, please log in again")
        if resp.status_code != 200:
            raise ApiError(f"Save failed ({resp.status_code}): {resp.text[:200]}")

        try:
            return resp.json()
        except ValueError as e:
            raise ApiError("Server returned an unexpected (non-JSON) response") from e

    def list_files(self, folder: str = "saved") -> list:
        if not self.token:
            raise ApiError("Not logged in")

        try:
            resp = requests.get(
                f"{self.base_url}/files/list.php",
                params={"folder": folder},
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code == 401:
            raise ApiError("Session expired, please log in again")
        if resp.status_code != 200:
            raise ApiError(f"Could not list files ({resp.status_code}): {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiError("Server returned an unexpected (non-JSON) response") from e

        return data.get("files", [])

    def load_file(self, filename: str, folder: str = "saved") -> str:
        if not self.token:
            raise ApiError("Not logged in")

        try:
            resp = requests.get(
                f"{self.base_url}/files/load.php",
                params={"filename": filename, "folder": folder},
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code == 401:
            raise ApiError("Session expired, please log in again")
        if resp.status_code == 404:
            raise ApiError("File not found on server")
        if resp.status_code != 200:
            raise ApiError(f"Load failed ({resp.status_code}): {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiError("Server returned an unexpected (non-JSON) response") from e

        content = data.get("content")
        if content is None:
            raise ApiError("Server response did not include file content")
        return content

    def delete_file(self, filename: str, folder: str = "saved") -> None:
        if not self.token:
            raise ApiError("Not logged in")

        try:
            resp = requests.post(
                f"{self.base_url}/files/delete.php",
                json={"filename": filename, "folder": folder},
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code == 401:
            raise ApiError("Session expired, please log in again")
        if resp.status_code == 404:
            raise ApiError("File not found on server")
        if resp.status_code != 200:
            raise ApiError(f"Delete failed ({resp.status_code}): {resp.text[:200]}")

    def list_folders(self) -> list:
        if not self.token:
            raise ApiError("Not logged in")

        try:
            resp = requests.get(
                f"{self.base_url}/files/list_folders.php",
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code == 401:
            raise ApiError("Session expired, please log in again")
        if resp.status_code != 200:
            raise ApiError(f"Could not list folders ({resp.status_code}): {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiError("Server returned an unexpected (non-JSON) response") from e

        return data.get("folders", [])

    def create_folder(self, name: str) -> str:
        if not self.token:
            raise ApiError("Not logged in")

        try:
            resp = requests.post(
                f"{self.base_url}/files/create_folder.php",
                json={"folder": name},
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as e:
            raise ApiError(f"Could not reach server: {e}") from e

        if resp.status_code == 401:
            raise ApiError("Session expired, please log in again")
        if resp.status_code != 200:
            try:
                message = resp.json().get("error")
            except ValueError:
                message = None
            raise ApiError(message or f"Could not create folder ({resp.status_code}): {resp.text[:200]}")

        try:
            data = resp.json()
        except ValueError as e:
            raise ApiError("Server returned an unexpected (non-JSON) response") from e

        return data.get("folder", name)
