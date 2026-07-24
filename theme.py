"""
Color schemes for the editor and app chrome, selected by a theme name
string: "light", "dark", or "nord".

- "light": NPP's classic default stylers.xml palette.
- "dark": NPP's real "Dark Mode" editor theme, which is the Zenburn-based
  scheme shipped as installer/themes/DarkModeDefault.xml (background
  #3F3F3F, foreground #DCDCCC, etc.) -- these are the *exact* hex values
  from that file, not an approximation. Dark UI chrome colors (menus/
  dialogs/tabs/status bar) are NPP's own dark mode UI palette from
  PowerEditor/src/NppDarkMode.cpp (the "Black" theme: background #202020,
  text #E0E0E0, etc.).
- "nord": the Nord color scheme (https://www.nordtheme.com/), Polar
  Night/Snow Storm/Frost/Aurora palette -- same hex values as the
  project's own reference palette.

Every theme other than "light" also themes the whole application (menus,
tabs, dialogs, scrollbars, status bar), not just the text area -- "light"
needs no stylesheet at all since Qt's own default palette already looks
right against a white editor background.
"""

import sys

from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Editor content colors
# ---------------------------------------------------------------------------

NPP_COLORS = {
    "background": QColor("#FFFFFF"),
    "foreground": QColor("#000000"),
    "caret": QColor("#000000"),
    "caret_line": QColor("#EFEFEF"),
    "selection_bg": QColor("#C0DCE7"),
    "selection_fg": None,  # keep the text's own color when selected
    "margin_bg": QColor("#E4E4E4"),
    "margin_fg": QColor("#808080"),
    "comment": QColor("#008000"),
    "number": QColor("#FF8000"),
    "keyword": QColor("#0000FF"),
    "string": QColor("#A31515"),
    "preprocessor": QColor("#804000"),
    "operator": QColor("#000000"),
    "tag": QColor("#800000"),
    "attribute": QColor("#FF0000"),
}

# Exact values from PowerEditor/installer/themes/DarkModeDefault.xml
# (Zenburn-based -- this is what Notepad++ itself switches editor content
# to when you enable Dark Mode).
DARK_COLORS = {
    "background": QColor("#3F3F3F"),
    "foreground": QColor("#DCDCCC"),
    "caret": QColor("#8FAF9F"),
    "caret_line": QColor("#101010"),
    "selection_bg": QColor("#585858"),
    "selection_fg": QColor("#000000"),
    "margin_bg": QColor("#0C0C0C"),
    "margin_fg": QColor("#8A8A8A"),
    "comment": QColor("#7F9F7F"),
    "number": QColor("#8CD0D3"),
    "keyword": QColor("#DFC47D"),
    "string": QColor("#CC9393"),
    "preprocessor": QColor("#DFC47D"),
    "operator": QColor("#9F9D6D"),
    "tag": QColor("#E3CEAB"),
    "attribute": QColor("#DFDFDF"),
    "fold_fg": QColor("#707070"),
    "fold_active_fg": QColor("#7F9F7F"),
    "fold_margin_bg": QColor("#101010"),
    "class_name": QColor("#DCDCCC"),
    "function_name": QColor("#CEDF99"),
    "decorator": QColor("#93E0E3"),
}

# Nord (https://www.nordtheme.com/docs/colors-and-palettes): Polar Night
# (nord0-3, darkest to lightest) for backgrounds, Snow Storm (nord4-6) for
# foreground text, Frost (nord7-10) for keywords/types, Aurora (nord11-15)
# for the usual red/orange/yellow/green/purple accent roles.
NORD_COLORS = {
    "background": QColor("#2E3440"),   # nord0
    "foreground": QColor("#D8DEE9"),   # nord4
    "caret": QColor("#D8DEE9"),        # nord4
    "caret_line": QColor("#3B4252"),   # nord1
    "selection_bg": QColor("#434C5E"),  # nord2
    "selection_fg": None,
    "margin_bg": QColor("#3B4252"),    # nord1
    "margin_fg": QColor("#4C566A"),    # nord3
    "comment": QColor("#616E88"),      # muted blue-gray (standard Nord comment tone)
    "number": QColor("#B48EAD"),       # nord15
    "keyword": QColor("#81A1C1"),      # nord9
    "string": QColor("#A3BE8C"),       # nord14
    "preprocessor": QColor("#5E81AC"),  # nord10
    "operator": QColor("#81A1C1"),     # nord9
    "tag": QColor("#81A1C1"),          # nord9
    "attribute": QColor("#8FBCBB"),    # nord7
    "fold_fg": QColor("#4C566A"),      # nord3
    "fold_active_fg": QColor("#88C0D0"),  # nord8
    "fold_margin_bg": QColor("#3B4252"),  # nord1
    "class_name": QColor("#8FBCBB"),   # nord7
    "function_name": QColor("#88C0D0"),  # nord8
    "decorator": QColor("#D08770"),    # nord12
}

_EDITOR_COLORS = {
    "light": NPP_COLORS,
    "dark": DARK_COLORS,
    "nord": NORD_COLORS,
}

# ---------------------------------------------------------------------------
# Application chrome colors (menus, dialogs, tabs, status bar)
# ---------------------------------------------------------------------------

# Exact values from PowerEditor/src/NppDarkMode.cpp ("Black" dark theme).
DARK_CHROME = {
    "background": QColor("#202020"),
    "softer_background": QColor("#383838"),
    "hot_background": QColor("#454545"),
    "text": QColor("#E0E0E0"),
    "darker_text": QColor("#C0C0C0"),
    "disabled_text": QColor("#808080"),
    "edge": QColor("#646464"),
    "hot_edge": QColor("#9B9B9B"),
    "disabled_edge": QColor("#484848"),
}

NORD_CHROME = {
    # One Nord swatch lighter than the editor's own nord0 background (see
    # NORD_COLORS["background"] below) -- otherwise the menu bar/toolbar are
    # the exact same color as the text area and visually merge into it.
    "background": QColor("#3B4252"),      # nord1
    "softer_background": QColor("#434C5E"),  # nord2
    "hot_background": QColor("#4C566A"),  # nord3
    "text": QColor("#ECEFF4"),            # nord6
    "darker_text": QColor("#D8DEE9"),     # nord4
    "disabled_text": QColor("#4C566A"),   # nord3
    "edge": QColor("#4C566A"),            # nord3
    "hot_edge": QColor("#88C0D0"),        # nord8
    "disabled_edge": QColor("#434C5E"),   # nord2
}

# "light" intentionally has no chrome entry -- it uses no stylesheet at all.
_CHROME = {
    "dark": DARK_CHROME,
    "nord": NORD_CHROME,
}

# Display order + labels for the Theme menu.
THEME_NAMES = ("light", "dark", "nord")
THEME_LABELS = {"light": "Light", "dark": "Dark", "nord": "Nord"}

EDITOR_FONT_FAMILY = "Consolas"
EDITOR_FONT_SIZE = 10

# Raw Scintilla "structural default" style -- covers the blank/unstyled
# canvas area (e.g. past end of text) that a QsciLexer's own numbered
# styles don't reach. Left uncolored, this is what causes a leftover light
# rectangle when switching to a dark theme.
STYLE_DEFAULT = 32

# The line-number margin's digit text is drawn using this style, not via
# any per-margin "foreground" setting -- confirmed against NPP's own
# DarkModeDefault.xml, which styles "Line number margin" as styleID 33.
STYLE_LINENUMBER = 33

# Margin indices, mirrored from editor_widget.py (kept independent here so
# theme.py has no import dependency on it).
MARGIN_LINE_NUMBERS = 0
MARGIN_SYMBOLS = 1
MARGIN_FOLD = 2


def is_dark_theme(theme_name: str) -> bool:
    """Every theme except "light" reads as dark for purposes like the
    native title bar and which toolbar icon set (light-on-dark vs
    dark-on-light) to use."""
    return theme_name != "light"


def editor_font() -> QFont:
    font = QFont(EDITOR_FONT_FAMILY, EDITOR_FONT_SIZE)
    font.setStyleHint(QFont.Monospace)
    return font


def _scintilla_color_int(color: QColor) -> int:
    """Scintilla wants colors packed as 0x00BBGGRR, not Qt's usual RGB order."""
    return (color.blue() << 16) | (color.green() << 8) | color.red()


def apply_theme_to_lexer(lexer, theme_name: str = "light") -> None:
    """
    Applies the given theme's palette to any QsciLexer subclass by walking
    its style numbers and recoloring the ones that look like
    comments/strings/etc. by name (QsciLexer.description(style) is defined
    generically for every lexer, so this works across QsciLexerPython,
    QsciLexerHTML, etc. without needing a separate style-id table per
    lexer).
    """
    colors = _EDITOR_COLORS.get(theme_name, NPP_COLORS)
    font = editor_font()

    lexer.setDefaultFont(font)
    lexer.setDefaultColor(colors["foreground"])
    lexer.setDefaultPaper(colors["background"])
    lexer.setFont(font)

    for style in range(128):
        try:
            desc = lexer.description(style)
        except Exception:
            break
        if not desc:
            continue

        name = desc.lower()
        lexer.setPaper(colors["background"], style)
        lexer.setFont(font, style)

        if "comment" in name:
            lexer.setColor(colors["comment"], style)
        elif "number" in name:
            lexer.setColor(colors["number"], style)
        elif "keyword" in name or "word" in name:
            bold_font = QFont(font)
            bold_font.setBold(True)
            lexer.setFont(bold_font, style)
            lexer.setColor(colors["keyword"], style)
        elif "string" in name or "quoted" in name or "character" in name:
            lexer.setColor(colors["string"], style)
        elif "preprocessor" in name:
            lexer.setColor(colors["preprocessor"], style)
        elif "decorator" in name:
            lexer.setColor(colors.get("decorator", colors["preprocessor"]), style)
        elif "def" in name or "function" in name or "method" in name:
            lexer.setColor(colors.get("function_name", colors["foreground"]), style)
        elif "class" in name:
            lexer.setColor(colors.get("class_name", colors["foreground"]), style)
        elif "tag" in name:
            lexer.setColor(colors["tag"], style)
        elif "attribute" in name:
            lexer.setColor(colors["attribute"], style)
        elif "operator" in name:
            lexer.setColor(colors["operator"], style)
        else:
            lexer.setColor(colors["foreground"], style)


def apply_theme_to_editor(editor, theme_name: str = "light") -> None:
    """Colors that live on the QsciScintilla widget itself, outside the
    lexer: caret, selection, margins, current-line highlight, folding, and
    the raw Scintilla STYLE_DEFAULT (32) that lexers don't cover."""
    colors = _EDITOR_COLORS.get(theme_name, NPP_COLORS)

    editor.setCaretForegroundColor(colors["caret"])
    editor.setCaretLineVisible(True)
    editor.setCaretLineBackgroundColor(colors["caret_line"])
    editor.setSelectionBackgroundColor(colors["selection_bg"])
    if colors.get("selection_fg") is not None:
        editor.setSelectionForegroundColor(colors["selection_fg"])
    else:
        editor.resetSelectionForegroundColor()
    editor.setColor(colors["foreground"])
    editor.setPaper(colors["background"])
    editor.setFont(editor_font())

    # Margin colors, done via raw Scintilla messages rather than
    # setMarginsBackgroundColor()/setMarginsForegroundColor(): those
    # high-level QScintilla calls turned out not to reliably repaint
    # already-configured NumberMargin/SymbolMargin margins in testing
    # (the margins stayed light while the text area, styled the same
    # low-level way below, went dark correctly) -- so every margin color
    # here goes through SendScintilla() directly, the same mechanism
    # already proven to work for the text area's STYLE_DEFAULT.
    back = _scintilla_color_int(colors["background"])
    fore = _scintilla_color_int(colors["foreground"])
    margin_back = _scintilla_color_int(colors["margin_bg"])
    margin_fore = _scintilla_color_int(colors["margin_fg"])
    fold_back = _scintilla_color_int(colors.get("fold_margin_bg", colors["margin_bg"]))

    # Text area default style (covers blank/unstyled canvas beyond the
    # lexer's own styles, e.g. past the end of the text).
    editor.SendScintilla(editor.SCI_STYLESETBACK, STYLE_DEFAULT, back)
    editor.SendScintilla(editor.SCI_STYLESETFORE, STYLE_DEFAULT, fore)

    # SCI_STYLECLEARALL resets EVERY style (line numbers included) to match
    # STYLE_DEFAULT -- it must run right after STYLE_DEFAULT is set and
    # before any more specific style below, otherwise it would immediately
    # wipe out the line-number styling that follows.
    editor.SendScintilla(editor.SCI_STYLECLEARALL)

    # Line-number digits are drawn using STYLE_LINENUMBER, not a per-margin
    # foreground setting.
    editor.SendScintilla(editor.SCI_STYLESETBACK, STYLE_LINENUMBER, margin_back)
    editor.SendScintilla(editor.SCI_STYLESETFORE, STYLE_LINENUMBER, margin_fore)

    # Per-margin background. SCI_SETMARGINBACKN only reliably repaints a
    # margin whose *type* is SC_MARGIN_COLOUR -- the number margin gets its
    # background from STYLE_LINENUMBER above so its default type is fine,
    # but the symbol (bookmark) and fold margins default to SC_MARGIN_SYMBOL
    # (type 0), which Scintilla does NOT recolor via SETMARGINBACKN. Left
    # alone, that showed up as a bright, un-themed vertical strip sitting
    # right where the bookmark margin is in dark/Nord mode. Switching those
    # two margins' raw type to SC_MARGIN_COLOUR (4) makes them honor
    # SETMARGINBACKN like the docs promise, while still drawing markers
    # (bookmark dots / fold arrows) normally on top.
    SC_MARGIN_COLOUR = 4
    editor.SendScintilla(editor.SCI_SETMARGINTYPEN, MARGIN_SYMBOLS, SC_MARGIN_COLOUR)
    editor.SendScintilla(editor.SCI_SETMARGINTYPEN, MARGIN_FOLD, SC_MARGIN_COLOUR)

    editor.SendScintilla(editor.SCI_SETMARGINBACKN, MARGIN_LINE_NUMBERS, margin_back)
    editor.SendScintilla(editor.SCI_SETMARGINBACKN, MARGIN_SYMBOLS, margin_back)
    editor.SendScintilla(editor.SCI_SETMARGINBACKN, MARGIN_FOLD, fold_back)

    # BoxedTreeFoldStyle draws its little +/- boxes and the connector lines
    # between them using QScintilla's own *default* marker colors -- a
    # hardcoded white line on a black box -- until told otherwise, which is
    # completely separate from the fold margin *background* colored just
    # above. That hardcoded white line is the persistent bright vertical
    # line seen down the fold margin column in dark/Nord mode: it's drawn
    # even in a brand-new empty file, because BoxedTreeFoldStyle always
    # renders its root descender guide down the full visible height, not
    # just next to actual foldable lines. setFoldMarginColors() is Qsci's
    # own API for recoloring both the margin fill and the fold markers/
    # connector lines together, wiring up the "fold_fg" color role that
    # was defined above but never actually applied anywhere.
    fold_line = colors.get("fold_fg", colors["margin_fg"])
    editor.setFoldMarginColors(fold_line, colors.get("fold_margin_bg", colors["margin_bg"]))


# ---------------------------------------------------------------------------
# Whole-application chrome theming (menus, dialogs, tabs, status bar)
# ---------------------------------------------------------------------------

def _chrome_stylesheet(c: dict) -> str:
    return f"""
    QMainWindow, QDialog {{
        background-color: {c['background'].name()};
        color: {c['text'].name()};
    }}
    QMenuBar {{
        background-color: {c['background'].name()};
        color: {c['text'].name()};
    }}
    QMenuBar::item:selected {{
        background-color: {c['hot_background'].name()};
    }}
    QMenu {{
        background-color: {c['softer_background'].name()};
        color: {c['text'].name()};
        border: 1px solid {c['edge'].name()};
    }}
    QMenu::item:selected {{
        background-color: {c['hot_background'].name()};
    }}
    QMenu::item:disabled {{
        color: {c['disabled_text'].name()};
    }}
    QTabWidget::pane {{
        border: none;
        background-color: {c['background'].name()};
    }}
    QTabBar::tab {{
        background-color: {c['softer_background'].name()};
        color: {c['text'].name()};
        padding: 5px 10px;
        border: 1px solid {c['edge'].name()};
    }}
    QTabBar::tab:selected {{
        background-color: {c['hot_background'].name()};
        border-top: 2px solid #8DC63F;
    }}
    QToolBar {{
        background-color: {c['background'].name()};
        border: none;
        spacing: 2px;
        padding: 2px;
    }}
    QToolButton {{
        background-color: transparent;
        border: 1px solid transparent;
        padding: 3px;
    }}
    QToolButton:hover {{
        background-color: {c['hot_background'].name()};
        border: 1px solid {c['hot_edge'].name()};
    }}
    QStatusBar {{
        background-color: {c['background'].name()};
        color: {c['darker_text'].name()};
    }}
    QStatusBar QLabel {{
        color: {c['darker_text'].name()};
        padding: 0 8px;
        border-left: 1px solid {c['edge'].name()};
    }}
    QScrollBar:vertical {{
        background: {c['background'].name()};
        width: 14px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['softer_background'].name()};
        min-height: 24px;
        border: 1px solid {c['edge'].name()};
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['hot_background'].name()};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {c['background'].name()};
        height: 14px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {c['softer_background'].name()};
        min-width: 24px;
        border: 1px solid {c['edge'].name()};
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c['hot_background'].name()};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    QLabel {{
        color: {c['text'].name()};
    }}
    QComboBox {{
        background-color: {c['softer_background'].name()};
        color: {c['text'].name()};
        border: 1px solid {c['edge'].name()};
        padding: 3px 6px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['softer_background'].name()};
        color: {c['text'].name()};
        selection-background-color: {c['hot_background'].name()};
    }}
    QLineEdit, QListWidget, QTextEdit {{
        background-color: {c['softer_background'].name()};
        color: {c['text'].name()};
        border: 1px solid {c['edge'].name()};
    }}
    QPushButton {{
        background-color: {c['softer_background'].name()};
        color: {c['text'].name()};
        border: 1px solid {c['edge'].name()};
        padding: 4px 10px;
    }}
    QPushButton:hover {{
        background-color: {c['hot_background'].name()};
        border: 1px solid {c['hot_edge'].name()};
    }}
    QPushButton:disabled {{
        color: {c['disabled_text'].name()};
        border: 1px solid {c['disabled_edge'].name()};
    }}
    QRadioButton, QCheckBox {{
        color: {c['text'].name()};
    }}
    QFrame {{
        color: {c['text'].name()};
    }}
    """


def apply_app_theme(theme_name: str) -> None:
    app = QApplication.instance()
    if app is None:
        return
    chrome = _CHROME.get(theme_name)
    app.setStyleSheet(_chrome_stylesheet(chrome) if chrome else "")


def apply_dark_titlebar(window, dark: bool) -> None:
    """Best-effort native Windows title bar dark mode (DWM), matching NPP's
    own OS-drawn title bar -- a QSS stylesheet can't reach this since it's
    painted by Windows, not Qt. No-op on non-Windows or on Windows builds
    without DWM immersive-dark-mode support (older than ~2019H1)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(window.winId())
        value = ctypes.c_int(1 if dark else 0)
        # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE on Windows 10 20H1+ / 11.
        # 19 = the same attribute's id on earlier Windows 10 builds.
        for attr in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                ctypes.c_void_p(hwnd), attr, ctypes.byref(value), ctypes.sizeof(value)
            )
            if result == 0:
                break

        # Windows 11 also draws a thin 1px border around the *whole window*
        # in the system accent color (Settings > Personalization > Colors)
        # -- separate from the title bar's dark/light mode above, and not
        # reachable from a Qt stylesheet since it's DWM compositor chrome,
        # not anything the app draws itself. Against a dark editor/toolbar
        # background that accent-colored border reads as a stray bright
        # line down the window's edges (most noticeable on the left, right
        # against the plain editor background). DWMWA_BORDER_COLOR (34,
        # Windows 11 22H2+) lets us turn it off for dark themes and put it
        # back for light theme.
        DWMWA_BORDER_COLOR = 34
        border_value = ctypes.c_int(-2 if dark else -1)  # DWMWA_COLOR_NONE / DWMWA_COLOR_DEFAULT
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.c_void_p(hwnd), DWMWA_BORDER_COLOR, ctypes.byref(border_value), ctypes.sizeof(border_value)
        )
    except Exception:
        pass  # never let a cosmetic title-bar tweak crash the app
