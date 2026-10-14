@echo off
cd /d "%~dp0"
set "TISSOT_PY=python"
if exist ".venv\Scripts\python.exe" set "TISSOT_PY=.venv\Scripts\python.exe"
"%TISSOT_PY%" manage.py check
if errorlevel 1 goto fail
"%TISSOT_PY%" manage.py migrate --noinput
if errorlevel 1 goto fail
"%TISSOT_PY%" manage.py seed_demo
if errorlevel 1 goto fail
"%TISSOT_PY%" manage.py create_demo_admin
if errorlevel 1 goto fail
echo Open http://127.0.0.1:8000/ in your browser.
echo Keep this window open. Press Ctrl+C to stop.
"%TISSOT_PY%" manage.py runserver 127.0.0.1:8000 --noreload
goto end
:fail
echo Setup failed. See README.md for installation instructions.
:end
pause
