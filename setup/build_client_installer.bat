@echo off
echo [✔] Membina folder installer Client...

:: Buat folder sementara
set OUTPUT=client_installer
rmdir /s /q %OUTPUT%
mkdir %OUTPUT%\client_app
mkdir %OUTPUT%\client_app\keys
mkdir %OUTPUT%\client_app\logs
mkdir %OUTPUT%\client_app\bin
mkdir %OUTPUT%\client_app\installer

:: Salin fail Python
copy client_app\main_client_ui.py %OUTPUT%\client_app\
copy client_app\sign_client.py %OUTPUT%\client_app\
copy client_app\verify_client.py %OUTPUT%\client_app\

:: Salin kunci (contoh public key)
copy client_app\keys\*.bin %OUTPUT%\client_app\keys\

:: Salin binari verify & sign
copy admin_app\bin\sign.exe %OUTPUT%\client_app\bin\
copy admin_app\bin\verify.exe %OUTPUT%\client_app\bin\

:: Salin installer tools
copy client_app\installer\*.bat %OUTPUT%\client_app\installer\
copy client_app\installer\*.reg %OUTPUT%\client_app\installer\
copy client_app\installer\readme.txt %OUTPUT%\client_app\installer\

echo [✔] Selesai bina folder %OUTPUT%
pause
