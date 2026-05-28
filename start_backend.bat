@echo off
REM Simple helper to create a virtualenv (if missing), install requirements,
REM and start the FastAPI backend with Uvicorn.

if not exist ".venv" (
  python -m venv .venv
)

set PY=.venv\Scripts\python.exe
%PY% -m pip install -r backend/requirements.txt
echo Starting backend via %PY%...
%PY% -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
