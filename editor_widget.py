"""
CodeEditor: a QsciScintilla widget configured to behave like a Notepad++ tab
-- line numbers, a bookmark margin (6 colored categories), folding,
Ctrl+MouseWheel zoom, and NPP-like coloring for whichever lexer applies to
the open file (Python / HTML / PHP / plain text).
"""

import os

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QMenu, QToolTip, QAction, QFrame
from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciLexerHTML

import theme
import bookmark_categories as bmcat
import bookmark_store

MARGIN_LINE_NUMBERS = 0
MARGIN_SYMBOLS = 1
MARGIN_FOLD = 2

SYMBOL_MARGIN_WIDTH = 16
FOLD_MARGIN_WIDTH = 14


def lexer_for_path(path: str):
    """Returns a configured QsciLexer for the file's extension, or None for
    plain text (no highlighting -- exactly what "plain text" should look
    like)."""
    ext = os.path.splitext(path)[1].lower() if path else ""

    if ext == ".py":
        return QsciLexerPython()
    if ext in (".html", ".htm", ".php"):
        # Scintilla's HTML lexer (which QsciLexerHTML wraps) natively
        # highlights embedded PHP/JS blocks inside HTML, so it doubles as
        # our PHP lexer -- this is the standard QScintilla approach since
        # there's no separate free-standing PHP-only lexer class.
        lexer = QsciLexerHTML()
        return lexer
    return None  # plain text


class CodeEditor(QsciScintilla):
    def __init__(self, theme_name: str, category_store: bmcat.BookmarkCategoryStore, parent=None):
        super().__init__(parent)
        self.file_path = None
        self.server_origin = None  # {"folder": ..., "filename": ...} when opened/saved to server
        self.theme_name = theme_name
        self.category_store = category_store

        # Where this file's bookmarks are persisted -- a bookmark_store
        # LocalLocation/ServerLocation plus the key identifying this file
        # within it. Both None until the buffer has a real home (a local
        # path or a server save), so a brand-new Untitled tab's bookmarks
        # simply aren't persisted until it's saved somewhere. See
        # bookmark_store.py: bookmarks live alongside the file itself
        # (same folder locally, same server folder remotely) so they
        # follow the file across machines.
        self.bookmark_location = None
        self.bookmark_entry_key = None

        # QsciScintilla inherits QFrame, which by default draws a sunken
        # panel border around the whole widget using the OS palette's
        # "mid"/"dark" shading -- unrelated to anything theme.py colors, so
        # it stayed the light-theme gray no matter what theme was active.
        # Against a dark editor background that showed up as a bright thin
        # line down the left edge (and top/right/bottom, less noticeably).
        # Dropping the frame entirely removes it for every theme. Belt and
        # suspenders: also override via QSS directly on the widget (in case
        # the app-wide stylesheet cascades an unexpected border here) and
        # zero out Scintilla's own left/right "margin" -- the small strip of
        # blank space it pads in before margin 0 and after the text, which
        # is separate from the numbered margins and isn't governed by
        # SCI_SETMARGINBACKN at all, so it stayed uncolored no matter what
        # theme was active.
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("border: none; outline: none;")

        # Font must be set before we compute the line-number margin's pixel
        # width below, otherwise the width is based on whatever placeholder
        # font QsciScintilla starts with and ends up wrong once we switch to
        # our editor font.
        self.setFont(theme.editor_font())

        self.setUtf8(True)
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)
        self.setAutoIndent(True)
        self.setMouseTracking(True)

        self._setup_margins()
        self._setup_markers()
        self._setup_folding()

        self.marginClicked.connect(self._on_margin_clicked)
        self.linesChanged.connect(self._update_line_number_margin_width)

        theme.apply_theme_to_editor(self, self.theme_name)
        self._update_line_number_margin_width()

    # ---- setup helpers -------------------------------------------------

    def _setup_margins(self):
        self.setMarginType(MARGIN_LINE_NUMBERS, QsciScintilla.NumberMargin)
        self.setMarginLineNumbers(MARGIN_LINE_NUMBERS, True)
        # Width is set dynamically -- see _update_line_number_margin_width()
        # (matches NPP's "line number dynamic width" behavior: the margin
        # grows as the file gains more digits in its line count).

        self.setMarginType(MARGIN_SYMBOLS, QsciScintilla.SymbolMargin)
        self.setMarginWidth(MARGIN_SYMBOLS, SYMBOL_MARGIN_WIDTH)
        self.setMarginSensitivity(MARGIN_SYMBOLS, True)
        self.setMarginMarkerMask(MARGIN_SYMBOLS, (1 << 24) - 1)

        # Scintilla pads a couple of extra pixels of blank space before
        # margin 0 and after the text edge -- separate from any of the
        # numbered margins above, and not colored by SCI_SETMARGINBACKN, so
        # it showed up as a thin uncolored (light) sliver down the left
        # edge in dark themes no matter how the real margins were colored.
        # Zeroing both removes that gap entirely.
        # Looked up by number with a fallback in case this QScintilla
        # binding doesn't expose the constant by name -- 2154/2155 are
        # SCI_SETMARGINLEFT/SCI_SETMARGINRIGHT per Scintilla.iface.
        self.SendScintilla(getattr(QsciScintilla, "SCI_SETMARGINLEFT", 2154), 0)
        self.SendScintilla(getattr(QsciScintilla, "SCI_SETMARGINRIGHT", 2155), 0)

    def _setup_folding(self):
        self.setFolding(QsciScintilla.BoxedTreeFoldStyle, MARGIN_FOLD)
        self.setMarginWidth(MARGIN_FOLD, FOLD_MARGIN_WIDTH)

    def _update_line_number_margin_width(self):
        """Sizes margin 0 to fit the current line count exactly (plus a
        little padding), the same "grows as your file gets longer" behavior
        Notepad++ uses -- rather than a fixed guess at how many digits a
        file might need."""
        digits = max(3, len(str(self.lines())))
        width = QFontMetrics(self.font()).horizontalAdvance("0" * digits) + 12
        self.setMarginWidth(MARGIN_LINE_NUMBERS, width)

    def _setup_markers(self):
        for i, color in enumerate(bmcat.PRESET_COLORS):
            marker_id = bmcat.marker_id_for(i)
            self.markerDefine(QsciScintilla.Circle, marker_id)
            self.setMarkerBackgroundColor(color, marker_id)

    # ---- lexer / theme ---------------------------------------------------

    def load_lexer_for(self, path: str):
        lexer = lexer_for_path(path)
        if lexer is not None:
            theme.apply_theme_to_lexer(lexer, self.theme_name)
        self.setLexer(lexer)

    def apply_theme(self, theme_name: str):
        self.theme_name = theme_name
        theme.apply_theme_to_editor(self, theme_name)
        lexer = self.lexer()
        if lexer is not None:
            theme.apply_theme_to_lexer(lexer, theme_name)
            self.setLexer(None)
            self.setLexer(lexer)  # force restyle
        self._update_line_number_margin_width()

    # ---- bookmark categories --------------------------------------------

    def category_at_line(self, line: int) -> int:
        mask = self.markersAtLine(line)
        if mask <= 0:
            return bmcat.CATEGORY_NONE
        for i in range(bmcat.CATEGORY_COUNT):
            if mask & (1 << bmcat.marker_id_for(i)):
                return i
        return bmcat.CATEGORY_NONE

    def has_any_bookmark(self, line: int) -> bool:
        return self.category_at_line(line) != bmcat.CATEGORY_NONE

    def set_line_category(self, line: int, category_index):
        """category_index: 0..5 to set a color, or None to remove the
        bookmark entirely."""
        for i in range(bmcat.CATEGORY_COUNT):
            self.markerDelete(line, bmcat.marker_id_for(i))

        if category_index is not None:
            self.markerAdd(line, bmcat.marker_id_for(category_index))

        self._persist_bookmarks()

    # ---- bookmark persistence (survives close/reopen) ---------------------
    # QScintilla markers only live in memory, so without this a file's
    # bookmarks would silently vanish the moment its tab is closed or the
    # file is reopened. See bookmark_store.py for the on-disk format.

    def export_bookmarks(self) -> dict:
        """{line_number: category_index} for every currently bookmarked
        line."""
        result = {}
        for line in range(self.lines()):
            cat = self.category_at_line(line)
            if cat != bmcat.CATEGORY_NONE:
                result[line] = cat
        return result

    def _persist_bookmarks(self):
        if self.bookmark_location and self.bookmark_entry_key:
            bookmark_store.save_bookmarks(self.bookmark_location, self.bookmark_entry_key, self.export_bookmarks())

    def _load_bookmarks_from_store(self):
        if not (self.bookmark_location and self.bookmark_entry_key):
            return
        bookmarks = bookmark_store.load_bookmarks(self.bookmark_location, self.bookmark_entry_key)
        for line, cat in bookmarks.items():
            if 0 <= line < self.lines():
                self.markerAdd(line, bmcat.marker_id_for(cat))

    def bind_bookmark_location(self, location, entry_key: str):
        """Call when a file is opened (local or from the server) -- attaches
        this editor to where that file's bookmarks live and restores any
        found there. Does not persist anything new."""
        self.bookmark_location = location
        self.bookmark_entry_key = entry_key
        self._load_bookmarks_from_store()

    def rekey_bookmark_location(self, new_location, new_entry_key: str):
        """Call after a save completes (first local save, Save As, or
        save-to-server) -- migrates any bookmarks saved under this editor's
        previous location/key to the new one, and persists the current
        state there."""
        old_location, old_entry_key = self.bookmark_location, self.bookmark_entry_key
        bookmark_store.rekey(old_location, old_entry_key, new_location, new_entry_key)
        self.bookmark_location = new_location
        self.bookmark_entry_key = new_entry_key
        self._persist_bookmarks()

    # ---- margin interaction ----------------------------------------------
    # Every click (left or right) on the bookmark margin opens the same
    # color-picker menu, so choosing which of the 6 colors to use is always
    # one click away -- rather than always placing a fixed default color
    # and requiring a second, less discoverable right-click to recolor it.

    def _on_margin_clicked(self, margin, line, state):
        if margin != MARGIN_SYMBOLS:
            return
        self._show_category_menu(line)

    def _margin_symbols_x_range(self):
        x0 = self.marginWidth(MARGIN_LINE_NUMBERS)
        x1 = x0 + self.marginWidth(MARGIN_SYMBOLS)
        return x0, x1

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            x0, x1 = self._margin_symbols_x_range()
            if x0 <= event.x() < x1:
                line = self.lineAt(event.pos())
                if line >= 0:
                    self._show_category_menu(line, event.globalPos())
                    return
        super().mousePressEvent(event)

    def _show_category_menu(self, line: int, global_pos=None):
        if global_pos is None:
            from PyQt5.QtGui import QCursor
            global_pos = QCursor.pos()

        menu = QMenu(self)
        current = self.category_at_line(line)

        for i in range(bmcat.CATEGORY_COUNT):
            label = self.category_store.name_for(i)
            action = QAction(label, self, checkable=True)
            action.setChecked(current == i)
            action.triggered.connect(lambda checked, idx=i, ln=line: self.set_line_category(ln, idx))
            menu.addAction(action)

        if current != bmcat.CATEGORY_NONE:
            menu.addSeparator()
            remove_action = QAction("Remove bookmark", self)
            remove_action.triggered.connect(lambda checked, ln=line: self.set_line_category(ln, None))
            menu.addAction(remove_action)

        menu.exec_(global_pos)

    # ---- hover tooltip on colored bookmarks -------------------------------

    def event(self, e):
        if e.type() == QEvent.ToolTip:
            x0, x1 = self._margin_symbols_x_range()
            if x0 <= e.pos().x() < x1:
                line = self.lineAt(e.pos())
                if line >= 0:
                    cat = self.category_at_line(line)
                    if cat != bmcat.CATEGORY_NONE:
                        QToolTip.showText(e.globalPos(), self.category_store.name_for(cat), self)
                        return True
            QToolTip.hideText()
        return super().event(e)

    # ---- zoom --------------------------------------------------------------

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoomIn()
            elif delta < 0:
                self.zoomOut()
            event.accept()
            return
        super().wheelEvent(event)
