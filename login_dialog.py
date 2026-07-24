"""
Login: asks for the server URL + credentials, then talks to the server for
that one session. The password itself is never stored -- only the session
token the server hands back, and only if "Remember me" is checked.

"Remember me" defaults to OFF: MyNote won't write anything to disk about
who's logged in unless the user explicitly opts in. That keeps a login done
on a shared/borrowed PC (or while testing a freshly built .exe) from quietly
leaving a working session behind for the next person to open the app. When
left unchecked, the token lives only in memory for the running session and
is gone the moment the app is closed.

Also offers "Create account", for a server/ folder that was just uploaded
and hasn't been set up yet -- this talks to server/setup.php instead of
login.php, so there's no need to open a browser or hand-edit any PHP files
first. It's a one-time operation server-side (setup.php refuses once an
account already exists), so it's safe to have this button always visible.
"""

from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QPushButton, QLabel,
    QMessageBox, QCheckBox,
)

import config
import theme
from api_client import ApiClient, ApiError

SESSION_FILE = "session.json"


def load_session():
    """Returns {"base_url":..., "token":...} or None if never logged in /
    logged out."""
    return config.load_json(SESSION_FILE, None)


def save_session(base_url: str, token: str):
    config.save_json(SESSION_FILE, {"base_url": base_url, "token": token})


def clear_session():
    config.save_json(SESSION_FILE, None)


class LoginDialog(QDialog):
    """On accept, self.client is a logged-in ApiClient and the session has
    already been persisted to disk."""

    def __init__(self, parent=None, default_base_url: str = "", dark_theme: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Log in")
        self.client = None
        self.setMinimumWidth(460)
        theme.apply_dark_titlebar(self, dark_theme)

        field_style = "padding: 6px 8px; font-size: 11pt;"

        layout = QFormLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setVerticalSpacing(16)
        layout.setHorizontalSpacing(16)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        label_style = "font-size: 11pt;"

        self.server_edit = QLineEdit(default_base_url)
        self.server_edit.setPlaceholderText("https://yourdomain.com/api")
        self.server_edit.setStyleSheet(field_style)
        self.server_edit.setMinimumHeight(32)
        server_label = QLabel("Server URL:")
        server_label.setStyleSheet(label_style)
        layout.addRow(server_label, self.server_edit)

        self.user_edit = QLineEdit()
        self.user_edit.setStyleSheet(field_style)
        self.user_edit.setMinimumHeight(32)
        user_label = QLabel("Username:")
        user_label.setStyleSheet(label_style)
        layout.addRow(user_label, self.user_edit)

        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setStyleSheet(field_style)
        self.pass_edit.setMinimumHeight(32)
        pass_label = QLabel("Password:")
        pass_label.setStyleSheet(label_style)
        layout.addRow(pass_label, self.pass_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.Password)
        self.confirm_edit.setStyleSheet(field_style)
        self.confirm_edit.setMinimumHeight(32)
        confirm_label = QLabel("Confirm password:")
        confirm_label.setStyleSheet(label_style)
        layout.addRow(confirm_label, self.confirm_edit)

        hint = QLabel("Confirm password is only needed for Create Account (first-time server setup).")
        hint.setStyleSheet("color: #808080; font-size: 9pt;")
        hint.setWordWrap(True)
        layout.addRow(hint)

        self.remember_checkbox = QCheckBox("Remember me on this device")
        self.remember_checkbox.setStyleSheet(label_style)
        remember_hint = QLabel(
            "Off by default. When off, you'll need to log in again next time "
            "you open MyNote -- nothing about this login is written to disk."
        )
        remember_hint.setStyleSheet("color: #808080; font-size: 9pt;")
        remember_hint.setWordWrap(True)
        layout.addRow(self.remember_checkbox)
        layout.addRow(remember_hint)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #B00020; font-size: 10pt;")
        self.status_label.setWordWrap(True)
        layout.addRow(self.status_label)

        button_row = QDialogButtonBox()
        self.create_account_button = QPushButton("Create Account")
        self.create_account_button.setMinimumSize(130, 32)
        self.create_account_button.clicked.connect(self._on_create_account)
        button_row.addButton(self.create_account_button, QDialogButtonBox.ActionRole)

        self.login_button = QPushButton("Log In")
        self.login_button.setMinimumSize(90, 32)
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self._on_login)
        button_row.addButton(self.login_button, QDialogButtonBox.AcceptRole)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumSize(90, 32)
        self.cancel_button.clicked.connect(self.reject)
        button_row.addButton(self.cancel_button, QDialogButtonBox.RejectRole)

        layout.addRow(button_row)

    def _collect_fields(self):
        base_url = self.server_edit.text().strip()
        username = self.user_edit.text().strip()
        password = self.pass_edit.text()
        return base_url, username, password

    def _on_login(self):
        base_url, username, password = self._collect_fields()

        if not base_url or not username or not password:
            self.status_label.setText("Server URL, username and password are all required.")
            return

        client = ApiClient(base_url)
        try:
            token = client.login(username, password)
        except ApiError as e:
            self.status_label.setText(str(e))
            return

        if self.remember_checkbox.isChecked():
            save_session(base_url, token)
        else:
            clear_session()  # wipe any session saved from a previous "remember me" login
        self.client = client
        self.accept()

    def _on_create_account(self):
        base_url, username, password = self._collect_fields()
        confirm_password = self.confirm_edit.text()

        if not base_url or not username or not password:
            self.status_label.setText("Server URL, username and password are all required.")
            return
        if password != confirm_password:
            self.status_label.setText("Password and confirm password don't match.")
            return
        if len(password) < 8:
            self.status_label.setText("Password must be at least 8 characters.")
            return

        client = ApiClient(base_url)
        try:
            token = client.setup_account(username, password)
        except ApiError as e:
            self.status_label.setText(str(e))
            return

        if self.remember_checkbox.isChecked():
            save_session(base_url, token)
        else:
            clear_session()
        self.client = client
        self.status_label.setStyleSheet("color: #2e7d32; font-size: 10pt;")
        self.status_label.setText("Account created and logged in.")
        self.accept()


def try_restore_client() -> ApiClient:
    """Returns an ApiClient from the saved session, or None if not logged in."""
    session = load_session()
    if not session or not session.get("token"):
        return None
    return ApiClient(session["base_url"], session["token"])
