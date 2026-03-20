"""
01_scraper.py — Stiahnutie konsolidovaných znení zákonov z static.slov-lex.sk

Čo robí:
  - Pre každý zákon v config.ZAKONY skúsi stiahnuť print HTML verziu
  - Automaticky skúša viacero dátumov (20260101, 20250401, 20250101...)
    lebo nie všetky zákony majú znenie práve k 2026-01-01
  - Uloží HTML do data/raw_html/ZZ_{rok}_{cislo}.html

Spustenie:
  python 01_scraper.py

Expected output:
  data/raw_html/ZZ_2001_311.html   (Zákonník práce)
  data/raw_html/ZZ_2004_5.html     (Zákon o službách zamestnanosti)
  ... atď pre všetkých 5 zákonov
"""

import requests
import os
import time
import sys
from config import ZAKONY, RAW_HTML_DIR

# Dátumy na vyskúšanie — od najnovšieho po staršie
# Slov-Lex ukladá znenia k dátumu nadobudnutia účinnosti poslednej zmeny.
# Ak 20260101 neexistuje, skúsime staršie dátumy.
FALLBACK_DATES = [
    "20260101",
    "20250901",
    "20250401",
    "20250101",
    "20241001",
    "20240101",
    "20230101",
]

BASE_URL = "https://static.slov-lex.sk/static/SK/ZZ/{rok}/{cislo}/{datum}.print.html"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SlovLex-PoC-Scraper/1.0; "
                  "open-source project; contact: belispav@gmail.com)",
}


def download_zakon(zakon: dict) -> bool:
    """
    Pokúsi sa stiahnuť zákon. Vracia True ak úspešne, False ak zlyhá.
    """
    os.makedirs(RAW_HTML_DIR, exist_ok=True)
    output_path = f"{RAW_HTML_DIR}/ZZ_{zakon['rok']}_{zakon['cislo_num']}.html"

    # Ak súbor už existuje, preskočíme (idempotentné správanie)
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"  ✓ Preskočený (už existuje, {size:,} B): {output_path}")
        return True

    # Skúšame dátumy od najnovšieho
    dates_to_try = [zakon["datum"]] + [d for d in FALLBACK_DATES if d != zakon["datum"]]

    for datum in dates_to_try:
        url = BASE_URL.format(rok=zakon["rok"], cislo=zakon["cislo_num"], datum=datum)
        print(f"  Skúšam: {url}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            print(f"  ✗ Sieťová chyba: {e}")
            continue

        if resp.status_code == 200 and len(resp.text) > 5000:
            # Základná kontrola — HTML musí mať aspoň 5 kB obsahu
            resp.encoding = "utf-8"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(resp.text)
            size = len(resp.text)
            print(f"  ✓ Stiahnuté k dátumu {datum}: {output_path} ({size:,} B)")
            # Uložíme skutočný dátum do konfig súboru pre referenciu
            _log_actual_date(zakon["id"], datum)
            return True
        elif resp.status_code == 404:
            print(f"  ✗ 404 pre dátum {datum}")
        else:
            print(f"  ✗ HTTP {resp.status_code}, veľkosť: {len(resp.text)} B")

        time.sleep(1)  # Slušný rate limiting

    return False


def _log_actual_date(zakon_id: str, datum: str):
    """Zapíše skutočný dátum do data/actual_dates.txt pre referenčné účely."""
    log_path = "data/actual_dates.txt"
    os.makedirs("data", exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{zakon_id}={datum}\n")


def main():
    print("=" * 60)
    print("Slov-Lex Scraper — PŽS Strata zamestnania")
    print("=" * 60)
    print()

    success_count = 0
    failed = []

    for zakon in ZAKONY:
        print(f"[{zakon['id']}] {zakon['nazov']} ({zakon['cislo']})")
        ok = download_zakon(zakon)
        if ok:
            success_count += 1
        else:
            failed.append(zakon["nazov"])
            print(f"  ✗✗ ZLYHANIE — zákon sa nepodarilo stiahnuť!")
        print()
        time.sleep(2)  # Rate limiting medzi zákonmi

    print("=" * 60)
    print(f"Výsledok: {success_count}/{len(ZAKONY)} zákonov stiahnutých")

    if failed:
        print(f"\nZLYHALI ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")
        print()
        print("RIEŠENIE pre zlyhané zákony:")
        print("  1. Manuálne otvor URL v prehliadači (viď config.py → url_portal)")
        print("  2. Skopíruj správny dátum z URL a uprav config.py → datum")
        print("  3. Alebo: stiahni PDF a ulož ako data/raw_html/ZZ_{rok}_{cislo}.pdf")
        print("     (02_chunker.py vie čítať aj PDF cez pymupdf)")
        sys.exit(1)
    else:
        print("\n✓ Všetky zákony stiahnuté. Ďalší krok: python 02_chunker.py")


if __name__ == "__main__":
    main()
