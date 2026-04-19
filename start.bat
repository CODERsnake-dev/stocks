@echo off
cd /d "%~dp0"

echo Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo =============================================
echo  Stock Tracker is starting...
echo  Open on this PC:   http://localhost:5000
echo.
echo  To open on your PHONE (same WiFi):
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /C:"IPv4 Address"') do (
    set ip=%%A
    goto :found
)
:found
set ip=%ip: =%
echo  Open on your phone: http://%ip%:5000
echo =============================================
echo.

python app.py
pause
