"""
Colored/named bookmark categories -- same design validated in the earlier
Notepad++ C++ prototype, ported to QScintilla:

- 6 fixed preset colors, each with a user-editable name (global setting,
  saved to config.json, not per-file).
- A line's bookmark marker is one of: no bookmark, plain bookmark, or one
  of the 6 colored categories.
- Assign a category by right-clicking a bookmark in the margin.
- Hovering a colored bookmark shows its category name as a tooltip.
"""

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDialogButtonBox, QFrame,
)

import config
import theme

CATEGORY_COUNT = 6
CATEGORY_NONE = -1

PRESET_COLORS = [
    QColor("#E74C3C"),  # Red
    QColor("#E67E22"),  # Orange
    QColor("#F1C40F"),  # Yellow
    QColor("#2ECC71"),  # Green
    QColor("#3498DB"),  # Blue
    QColor("#9B59B6"),  # Purple
]

DEFAULT_NAMES = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple"]

# QsciScintilla marker handles: 0 = plain bookmark (kept separate from the
# folder/line-number margins' own built-in markers), 1..6 = categories.
MARKER_PLAIN = 0
MARKER_CATEGORY_BASE = 1  # occupies 1..CATEGORY_COUNT


def marker_id_for(category_index: int) -> int:
    """category_index: CATEGORY_NONE for the plain bookmark, else 0..5."""
    if category_index == CATEGORY_NONE:
        return MARKER_PLAIN
    return MARKER_CATEGORY_BASE + category_index


class BookmarkCategoryStore:
    """Loads/saves the 6 category names. Colors are fixed presets (not
    user-editable), only the label attached to each color is."""

    def __init__(self):
        saved = config.load_json("bookmark_categories.json", None)
        if saved and isinstance(saved, list) and len(saved) == CATEGORY_COUNT:
            self.names = list(saved)
        else:
            self.names = list(DEFAULT_NAMES)

    def save(self) -> None:
        config.save_json("bookmark_categories.json", self.names)

    def name_for(self, category_index: int) -> str:
        if 0 <= category_index < CATEGORY_COUNT:
            return self.names[category_index]
        return ""


class BookmarkCategoriesDialog(QDialog):
    """Settings dialog: rename each of the 6 bookmark colors."""

    def __init__(self, store: BookmarkCategoryStore, parent=None, dark_theme: bool = False):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Bookmark Categories")
        self._edits = []
        theme.apply_dark_titlebar(self, dark_theme)

        layout = QVBoxLayout(self)

        hint = QLabel(
            "Name each of the 6 bookmark colors. Right-click a bookmark in "
            "the margin to assign one of these categories to it."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        for i in range(CATEGORY_COUNT):
            row = QHBoxLayout()

            swatch = QFrame()
            swatch.setFixedSize(18, 18)
            swatch.setFrameShape(QFrame.Box)
            color = PRESET_COLORS[i]
            swatch.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #666;"
            )
            row.addWidget(swatch)

            edit = QLineEdit(self.store.names[i])
            edit.setMaxLength(64)
            self._edits.append(edit)
            row.addWidget(edit)

            layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        for i, edit in enumerate(self._edits):
            text = edit.text().strip()
            self.store.names[i] = text if text else DEFAULT_NAMES[i]
        self.store.save()
        self.accept()
