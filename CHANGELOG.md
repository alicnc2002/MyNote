# MyNote Change Log

Also viewable in-app: **Help > Change Log...**

## 1.4.0

- Added a **Help > How to Use...** entry covering basic editor operation
  and how to set up a personal server.
- About MyNote now links to the project's GitHub page.
- Fixed the Nord theme's menu bar/toolbar being the exact same color as
  the editor background.

## 1.3.0

- Added a Nord theme (View > Theme > Nord), alongside Light and Dark.
- Open from Server now has a folder picker, a "New Folder..." button to
  organize saved files, and a Delete button to remove files you no longer
  need straight from that dialog. New server endpoints: `files/delete.php`,
  `files/create_folder.php`, `files/list_folders.php`.
- Fixed a bright white line running down the fold margin in dark themes
  (QScintilla's boxed fold-tree connector lines were using their hardcoded
  default color instead of the theme's colors).

## 1.2.0

- Renamed the app from PyNotepad to MyNote.
- Fixed a bright, uncolored vertical line that showed up in the bookmark
  margin in dark theme (the margin's background wasn't repainting
  correctly).

## 1.1.0

- Added a "Remember me on this device" checkbox to the login dialog (off by
  default -- the session token is only saved to disk if you opt in). Fixes
  the login session being silently retained after logging in to test a
  build.
- Added a **Help** menu, with **About PyNotepad** and **Change Log**.

## 1.0.0

- Core editor: multi-tab editing with syntax highlighting for
  Python / HTML / PHP / plain text, Ctrl+MouseWheel zoom, Notepad++-style
  color theme with a dark mode toggle.
- Colored, named bookmark categories (Settings > Bookmark Categories...).
- Server account system: log in once, then Save to Server / Save Locally,
  Open from Server, and a background auto-sync of unsaved changes to a temp
  folder on the server.
- Self-service account setup: a "Create Account" button in the login dialog
  (and a matching `setup.php` wizard page) so a freshly uploaded server
  doesn't need any manual password hashing or file editing.
- Bookmarks follow the file, not the device: bookmarks are stored in a
  `bookmarks.json` sidecar next to the file itself (locally or on the
  server), tagged with a signature key so PyNotepad never overwrites an
  unrelated file of the same name. Opening the same file from a different
  computer or from the server shows the same bookmarks.
- Save As now offers real file-type filters (Python, HTML, PHP, Text,
  JavaScript, CSS, JSON, XML, Markdown, All Files) instead of only "All
  Files", so files get sensible extensions by default.
- UI polish: larger Login and Save dialogs, a "Larger Icons (1.5x)" toolbar
  option, a separate light-toolbar icon set for contrast in light mode, a
  custom app icon, and a fix so every dialog (not just the main window)
  follows the dark title bar setting.
- Packaged as a standalone Windows `.exe` (`build.bat`) with an optional
  code-signing script (`sign.bat`) for a self-signed certificate.
