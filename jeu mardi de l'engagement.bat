@echo off
setlocal

chcp 65001 >nul

set "GAME_DIR=%~dp0"

pushd "%GAME_DIR%" || (
    echo Unable to access project folder: "%GAME_DIR%"
    pause
    exit /b 1
)

py "%GAME_DIR%\play.py"
set "PY_EXIT=%ERRORLEVEL%"

if %PY_EXIT% neq 0 (
    echo Python finished with exit code %PY_EXIT%.
) else (
    echo Jeu termine. Appuyez sur une touche pour fermer.
)

pause

popd

exit /b %PY_EXIT%
