"""
MyNote -- a small Notepad++-alike built on PyQt5 + QScintilla.

Run with:  python main.py [file ...]

Features:
- Multi-tab editing with syntax highlighting for Python / HTML / PHP / plain text
- Ctrl+MouseWheel zoom
- Notepad++-style color theme (Light / Dark / Nord, View > Theme)
- Colored/named bookmark categories (Settings > Bookmark Categories...)
- One-time login + save-to-server / save-locally, with a background
  temp-folder auto-sync for unsaved changes (Settings > Log in...)
"""

import os
import re
import sys
import uuid

from PyQt5.QtCore import Qt, QTimer, QSize, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QFileDialog, QMessageBox,
    QAction, QActionGroup, QMenuBar, QStatusBar, QToolBar, QLabel,
    QDialog, QVBoxLayout, QTextEdit, QPushButton,
)

import config
import theme
import bookmark_categories as bmcat
import bookmark_store
from editor_widget import CodeEditor
from login_dialog import LoginDialog, try_restore_client, clear_session, load_session
from save_dialog import SaveDestinationDialog, SAVE_TO_SERVER, SAVE_LOCALLY
from open_server_dialog import OpenFromServerDialog
from api_client import ApiError

AUTOSAVE_INTERVAL_MS = 2 * 60 * 1000  # push unsaved changes to server temp folder every 2 minutes

APP_VERSION = "1.4.0"

PROJECT_URL = "https://github.com/alicnc2002/MyNote"

HELP_TEXT = """\
MyNote -- How to Use

BASICS
- File > New Tab / Open / Save / Save As, same as any text editor. Each
  open file gets its own tab; unsaved tabs show a dot next to their name.
- Ctrl+MouseWheel zooms the editor in/out.
- Click in the thin margin just left of the text (the bookmark margin) to
  color-tag a line. Right-click there too. Manage the category names and
  colors under Settings > Bookmark Categories...
- The small triangle in the leftmost margin folds/unfolds code blocks.
- View > Theme switches between Light, Dark, and Nord. Your choice is
  remembered for next time.

SETTING UP YOUR OWN SERVER
MyNote can optionally save your files to a personal server instead of
(or alongside) your own computer, so the same files and bookmarks follow
you across machines.

1. Host the PHP files in this project's server/ folder on any PHP 7.4+
   web host (shared hosting like cPanel works fine). See server/README.md
   in this repo for the full step-by-step guide, including the required
   folder permissions and the one-time config.local.php secret key setup.
2. In MyNote, go to Settings > Log in..., enter your server's address,
   and either log in with an account the host admin already created, or
   use "Create Account" if the server allows self-service signup
   (setup.php).
3. Once logged in, File > Save to Server / Open from Server become
   available, and unsaved changes are quietly auto-synced to a temp
   folder on the server every couple of minutes as a safety net.
4. "Remember me on this device" on the login screen controls whether your
   session is kept signed in after you close MyNote -- leave it unchecked
   on a shared/public computer.

You don't need a server at all to use MyNote locally -- it's entirely
optional.

More info and updates: {url}
""".format(url=PROJECT_URL)

CHANGELOG_TEXT = """\
MyNote Change Log

1.4.0
- Added a "How to Use" entry to the Help menu covering basic editor
  operation and how to set up a personal server.
- About MyNote now links to the project's GitHub page.
- Fixed the Nord theme's menu bar/toolbar being the exact same color as
  the editor background (they blended together with no visible border).

1.3.0
- Added a Nord theme (View > Theme > Nord), alongside Light and Dark.
- Open from Server now has a folder picker, a "New Folder..." button to
  organize saved files, and a Delete button to remove files you no longer
  need straight from that dialog.
- Fixed a bright white line running down the fold margin in dark themes
  (the fold-tree connector lines were using a hardcoded default color
  instead of the theme's colors).

1.2.0
- Renamed the app from PyNotepad to MyNote.
- Fixed a bright, uncolored vertical line that showed up in the bookmark
  margin in dark theme (the margin's background wasn't repainting
  correctly).

1.1.0
- Added a "Remember me on this device" checkbox to the login dialog
  (off by default -- the session token is only saved to disk if you opt in).
- Added this Help menu, with About and Change Log.

1.0.0
- Core editor: multi-tab editing with syntax highlighting for
  Python / HTML / PHP / plain text, Ctrl+MouseWheel zoom, Notepad++-style
  color theme with a dark mode toggle.
- Colored, named bookmark categories (Settings > Bookmark Categories...).
- Server account system: log in once, then Save to Server / Save Locally,
  Open from Server, and a background auto-sync of unsaved changes to a
  temp folder on the server.
- Self-service account setup: a "Create Account" button in the login
  dialog (and a matching setup.php wizard page) so a freshly uploaded
  server doesn't need any manual password hashing or file editing.
- Bookmarks follow the file, not the device: bookmarks are stored in a
  bookmarks.json sidecar next to the file itself (locally or on the
  server), tagged with a signature key so PyNotepad never overwrites an
  unrelated file of the same name. Opening the same file from a different
  computer or from the server shows the same bookmarks.
- Save As now offers real file-type filters (Python, HTML, PHP, Text,
  JavaScript, CSS, JSON, XML, Markdown, All Files) instead of only
  "All Files", so files get sensible extensions by default.
- UI polish: larger Login and Save dialogs, a "Larger Icons (1.5x)"
  toolbar option, a separate light-toolbar icon set for contrast in
  light mode, a custom app icon, and a fix so every dialog (not just the
  main window) follows the dark title bar setting.
- Packaged as a standalone Windows .exe (build.bat) with an optional
  code-signing script (sign.bat) for a self-signed certificate.
"""

if getattr(sys, "frozen", False):
    # Running from a PyInstaller-built .exe: bundled data (see build.bat's
    # --add-data) is unpacked next to sys._MEIPASS, not next to this .py file.
    _APP_DIR = sys._MEIPASS
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(_APP_DIR, "icons")
APP_ICON_PATH = os.path.join(ICONS_DIR, "app_icon.ico")

TOOLBAR_ICON_SIZE_NORMAL = 18
TOOLBAR_ICON_SIZE_LARGE = 27  # 1.5x

# Save As file-type filters -- without these, QFileDialog defaults to "All
# Files" only, which is how files with no extension at all kept getting
# created. Capped at 10 entries (including the "All Files" catch-all) and
# chosen for what this app actually does: the three languages it highlights,
# plain text, and a handful of other everyday text formats people editing
# code/config also tend to save.
SAVE_AS_FILTERS = (
    "Python Files (*.py);;"
    "HTML Files (*.html *.htm);;"
    "PHP Files (*.php);;"
    "Text Files (*.txt);;"
    "JavaScript Files (*.js);;"
    "CSS Files (*.css);;"
    "JSON Files (*.json);;"
    "XML Files (*.xml);;"
    "Markdown Files (*.md);;"
    "All Files (*)"
)


def _filter_for_extension(ext: str) -> str:
    """Picks the SAVE_AS_FILTERS entry matching an extension (e.g. ".py"),
    so Save As pre-selects the right file type for files that already have
    one. Falls back to the first (Python) filter if there's no match --
    QFileDialog needs *some* initial filter string."""
    ext = ext.lower()
    for part in SAVE_AS_FILTERS.split(";;"):
        patterns = [p.lower() for p in re.findall(r"\*(\.[A-Za-z0-9]+)", part)]
        if ext in patterns:
            return part
    return SAVE_AS_FILTERS.split(";;")[0]


def _extension_from_filter(filter_str: str) -> str:
    """Pulls the first "*.ext" pattern out of a filter string like
    "HTML Files (*.html *.htm)" -> ".html". Returns "" for "All Files (*)"
    or anything unrecognized, meaning: don't force an extension."""
    match = re.search(r"\(\*(\.[A-Za-z0-9]+)", filter_str)
    return match.group(1) if match else ""


def _icon(name: str, dark_theme: bool) -> QIcon:
    # The NPP dark-toolbar icon set (near-white glyphs) only reads clearly
    # against a dark toolbar -- on the light theme they're nearly invisible,
    # hence a separate light-toolbar icon set (dark glyphs) for contrast.
    subdir = "dark" if dark_theme else "light"
    path = os.path.join(ICONS_DIR, subdir, f"{name}.ico")
    if not os.path.isfile(path):
        path = os.path.join(ICONS_DIR, f"{name}.ico")  # fallback to the flat legacy set
    return QIcon(path) if os.path.isfile(path) else QIcon()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyNote")
        self.resize(1100, 750)

        prefs = config.load_json("prefs.json", {})
        self.theme_name = prefs.get("theme")
        if self.theme_name not in theme.THEME_NAMES:
            # Migrate from the old boolean "dark_theme" pref, or default to light.
            self.theme_name = "dark" if prefs.get("dark_theme") else "light"
        self.large_icons = bool(prefs.get("large_icons", False))
        theme.apply_app_theme(self.theme_name)  # theme the window chrome, not just the editor

        if os.path.isfile(APP_ICON_PATH):
            self.setWindowIcon(QIcon(APP_ICON_PATH))

        self.category_store = bmcat.BookmarkCategoryStore()
        self.api_client = try_restore_client()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.setCentralWidget(self.tabs)

        self._build_status_bar()
        self._build_menu()
        self._build_toolbar()

        self.tabs.currentChanged.connect(self._on_current_tab_changed)
        self._new_tab()

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave_to_server)
        self.autosave_timer.start(AUTOSAVE_INTERVAL_MS)

        theme.apply_dark_titlebar(self, self.is_dark)

    @property
    def is_dark(self) -> bool:
        """Whether the native title bar / icon set should read as "dark" --
        true for every theme except "light"."""
        return theme.is_dark_theme(self.theme_name)

    # ---- menu -----------------------------------------------------------

    def _build_menu(self):
        menubar: QMenuBar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        self._add_action(file_menu, "&New", "Ctrl+N", self._new_tab)
        self._add_action(file_menu, "&Open...", "Ctrl+O", self._open_file)
        self._add_action(file_menu, "Open from &Server...", "Ctrl+Shift+O", self._open_from_server)
        self._add_action(file_menu, "&Save", "Ctrl+S", self._save_current)
        self._add_action(file_menu, "Save &As...", "Ctrl+Shift+S", self._save_current_as)
        file_menu.addSeparator()
        self._add_action(file_menu, "E&xit", "Ctrl+Q", self.close)

        view_menu = menubar.addMenu("&View")
        self._add_action(view_menu, "Zoom In", "Ctrl+=", lambda: self._current_editor().zoomIn())
        self._add_action(view_menu, "Zoom Out", "Ctrl+-", lambda: self._current_editor().zoomOut())
        self._add_action(view_menu, "Reset Zoom", "Ctrl+0", lambda: self._current_editor().zoomTo(0))
        view_menu.addSeparator()
        theme_menu = view_menu.addMenu("Theme")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        self.theme_actions = {}
        for name in theme.THEME_NAMES:
            action = QAction(theme.THEME_LABELS[name], self, checkable=True)
            action.setChecked(self.theme_name == name)
            action.triggered.connect(lambda checked, n=name: self._set_theme(n))
            theme_group.addAction(action)
            theme_menu.addAction(action)
            self.theme_actions[name] = action

        self.large_icons_action = QAction("Larger Icons (1.5x)", self, checkable=True)
        self.large_icons_action.setChecked(self.large_icons)
        self.large_icons_action.triggered.connect(self._toggle_large_icons)
        view_menu.addAction(self.large_icons_action)

        settings_menu = menubar.addMenu("&Settings")
        self._add_action(settings_menu, "&Bookmark Categories...", "", self._open_bookmark_categories)
        settings_menu.addSeparator()
        self.login_action = self._add_action(settings_menu, "&Log in...", "", self._open_login)
        self.logout_action = self._add_action(settings_menu, "Log &out", "", self._logout)
        self._refresh_login_menu_state()

        help_menu = menubar.addMenu("&Help")
        self._add_action(help_menu, "&How to Use...", "", self._open_help)
        help_menu.addSeparator()
        self._add_action(help_menu, "&Change Log...", "", self._open_changelog)
        help_menu.addSeparator()
        self._add_action(help_menu, "&About MyNote", "", self._open_about)

    def _add_action(self, menu, text, shortcut, slot):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _refresh_login_menu_state(self):
        logged_in = self.api_client is not None
        self.login_action.setEnabled(not logged_in)
        self.logout_action.setEnabled(logged_in)

    def _build_toolbar(self):
        self.toolbar = QToolBar("Main")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        self._toolbar_icon_actions = []  # [(action, icon_name), ...] -- reapplied on theme/size change

        def add(icon_name, text, slot, tip=None):
            action = QAction(_icon(icon_name, self.is_dark), text, self)
            action.setToolTip(tip or text)
            action.triggered.connect(slot)
            self.toolbar.addAction(action)
            self._toolbar_icon_actions.append((action, icon_name))
            return action

        add("new_off", "New", self._new_tab)
        add("open_off", "Open", self._open_file)
        add("open_server_off", "Open from Server", self._open_from_server, tip="Open from Server (Ctrl+Shift+O)")
        add("save_off", "Save", self._save_current)
        add("saveall_off", "Save All", self._save_all)
        self.toolbar.addSeparator()
        add("cut_off", "Cut", lambda: self._current_editor().cut())
        add("copy_off", "Copy", lambda: self._current_editor().copy())
        add("paste_off", "Paste", lambda: self._current_editor().paste())
        self.toolbar.addSeparator()
        add("undo_off", "Undo", lambda: self._current_editor().undo())
        add("redo_off", "Redo", lambda: self._current_editor().redo())
        self.toolbar.addSeparator()
        add("zoomIn_off", "Zoom In", lambda: self._current_editor().zoomIn())
        add("zoomOut_off", "Zoom Out", lambda: self._current_editor().zoomOut())

        self._apply_toolbar_icon_size()

    def _apply_toolbar_icon_size(self):
        size = TOOLBAR_ICON_SIZE_LARGE if self.large_icons else TOOLBAR_ICON_SIZE_NORMAL
        self.toolbar.setIconSize(QSize(size, size))

    def _refresh_toolbar_icons(self):
        for action, icon_name in self._toolbar_icon_actions:
            action.setIcon(_icon(icon_name, self.is_dark))

    def _toggle_large_icons(self):
        self.large_icons = self.large_icons_action.isChecked()
        self._apply_toolbar_icon_size()
        config.save_json("prefs.json", {"theme": self.theme_name, "large_icons": self.large_icons})

    def _build_status_bar(self):
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.status_pos = QLabel("Ln: 1  Col: 1")
        self.status_length = QLabel("length: 0")
        self.status_lines = QLabel("lines: 1")
        self.status_eol = QLabel("Windows (CR LF)")
        self.status_encoding = QLabel("UTF-8")

        for label in (self.status_pos, self.status_length, self.status_lines, self.status_eol, self.status_encoding):
            self.status.addPermanentWidget(label)

    def _refresh_status_bar(self):
        editor = self._current_editor()
        if editor is None:
            return
        line, col = editor.getCursorPosition()
        self.status_pos.setText(f"Ln: {line + 1}  Col: {col + 1}")
        self.status_length.setText(f"length: {len(editor.text())}")
        self.status_lines.setText(f"lines: {editor.lines()}")
        self.status_encoding.setText("UTF-8")

    def _save_all(self):
        for i in range(self.tabs.count()):
            editor: CodeEditor = self.tabs.widget(i)
            if not editor.isModified():
                continue
            if editor.file_path:
                self._save_locally(editor, editor.file_path)
            elif editor.server_origin:
                self._save_to_server(editor, editor.server_origin["filename"], editor.server_origin["folder"])
            else:
                self.tabs.setCurrentIndex(i)
                self._save_current_as()

    # ---- tab management ---------------------------------------------------

    def _current_editor(self) -> CodeEditor:
        return self.tabs.currentWidget()

    def _editor_display_name(self, editor: CodeEditor) -> str:
        if editor.file_path:
            return os.path.basename(editor.file_path)
        if editor.server_origin:
            return editor.server_origin["filename"]
        return "Untitled"

    def _new_tab(self, path: str = None, content: str = "", server_origin: dict = None):
        editor = CodeEditor(self.theme_name, self.category_store)
        editor.tab_uuid = uuid.uuid4().hex  # stable id for temp-folder autosave naming
        editor.file_path = path
        editor.server_origin = server_origin
        editor.setText(content)

        if path:
            editor.load_lexer_for(path)
            folder = os.path.dirname(os.path.abspath(path))
            editor.bind_bookmark_location(bookmark_store.LocalLocation(folder), os.path.basename(path))
        elif server_origin:
            editor.load_lexer_for(server_origin["filename"])
            location = bookmark_store.ServerLocation(self.api_client, server_origin["folder"])
            editor.bind_bookmark_location(location, server_origin["filename"])

        editor.setModified(False)

        label = self._editor_display_name(editor)
        index = self.tabs.addTab(editor, label)
        self.tabs.setCurrentIndex(index)
        editor.modificationChanged.connect(lambda modified, ed=editor: self._on_modified_changed(ed, modified))
        editor.cursorPositionChanged.connect(lambda ln, col, ed=editor: self._refresh_status_bar_for(ed))
        editor.textChanged.connect(lambda ed=editor: self._refresh_status_bar_for(ed))
        self._refresh_status_bar()
        return editor

    def _on_current_tab_changed(self, index: int):
        self._refresh_status_bar()

    def _refresh_status_bar_for(self, editor: CodeEditor):
        # Ignore updates from background tabs -- only the visible tab's
        # cursor/length should drive the status bar.
        if editor is self._current_editor():
            self._refresh_status_bar()

    def _on_modified_changed(self, editor: CodeEditor, modified: bool):
        index = self.tabs.indexOf(editor)
        if index < 0:
            return
        label = self._editor_display_name(editor)
        self.tabs.setTabText(index, (label + " *") if modified else label)

    def _close_tab(self, index: int):
        editor: CodeEditor = self.tabs.widget(index)
        if editor.isModified():
            name = self._editor_display_name(editor)
            reply = QMessageBox.question(
                self, "Unsaved changes",
                f'"{name}" has unsaved changes. Close anyway?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self._new_tab()

    # ---- open / save --------------------------------------------------------

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            QMessageBox.critical(self, "Open failed", str(e))
            return
        self._new_tab(path=path, content=content)

    def _open_from_server(self):
        if not self.api_client:
            QMessageBox.warning(self, "Not logged in", "Log in from Settings first.")
            return
        dialog = OpenFromServerDialog(self, self.api_client, folder="saved", dark_theme=self.is_dark)
        if dialog.exec_() != dialog.Accepted:
            return
        try:
            content = self.api_client.load_file(dialog.selected_filename, dialog.selected_folder)
        except ApiError as e:
            QMessageBox.critical(self, "Open from server failed", str(e))
            return
        self._new_tab(server_origin={"folder": dialog.selected_folder, "filename": dialog.selected_filename}, content=content)

    def _save_current(self):
        editor = self._current_editor()
        if editor.file_path:
            self._save_locally(editor, editor.file_path)
        elif editor.server_origin:
            self._save_to_server(editor, editor.server_origin["filename"], editor.server_origin["folder"])
        else:
            self._save_current_as()

    def _save_current_as(self):
        editor = self._current_editor()
        dialog = SaveDestinationDialog(
            self,
            suggested_extension=os.path.splitext(editor.file_path or "")[1] or ".txt",
            server_available=self.api_client is not None,
            dark_theme=self.is_dark,
        )
        if dialog.exec_() != dialog.Accepted:
            return

        if dialog.destination == SAVE_TO_SERVER:
            self._save_to_server(editor, dialog.server_filename, folder="saved")
        else:
            current_ext = os.path.splitext(editor.file_path or "")[1]
            initial_filter = _filter_for_extension(current_ext) if current_ext else SAVE_AS_FILTERS.split(";;")[0]
            path, selected_filter = QFileDialog.getSaveFileName(
                self, "Save As", editor.file_path or "", SAVE_AS_FILTERS, initial_filter,
            )
            if not path:
                return
            if not os.path.splitext(path)[1]:
                ext = _extension_from_filter(selected_filter)
                if ext:
                    path += ext
            self._save_locally(editor, path)

    def _save_locally(self, editor: CodeEditor, path: str):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.text())
        except OSError as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return

        editor.file_path = path
        editor.load_lexer_for(path)
        folder = os.path.dirname(os.path.abspath(path))
        editor.rekey_bookmark_location(bookmark_store.LocalLocation(folder), os.path.basename(path))
        editor.setModified(False)
        index = self.tabs.indexOf(editor)
        self.tabs.setTabText(index, os.path.basename(path))
        self.status.showMessage(f"Saved {path}", 4000)

    def _save_to_server(self, editor: CodeEditor, filename: str, folder: str):
        if not self.api_client:
            QMessageBox.warning(self, "Not logged in", "Log in from Settings first.")
            return
        try:
            self.api_client.save_file(filename, editor.text(), folder=folder)
        except ApiError as e:
            QMessageBox.critical(self, "Save to server failed", str(e))
            return
        editor.server_origin = {"folder": folder, "filename": filename}
        editor.rekey_bookmark_location(bookmark_store.ServerLocation(self.api_client, folder), filename)
        editor.setModified(False)
        index = self.tabs.indexOf(editor)
        if index >= 0:
            self.tabs.setTabText(index, filename)
        self.status.showMessage(f"Saved '{filename}' to server", 4000)

    def _autosave_to_server(self):
        """Non-manual saves: push any dirty tab's content to the server temp
        folder, silently. This never touches the tab's real save state or
        local file -- it's purely a safety net."""
        if not self.api_client:
            return
        for i in range(self.tabs.count()):
            editor: CodeEditor = self.tabs.widget(i)
            if not editor.isModified():
                continue
            temp_name = f"autosave_{editor.tab_uuid}.tmp"
            try:
                self.api_client.save_file(temp_name, editor.text(), folder="temp")
                self.status.showMessage(f"Auto-synced unsaved changes ({self.tabs.tabText(i).rstrip(' *')})", 3000)
            except ApiError:
                # Silent by design -- don't interrupt typing with a dialog
                # every 2 minutes if the server happens to be unreachable.
                pass

    # ---- settings ---------------------------------------------------------

    def _open_bookmark_categories(self):
        dialog = bmcat.BookmarkCategoriesDialog(self.category_store, self, dark_theme=self.is_dark)
        dialog.exec_()

    def _open_login(self):
        session = load_session()
        default_url = session["base_url"] if session else ""
        dialog = LoginDialog(self, default_base_url=default_url, dark_theme=self.is_dark)
        if dialog.exec_() == dialog.Accepted:
            self.api_client = dialog.client
            self._refresh_login_menu_state()
            self.status.showMessage("Logged in", 3000)

    def _logout(self):
        clear_session()
        self.api_client = None
        self._refresh_login_menu_state()
        self.status.showMessage("Logged out", 3000)

    def _open_about(self):
        # Rich-text QLabel content (which QMessageBox renders its message
        # with) ignores the app's QSS "color" property and falls back to
        # black -- invisible against a dark background. Setting the color
        # inline in the HTML itself avoids that regardless of theme.
        text_color = {"light": "#000000", "dark": "#E0E0E0", "nord": "#ECEFF4"}[self.theme_name]
        link_color = {"light": "#0000EE", "dark": "#6CA0DC", "nord": "#88C0D0"}[self.theme_name]
        box = QMessageBox(self)
        box.setWindowTitle("About MyNote")
        box.setTextFormat(Qt.RichText)
        box.setText(
            f'<div style="color:{text_color};">'
            f"<h3>MyNote</h3>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>A small Notepad++-alike built on PyQt5 + QScintilla, with "
            f"optional login to save and open files from your own server.</p>"
            f'<p><a href="{PROJECT_URL}" style="color:{link_color};">{PROJECT_URL}</a></p>'
            f"</div>"
        )
        # QMessageBox's own message QLabel doesn't open links by default --
        # setOpenExternalLinks() makes clicking the repo link above launch
        # it in the system browser instead of doing nothing.
        label = box.findChild(QLabel, "qt_msgbox_label")
        if label is not None:
            label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            label.setOpenExternalLinks(True)
        theme.apply_dark_titlebar(box, self.is_dark)
        # Qt's automatic dialog centering has been seen to place a freshly
        # shown dialog off whatever screen the main window is actually on
        # (multi-monitor setups especially) -- pinning it relative to the
        # main window's own on-screen position guarantees it's visible.
        box.move(self.x() + 60, self.y() + 60)
        box.exec_()

    def _text_dialog(self, title: str, text: str, width: int = 560, height: int = 480):
        """Shared read-only scrollable text dialog used by the Help menu's
        How to Use / Change Log entries."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(width, height)
        dialog.move(self.x() + 60, self.y() + 60)  # see _open_about for why
        theme.apply_dark_titlebar(dialog, self.is_dark)

        layout = QVBoxLayout(dialog)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(text)
        text_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 10pt;")
        layout.addWidget(text_edit)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button, alignment=Qt.AlignRight)

        dialog.exec_()

    def _open_help(self):
        self._text_dialog("How to Use", HELP_TEXT)

    def _open_changelog(self):
        self._text_dialog("Change Log", CHANGELOG_TEXT)

    def _set_theme(self, name: str):
        if name == self.theme_name:
            return
        self.theme_name = name
        theme.apply_app_theme(self.theme_name)
        theme.apply_dark_titlebar(self, self.is_dark)
        for i in range(self.tabs.count()):
            self.tabs.widget(i).apply_theme(self.theme_name)
        self._refresh_toolbar_icons()
        config.save_json("prefs.json", {"theme": self.theme_name, "large_icons": self.large_icons})

    # ---- shutdown -----------------------------------------------------------

    def closeEvent(self, event):
        for i in range(self.tabs.count()):
            editor: CodeEditor = self.tabs.widget(i)
            if editor.isModified():
                name = self._editor_display_name(editor)
                reply = QMessageBox.question(
                    self, "Unsaved changes",
                    f'"{name}" has unsaved changes. Quit anyway?',
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    event.ignore()
                    return
        event.accept()


def main():
    app = QApplication(sys.argv)
    if os.path.isfile(APP_ICON_PATH):
        app.setWindowIcon(QIcon(APP_ICON_PATH))
    window = MainWindow()

    for path in sys.argv[1:]:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                window._new_tab(path=path, content=content)
            except OSError:
                pass

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
