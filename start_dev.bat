@echo off
echo ========================================================
echo   Starting Delhi DTC Crowdedness Journey Planner
echo ========================================================

echo 1. Launching FastAPI Backend on http://localhost:8000...
start cmd /k ".\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo 2. Launching Vite React Frontend on http://localhost:3000...
cd frontend
start cmd /k "npm run dev"

echo.
echo Application started!
echo Frontend: http://localhost:3000
echo Backend API & Swagger Docs: http://localhost:8000/docs
echo ========================================================
pause
