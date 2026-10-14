@echo off
chcp 65001 > nul
title Gokturk Medya Istasyonu Kaldirma Sihirbazi
color 0C

:: Yonetici izni kontrolu
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] HATA: Lutfen bu dosyaya SAG TIKLAYIP "YONETICI OLARAK CALISTIR" deyin.
    pause
    exit /b
)

echo =====================================================
echo    Gokturk Medya Istasyonu Kaldirma Sihirbazi
echo =====================================================
echo.
echo [!] DIKKAT: Bu islem programi, ayarlari ve masaustu kisayolunu TAMAMEN SILECEKTIR.
echo.
set /p ONAY="Devam etmek istiyor musunuz? (E/H): "

if /i "%ONAY%" neq "E" (
    echo.
    echo [-] Islem kullanici tarafindan iptal edildi.
    timeout /t 2 > nul
    exit /b
)

echo.
echo [-] Temizlik operasyonu baslatiliyor...
echo.

:: 1. Masaustu Kisayolunu Silme
powershell -Command "$desktop = [Environment]::GetFolderPath('Desktop'); if (Test-Path \"$desktop\Gokturk Dizi Indirici.lnk\") { Remove-Item \"$desktop\Gokturk Dizi Indirici.lnk\" -Force }"
echo [+] Masaustu kisayolu silindi.

:: 2. APPDATA Ayar Klasorunu Silme
if exist "%APPDATA%\GokturkMediaDownloader" (
    rd /s /q "%APPDATA%\GokturkMediaDownloader"
    echo [+] Kullanici ayarlari ve indirme profilleri temizlendi.
)

:: 3. Kendi Klasorunu Silme Hilesi (Temp klasorune zoplama)
if "%~dp0"=="%TEMP%\" goto :KlasoruUcur

copy /y "%~f0" "%TEMP%\GokturkKaldir.bat" > nul
start "" "%TEMP%\GokturkKaldir.bat"
exit /b

:KlasoruUcur
timeout /t 1 /nobreak > nul

if exist "C:\DiziIndirici" (
    rd /s /q "C:\DiziIndirici"
    echo [+] Program dosyalari (C:\DiziIndirici) basariyla silindi.
)

echo.
echo =====================================================
echo [✓] GOKTURK MEDYA ISTASYONU SISTEMDEN TEMIZLENDI!
echo =====================================================
echo.
echo Pencereyi kapattiginizda gecici dosyalar da silinecektir.
pause

del "%TEMP%\GokturkKaldir.bat" & exit
