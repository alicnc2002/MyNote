# MyNote

Tiny portable note app in Python. Inspired by Notepad++, with optional
personal server support so your files and bookmarks follow you across
machines.

## Features

- Multi-tab editing with syntax highlighting for Python / HTML / PHP /
  plain text
- Notepad++-style color themes: Light, Dark, and Nord (`View > Theme`)
- Ctrl+MouseWheel zoom
- Colored, named bookmark categories, click the margin next to any line
  to tag it (`Settings > Bookmark Categories...`)
- Optional account login: save to / open from your own server, with a
  background auto-sync of unsaved changes so you never lose work
- Self-contained Windows `.exe` build, no Python install required to run it

See `Help > How to Use...` inside the app for a full walkthrough, and
`Help > Change Log...` for release history.

## Running from source

Requires Python 3.9+ and the packages in `requirements.txt`:

```
pip install -r requirements.txt
python main.py
```

## Building a standalone Windows .exe

See [BUILD.md](BUILD.md) -- short version: double-click `build.bat`, the
finished `MyNote.exe` lands in `dist\`.

## Setting up a personal server (optional)

MyNote works entirely offline with no server at all. If you want your
files to follow you across machines, the PHP backend that powers
save/open-from-server lives in [`../server/`](../server) (see that
folder's own README for hosting requirements and setup steps). Once
it's hosted somewhere, use `Settings > Log in...` in the app to connect.

## License

GPL-3.0 -- see [LICENSE](../LICENSE).
