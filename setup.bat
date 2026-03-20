@echo off
REM setup.bat — Krok 1.1: Inštalácia prostredia (Windows)
REM Spusti toto v príkazovom riadku (cmd) v priečinku slovlex-asistent/

echo ============================================================
echo  Slov-Lex PoC — Inštalácia prostredia
echo ============================================================
echo.

REM Vytvorenie virtual environment
echo [1/3] Vytváram Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo CHYBA: Python nie je nainštalovaný alebo nie je v PATH
    echo Stiahni Python 3.11+ z https://python.org
    pause
    exit /b 1
)
echo       OK: venv/ vytvorený

REM Aktivácia venv
echo [2/3] Aktivujem venv...
call venv\Scripts\activate.bat

REM Inštalácia balíčkov
echo [3/3] Inštalujem balíčky (môže trvať 5-10 minút)...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo CHYBA: Inštalácia zlyhala
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Hotovo! Prostredie je pripravené.
echo ============================================================
echo.
echo ĎALŠÍ KROKY:
echo   1. Aktivuj venv pri každom novom okne cmd:
echo      venv\Scripts\activate
echo.
echo   2. Krok 1.2 — Overenie URL:
echo      Otvor tieto URL v prehliadači a skontroluj či sa načítajú:
echo      https://static.slov-lex.sk/static/SK/ZZ/2001/311/20260101.print.html
echo      https://static.slov-lex.sk/static/SK/ZZ/2004/5/20260101.print.html
echo      https://static.slov-lex.sk/static/SK/ZZ/2003/461/20260101.print.html
echo      https://static.slov-lex.sk/static/SK/ZZ/2013/417/20260101.print.html
echo      https://static.slov-lex.sk/static/SK/ZZ/2003/462/20260101.print.html
echo.
echo      Ak niektorá URL vrátila 404:
echo        - Zisti správny dátum z portálu slov-lex.sk
echo        - Uprav "datum" pre daný zákon v config.py
echo.
echo   3. Krok 1.3 — Stiahnutie zákonov:
echo      python 01_scraper.py
echo.
pause
