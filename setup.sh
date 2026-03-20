#!/bin/bash
# setup.sh — Krok 1.1: Inštalácia prostredia (macOS / Linux)
# Spusti: bash setup.sh

set -e

echo "============================================================"
echo " Slov-Lex PoC — Inštalácia prostredia"
echo "============================================================"
echo ""

# Kontrola Python verzie
python3 --version >/dev/null 2>&1 || {
    echo "CHYBA: python3 nie je nainštalovaný"
    exit 1
}

echo "[1/3] Vytváram Python virtual environment..."
python3 -m venv venv
echo "      OK: venv/ vytvorený"

echo "[2/3] Aktivujem venv..."
source venv/bin/activate

echo "[3/3] Inštalujem balíčky (môže trvať 5-10 minút)..."
pip install --upgrade pip -q
pip install -r requirements.txt

echo ""
echo "============================================================"
echo " Hotovo! Prostredie je pripravené."
echo "============================================================"
echo ""
echo "ĎALŠÍ KROKY:"
echo "  1. Aktivuj venv pri každom novom termináli:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Krok 1.2 — Overenie URL (otvor v prehliadači):"
echo "     https://static.slov-lex.sk/static/SK/ZZ/2001/311/20260101.print.html"
echo "     https://static.slov-lex.sk/static/SK/ZZ/2004/5/20260101.print.html"
echo "     https://static.slov-lex.sk/static/SK/ZZ/2003/461/20260101.print.html"
echo "     https://static.slov-lex.sk/static/SK/ZZ/2013/417/20260101.print.html"
echo "     https://static.slov-lex.sk/static/SK/ZZ/2003/462/20260101.print.html"
echo ""
echo "  3. Krok 1.3:"
echo "     python 01_scraper.py"
