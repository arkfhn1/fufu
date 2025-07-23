@echo off
setlocal

REM Folder asal .bat ini
set SCRIPT_DIR=%~dp0

REM Fail registry
set REG_FILE=%SCRIPT_DIR%context_menu.reg

echo.
echo ============================
echo  Menambah Right-Click Menu
echo ============================
echo.

REM Semak jika fail .reg wujud
if not exist "%REG_FILE%" (
    echo [✘] Fail context_menu.reg tidak dijumpai!
    pause
    exit /b 1
)

REM Jalankan .reg untuk import ke Windows Registry
regedit /s "%REG_FILE%"

if %errorlevel%==0 (
    echo [✔] Right-click menu berjaya ditambah.
) else (
    echo [✘] Gagal tambah right-click menu.
)

echo.
pause
exit /b
