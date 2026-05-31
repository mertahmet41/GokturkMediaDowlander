@echo off
chcp 65001 > nul
title Gokturk Kurulum Sihirbazi

echo =====================================================
echo    Dizi - Film Indirici Otomatik Kurulum Sihirbazi
echo =====================================================
echo.

set HEDEF_KLASOR=C:\DiziIndirici

echo [+] Program dosyalari Yerel Disk (C:) icerisine tasiniyor...
if not exist "%HEDEF_KLASOR%" mkdir "%HEDEF_KLASOR%"

:: Bulunduğu klasördeki her şeyi C:\DiziIndirici içine kopyalar
xcopy /E /I /Y "%~dp0*" "%HEDEF_KLASOR%\" > nul

echo.
echo [+] Gerekli Python kutuphaneleri kuruluyor...
python -m pip install -r "%HEDEF_KLASOR%\requirements.txt"

echo.
echo [+] Arka plan tarayici motoru (Playwright Chromium) kuruluyor...
python -m playwright install chromium

echo.
echo [+] Video birlestirme motoru (FFmpeg) kuruluyor...
echo [!] Lutfen gerekirse ekranda cikacak onaylari (Y/N) onaylayin.
winget install Gyan.FFmpeg --accept-source-agreements --accept-package-agreements

echo.
echo [+] Masaustu kisayolu olusturuluyor...
:: Windows diline (Türkçe Masaüstü / İngilizce Desktop) bakılmaksızın masaüstünü bulan komut
powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $shortcut = $wshell.CreateShortcut($desktop + '\Gokturk Dizi Indirici.lnk'); $shortcut.TargetPath = '%HEDEF_KLASOR%\calistir.bat'; $shortcut.WorkingDirectory = '%HEDEF_KLASOR%'; $shortcut.Save()"

echo.
echo =====================================================
echo [✓] Kurulum ve Tasima tamamlandi!
echo [!] Program %HEDEF_KLASOR% klasorune kuruldu.
echo [!] Masaustunuzdeki 'Gokturk Dizi Indirici' kisayolu ile baslatabilirsiniz.
echo.
echo [!] NOT: Islem bittikten sonra bu indirdiginiz ilk klasoru silebilirsiniz.
echo =====================================================
pause