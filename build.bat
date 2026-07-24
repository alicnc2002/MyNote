@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL%==0 (
    set PY=python
) else (
    where py >nul 2>nul
    if %ERRORLEVEL%==0 (
        set PY=py
    ) else (
        echo Could not find Python on PATH. Install Python first, then re-run this script.
        pause
        exit /b 1
    )
)

echo Using %PY%
echo.
echo Installing app dependencies (PyQt5, QScintilla, requests)...
%PY% -m pip install --upgrade -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies. See errors above.
    pause
    exit /b 1
)

echo.
echo Installing PyInstaller...
%PY% -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo Failed to install PyInstaller. See errors above.
    pause
    exit /b 1
)

echo.
echo Building MyNote.exe (this can take a minute or two)...
%PY% -m PyInstaller --noconfirm --clean --name MyNote --onefile --windowed ^
    --icon icons\app_icon.ico ^
    --add-data "icons;icons" ^
    main.py

echo.
if exist dist\MyNote.exe (
    echo Build succeeded: dist\MyNote.exe
    echo You can copy that one file anywhere and run it -- no Python install needed.
) else (
    echo Build did not produce dist\MyNote.exe -- check the messages above for errors.
)
pause
