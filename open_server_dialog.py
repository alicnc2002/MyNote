"""
Open-from-server dialog: browse folders on the server, open a file into a
new tab, delete a file you no longer need, or create a new folder to keep
things organized. "temp" (background autosave snapshots) is deliberately
left out of the folder picker -- those are recovery snapshots, not files
someone would deliberately browse and reopen.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel, QMessageBox, QComboBox, QPushButton,
    QInputDialog,
)

import theme
from api_client import ApiClient, ApiError

# Folders the app manages internally and never shows for browsing/organizing.
HIDDEN_FOLDERS = {"temp"}


class OpenFromServerDialog(QDialog):
    """After exec_() == QDialog.Accepted, self.selected_filename and
    self.selected_folder identify the file to load (fetch its content
    separately via ApiClient.load_file)."""

    def __init__(self, parent, client: ApiClient, folder: str = "saved", dark_theme: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Open from Server")
        self.resize(460, 420)
        theme.apply_dark_titlebar(self, dark_theme)
        self.client = client
        self.folder = folder
        self.selected_filename = None
        self.selected_folder = None

        layout = QVBoxLayout(self)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Folder:"))
        self.folder_combo = QComboBox()
        self.folder_combo.currentIndexChanged.connect(self._on_folder_changed)
        folder_row.addWidget(self.folder_combo, stretch=1)
        self.new_folder_button = QPushButton("New Folder...")
        self.new_folder_button.clicked.connect(self._on_new_folder)
        folder_row.addWidget(self.new_folder_button)
        layout.addLayout(folder_row)

        layout.addWidget(QLabel("Files saved to your server:"))

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_accept)
        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Open | QDialogButtonBox.Cancel)
        self.delete_button = QPushButton("Delete")
        buttons.addButton(self.delete_button, QDialogButtonBox.DestructiveRole)
        self.delete_button.clicked.connect(self._on_delete)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_folders()

    # ---- folders ---------------------------------------------------------

    def _load_folders(self):
        try:
            folders = self.client.list_folders()
        except ApiError as e:
            QMessageBox.critical(self, "Could not list folders", str(e))
            folders = [self.folder]

        folders = [f for f in folders if f not in HIDDEN_FOLDERS]
        if self.folder not in folders:
            folders.insert(0, self.folder)

        self.folder_combo.blockSignals(True)
        self.folder_combo.clear()
        self.folder_combo.addItems(folders)
        index = self.folder_combo.findText(self.folder)
        if index >= 0:
            self.folder_combo.setCurrentIndex(index)
        self.folder_combo.blockSignals(False)

        self._load_list()

    def _on_folder_changed(self, _index):
        self.folder = self.folder_combo.currentText()
        self._load_list()

    def _on_new_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        try:
            created = self.client.create_folder(name)
        except ApiError as e:
            QMessageBox.critical(self, "Could not create folder", str(e))
            return
        self.folder = created
        self._load_folders()

    # ---- files -------------------------------------------------------------

    def _load_list(self):
        self.list_widget.clear()
        try:
            files = self.client.list_files(self.folder)
        except ApiError as e:
            QMessageBox.critical(self, "Could not list files", str(e))
            files = []

        if not files:
            placeholder = QListWidgetItem("(no files saved yet)")
            placeholder.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(placeholder)
            return

        for entry in files:
            name = entry.get("filename", "")
            modified = entry.get("modified", "")
            size = entry.get("size")
            details = f"  ({modified}" + (f", {size} bytes)" if size is not None else ")")
            item = QListWidgetItem(name + details)
            item.setData(Qt.UserRole, name)
            self.list_widget.addItem(item)

        self.list_widget.setCurrentRow(0)

    def _on_delete(self):
        item = self.list_widget.currentItem()
        if item is None or item.data(Qt.UserRole) is None:
            return
        name = item.data(Qt.UserRole)

        reply = QMessageBox.question(
            self, "Delete file",
            f'Delete "{name}" from the server? This can\'t be undone.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self.client.delete_file(name, self.folder)
        except ApiError as e:
            QMessageBox.critical(self, "Delete failed", str(e))
            return

        self._load_list()

    def _on_accept(self):
        item = self.list_widget.currentItem()
        if item is None or item.data(Qt.UserRole) is None:
            return
        self.selected_filename = item.data(Qt.UserRole)
        self.selected_folder = self.folder
        self.accept()
