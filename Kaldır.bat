@echo off
chcp 65001 > nul
title Gokturk Medya Istasyonu Kaldirma Sihirbazı
color 0C

:: Yönetici izni kontrolü (C diskinden dosya silmek için şart)
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
echo [!] DIKKAT: Bu islem programi, ayarları ve masaustu kisayolunu TAMAMEN SILECEKTIR.
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

:: 1. Masaüstü Kısayolunu Silme (Türkçe/İngilizce Windows fark etmez)
powershell -Command "$desktop = [Environment]::GetFolderPath('Desktop'); if (Test-Path \"$desktop\Gokturk Dizi Indirici.lnk\") { Remove-Item \"$desktop\Gokturk Dizi Indirici.lnk\" -Force }"
echo [+] Masaustu kisayolu imha edildi.

:: 2. APPDATA Ayar Klasörünü Silme
if exist "%APPDATA%\GokturkMediaDownloader" (
    rd /s /q "%APPDATA%\GokturkMediaDownloader"
    echo [+] Kullanici ayarlari ve indirme pro filleri temizlendi.
)

:: 3. Kendi Klasörünü Silme Hilesi (Temp klasörüne zıplama)
if "%~dp0"=="%TEMP%\" goto :KlasoruUcur

:: Kendini Temp'e kopyala ve oradan tetikle
copy /y "%~f0" "%TEMP%\GokturkKaldir.bat" > nul
start "" "%TEMP%\GokturkKaldir.bat"
exit /b

:KlasoruUcur
:: Ana klasörün tamamen kapandığından emin olmak için 1 saniye bekle
timeout /t 1 /nobreak > nul

:: C:\DiziIndirici klasörünü tamamen sil
if exist "C:\DiziIndirici" (
    rd /s /q "C:\DiziIndirici"
    echo [+] Program dosyalari (C:\DiziIndirici) başarıyla silindi.
)

echo.
echo =====================================================
echo [✓] GOKTURK MEDYA ISTASYONU SISTEMDEN TEMIZLENDI!
echo =====================================================
echo.
echo Pencereyi kapattiginizda gecici dosyalar da silinecektir.
pause

:: Kendi kendini imha etme (Temp'teki dosyayı siler)
del "%TEMP%\GokturkKaldir.bat" & exit