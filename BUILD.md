# Building MyNote.exe

1. Double-click `build.bat` in this folder.
2. It installs the app's dependencies, installs PyInstaller, then builds.
   Takes a minute or two -- a console window will show progress.
3. When it finishes, your executable is at `dist\MyNote.exe` -- a single
   file with everything bundled in (including the icons and app icon), no
   Python installation required to run it.

Copy `MyNote.exe` anywhere you like (Desktop, a USB drive, another
Windows PC) and double-click it to run.

## Rebuilding after code changes

Just run `build.bat` again -- it always builds fresh from whatever's
currently in this folder.

## Notes

- This produces a single-file ("onefile") build. It's the simplest thing to
  share, at the cost of a slightly slower startup (PyInstaller unpacks
  itself to a temp folder each launch) compared to a multi-file build. If
  startup speed becomes annoying, ask to switch `build.bat`'s
  `--onefile` to `--onedir` -- you'd then share the whole `dist\MyNote\`
  folder instead of one file.
- `--windowed` suppresses the console window MyNote itself would
  otherwise show (it's a GUI app; nothing prints to a console in normal
  use).
- Windows SmartScreen or antivirus may flag a freshly built, unsigned .exe
  from an unrecognized publisher the first time it runs -- that's normal
  for any home-built executable, not a sign anything's wrong. "More info" >
  "Run anyway" in the SmartScreen prompt, or add an exclusion in your
  antivirus if it gets quarantined.

## Signing it (optional)

After building, double-click `sign.bat` to sign `dist\MyNote.exe` with a
self-signed certificate (generated automatically, no extra tools needed --
just what's already built into Windows PowerShell). This replaces "Unknown
Publisher" with "MyNote (self-signed)" and makes the file tamper-evident.

It does **not** stop SmartScreen warnings on other people's PCs by itself --
a self-signed certificate is only trusted where you've explicitly imported
it. `sign.bat` prints the exact two commands for that (they need an admin
PowerShell window, since trusting a certificate system-wide requires
elevation -- that's a Windows security boundary, not something any script
can do unattended).

For warning-free distribution to strangers, you'd need a certificate from a
CA (e.g. Sectigo, DigiCert, SSL.com -- roughly $70-250/year, requires ID
verification) or Microsoft's Trusted Signing service (~$10/month). Once you
have either, the same `Set-AuthenticodeSignature` approach in `sign.ps1`
works with a real certificate in place of the self-signed one -- ask if you
get to that point and want the script adjusted.
