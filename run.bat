@echo off
chcp 65001 > nul
title eMaktab Avto-Kirish Tizimi

echo ========================================================
echo        eMaktab.uz Avto-Kirish va Faollik Tizimi
echo ========================================================
echo.

cd /d "%~dp0"

IF NOT EXIST ".venv\Scripts\python.exe" (
    echo [!] Virtual muhit (.venv) topilmadi. Yaratilmoqda...
    python -m venv .venv
    echo [*] Kerakli kutubxonalar o'rnatilmoqda...
    .venv\Scripts\pip.exe install -r requirements.txt
)

echo [*] Dastur ishga tushmoqda...
echo [*] Brauzerda ochish manzili: http://localhost:5000
echo.

start "" "http://localhost:5000"

.venv\Scripts\python.exe app.py
pause
