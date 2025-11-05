@echo off
setlocal EnableDelayedExpansion

chcp 65001 >nul

echo ================================================
echo   Installation du projet "jeu mardi de l'engagement"
echo ================================================

echo.
set "REPO_URL=https://codeload.github.com/stimoi/atelier-cr-ation_de_jeux_vid-os/zip/refs/heads/main"
set "ZIP_PATH=%TEMP%\atelier-jeu.zip"
set "EXTRACT_DIR=%TEMP%\atelier-jeu-extract"
set "TARGET_DIR=%USERPROFILE%\Documents\jeu mardi de l'engagement"
set "SCRIPT_DIR=%~dp0"
set "PY_READY=0"
set "SHORTCUT_NAME=Jeu mardi de l'engagement.lnk"

echo Dossier cible : "%TARGET_DIR%"
if exist "%TARGET_DIR%" (
    echo.
    echo Le dossier existe deja.
    choice /M "Voulez-vous le remplacer"
    if errorlevel 2 (
        echo Installation annulee.
        goto :END
    )
    echo Suppression de l'ancien dossier...
    rmdir /s /q "%TARGET_DIR%"
    if exist "%TARGET_DIR%" (
        echo Impossible de supprimer "%TARGET_DIR%". Fermez les fichiers ouverts et relancez.
        goto :END
    )
)

echo Nettoyage des fichiers temporaires...
if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%"
if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"

echo.
echo Telechargement du projet depuis GitHub...
powershell -NoProfile -Command "try { Invoke-WebRequest '%REPO_URL%' -OutFile '%ZIP_PATH%' -UseBasicParsing } catch { exit 1 }"
if errorlevel 1 (
    echo Echec du telechargement. Verifiez votre connexion Internet.
    goto :END
)

echo Extraction des fichiers...
powershell -NoProfile -Command "try { Expand-Archive -LiteralPath '%ZIP_PATH%' -DestinationPath '%EXTRACT_DIR%' -Force } catch { exit 1 }"
if errorlevel 1 (
    echo Echec de l'extraction du ZIP.
    goto :END
)

echo Recherche du dossier extrait...
set "SOURCE_DIR="
for /d %%D in ("%EXTRACT_DIR%\*") do (
    set "SOURCE_DIR=%%~fD"
    goto :FOUND_SOURCE
)
:FOUND_SOURCE
if not defined SOURCE_DIR (
    echo Impossible de trouver le dossier extrait.
    goto :END
)

echo Creation du dossier cible...
mkdir "%TARGET_DIR%" 2>nul
if not exist "%TARGET_DIR%" (
    echo Impossible de creer "%TARGET_DIR%".
    goto :END
)

echo Copie des fichiers vers "%TARGET_DIR%"...
robocopy "%SOURCE_DIR%" "%TARGET_DIR%" /E >nul
set "ROBO_EXIT=%ERRORLEVEL%"
if %ROBO_EXIT% GEQ 8 (
    echo Echec de la copie (code %ROBO_EXIT%).
    goto :END
)

echo Copie eventuelle de play.py du dossier courant...
if exist "%SCRIPT_DIR%play.py" (
    copy /Y "%SCRIPT_DIR%play.py" "%TARGET_DIR%\play.py" >nul
)

echo.
echo Verification de la presence de Python...
py --version >nul 2>&1
if errorlevel 1 (
    echo Python n'est pas detecte. Tentative d'installation via winget...
    winget --version >nul 2>&1
    if errorlevel 1 (
        echo Winget est indisponible. Installez Python 3.11 manuellement puis relancez ce script.
        goto :END
    )
    winget install -e --id Python.Python.3.11
    py --version >nul 2>&1
    if errorlevel 1 (
        echo Impossible d'installer Python automatiquement.
        goto :END
    )
)
set "PY_READY=1"

echo Mise a jour de pip et installation de pygame...
py -m ensurepip --upgrade >nul 2>&1
py -m pip install --upgrade pip
if errorlevel 1 (
    echo Echec de la mise a jour de pip.
    goto :END
)
py -m pip install --upgrade pygame
if errorlevel 1 (
    echo Echec de l'installation de pygame. Relancez la commande manuellement si besoin.
    goto :END
)

echo Creation d'un raccourci sur le Bureau...
powershell -NoProfile -Command "try { $ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $shortcutPath = Join-Path $desktop '%SHORTCUT_NAME%'; $shortcut = $ws.CreateShortcut($shortcutPath); $shortcut.TargetPath = '%SystemRoot%\py.exe'; $shortcut.Arguments = ' \"%TARGET_DIR%\play.py\"'; $shortcut.WorkingDirectory = '%TARGET_DIR%'; $shortcut.Description = 'Jeu mardi de l''engagement'; $shortcut.Save(); exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo Impossible de creer le raccourci automatiquement.
)

echo.
echo ================================================
echo   Installation terminee avec succes !
echo   Lancez le jeu via : "%TARGET_DIR%\play.py"
echo ================================================

echo.
pause
goto :EOF

:END
echo.
echo Le script s'est termine avec une erreur.
pause
exit /b 1
