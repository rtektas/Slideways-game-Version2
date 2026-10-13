@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencies
where py >nul 2>nul
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto error
goto dependencies
:usepython
python -m venv .venv
if errorlevel 1 goto error
:dependencies
".venv\Scripts\python.exe" -c "from PyQt5.QtWidgets import QApplication; import pygame.mixer" >nul 2>nul
if not errorlevel 1 goto launch
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
:launch
".venv\Scripts\python.exe" projet3.py
if errorlevel 1 goto error
exit /b 0
:error
echo.
echo Impossible de lancer le jeu. Verifiez que Python 3 est installe.
echo La premiere installation des dependances necessite une connexion Internet.
pause
exit /b 1
