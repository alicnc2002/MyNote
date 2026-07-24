"""
Save destination dialog: "Save to Server" (default filename = current
date+time) or "Save Locally" (regular file-system save, handled by the
caller via QFileDialog as usual).
"""

from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, QLineEdit,
    QDialogButtonBox, QLabel, QButtonGroup,
)

import theme

SAVE_TO_SERVER = "server"
SAVE_LOCALLY = "local"


def default_server_filename(extension: str = ".txt") -> str:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"{stamp}{extension}"


class SaveDestinationDialog(QDialog):
    """After exec_() == QDialog.Accepted:
    - self.destination is SAVE_TO_SERVER or SAVE_LOCALLY
    - self.server_filename is only meaningful when destination == SAVE_TO_SERVER
    """

    def __init__(self, parent=None, suggested_extension: str = ".txt", server_available: bool = True,
                 dark_theme: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Save")
        self.destination = None
        self.server_filename = None
        theme.apply_dark_titlebar(self, dark_theme)

        # Wider than the original (so the filename field isn't cramped), but
        # sized to fit its content rather than a forced tall minimum height,
        # which just left a dead empty gap above the buttons.
        self.setMinimumWidth(480)

        radio_style = "font-size: 12pt; padding: 4px 0;"
        field_style = "padding: 8px 10px; font-size: 12pt;"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        self.group = QButtonGroup(self)

        self.server_radio = QRadioButton("Save to server")
        self.server_radio.setStyleSheet(radio_style)
        self.server_radio.setEnabled(server_available)
        self.group.addButton(self.server_radio)
        layout.addWidget(self.server_radio)

        name_row = QHBoxLayout()
        name_row.setSpacing(10)
        name_row.addSpacing(24)
        name_label = QLabel("Name:")
        name_label.setStyleSheet("font-size: 12pt;")
        name_row.addWidget(name_label)
        self.name_edit = QLineEdit(default_server_filename(suggested_extension))
        self.name_edit.setStyleSheet(field_style)
        self.name_edit.setMinimumHeight(36)
        self.name_edit.setEnabled(server_available)
        name_row.addWidget(self.name_edit, stretch=1)
        layout.addLayout(name_row)

        self.local_radio = QRadioButton("Save locally")
        self.local_radio.setStyleSheet(radio_style)
        self.group.addButton(self.local_radio)
        layout.addWidget(self.local_radio)

        if server_available:
            self.server_radio.setChecked(True)
        else:
            self.local_radio.setChecked(True)
            note = QLabel("(Log in from Settings to enable server save.)")
            note.setStyleSheet("color: #808080; font-size: 10pt;")
            layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setMinimumSize(90, 34)
        buttons.button(QDialogButtonBox.Cancel).setMinimumSize(90, 34)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if self.server_radio.isChecked():
            self.destination = SAVE_TO_SERVER
            self.server_filename = self.name_edit.text().strip() or default_server_filename()
        else:
            self.destination = SAVE_LOCALLY
        self.accept()
