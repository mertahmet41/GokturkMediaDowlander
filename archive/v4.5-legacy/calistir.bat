@echo off
chcp 65001 > nul
title Gokturk Dizi Indirici
color 0C

echo.
echo  ██████╗ ██╗   ██╗    ██╗    ██╗██╗   ██╗███╗   ███╗██████╗ ██╗   ██╗███████╗
echo  ██╔══██╗╚██╗ ██╔╝    ██║    ██║██║   ██║████╗ ████║██╔══██╗██║   ██║██╔════╝
echo  ██████╔╝ ╚████╔╝     ██║ █╗ ██║██║   ██║██╔████╔██║██████╔╝██║   ██║███████╗
echo  ██╔══██╗  ╚██╔╝      ██║███╗██║██║   ██║██║╚██╔╝██║██╔═══╝ ██║   ██║╚════██║
echo  ██████╔╝   ██║       ╚███╔███╔╝╚██████╔╝██║ ╚═╝ ██║██║     ╚██████╔╝███████║
echo  ╚═════╝    ╚═╝        ╚══╝╚══╝  ╚═════╝ ╚═╝     ╚═╝╚═╝      ╚═════╝ ╚══════╝
echo.
echo  =============================================================================
echo                     Siber Indirme Istasyonu Baslatiliyor...
echo  =============================================================================
echo.

:: Python kodundaki ekran temizleme (cls) yaziyi aninda silmesin diye 3 saniye bekletiyoruz.
timeout /t 3 /nobreak > nul

:: Programi calistiriyoruz
python otuken.py

:: Eger program hata verip kapanirsa ekranda kalip hatayi gostermesi icin pause ekliyoruz
pause