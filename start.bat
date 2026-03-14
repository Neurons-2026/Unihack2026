@echo off
echo Starting 10min AI Daily...
echo.

start "Backend" cmd /k "cd /d C:\Users\yunka\OneDrive\Desktop\Hackathon\backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

start "Frontend" cmd /k "cd /d C:\Users\yunka\OneDrive\Desktop\Hackathon\frontend && npm run dev"

timeout /t 5 /nobreak >nul

start http://localhost:3000

echo Both servers started. Browser opening...
