"""
02_chunker.py — Parsing zákonov na paragrafy (chunky)

Slov-Lex HTML štruktúra (overená 15.3.2026):
  <div class="paragraf Skupina" id="paragraf-62">
    <div class="paragrafOznacenie">§ 62</div>
    <div class="paragrafNadpis">Výpovedná doba</div>
    <div class="odsek Skupina" id="paragraf-62.odsek-1">
      <div class="odsekOznacenie">(1)</div>
      <div class="text">Ak je daná výpoveď...</div>
    </div>
    ...
  </div>

Spustenie:
  python 02_chunker.py

Expected output:
  data/chunks.json — ~400-600 chunkov
"""

import json
import re
import os
import sys
from bs4 import BeautifulSoup
from config import ZAKONY, RAW_HTML_DIR, CHUNKS_FILE


def _extract_paragraphs(html_content: str, zakon_meta: dict) -> list[dict]:
    """
    Parsuje paragrafy pomocou natívnej HTML štruktúry Slov-Lex.
    Hľadá všetky <div id="paragraf-X"> kontajnery.
    """
    soup = BeautifulSoup(html_content, "lxml")
    chunks = []

    # Nájdi všetky div elementy ktorých id začína "paragraf-" ale nie "paragraf-X.nieco"
    # (chceme len hlavné kontajnery, nie sub-elementy)
    par_divs = soup.find_all("div", id=re.compile(r"^paragraf-[\da-z]+$"))

    for div in par_divs:
        par_id = div.get("id", "")  # napr. "paragraf-62"
        par_num = par_id.replace("paragraf-", "")  # napr. "62"

        # Čistý text celého paragrafu (vrátane všetkých odsekova)
        text = div.get_text(separator=" ", strip=True)
        # Normalizuj whitespace
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 20:
            continue  # prázdny alebo artefakt

        chunks.append({
            "id":               f"{zakon_meta['id']}_p{par_num}",
            "zakon":            zakon_meta["nazov"],
            "zakon_cislo":      zakon_meta["cislo"],
            "paragraf":         par_num,
            "text":             text,
            "url":              zakon_meta["url_portal"],
            "datum_ucinnosti":  zakon_meta["datum"],
        })

    return chunks


def _load_actual_dates() -> dict:
    log_path = "data/actual_dates.txt"
    dates = {}
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    dates[k] = v
    return dates


def main():
    print("=" * 60)
    print("Chunker — parsing zákonov na paragrafy")
    print("=" * 60)
    print()

    actual_dates = _load_actual_dates()
    all_chunks = []
    stats = {}

    for zakon in ZAKONY:
        html_path = f"{RAW_HTML_DIR}/ZZ_{zakon['rok']}_{zakon['cislo_num']}.html"

        if not os.path.exists(html_path):
            print(f"✗ Chýba: {html_path}")
            continue

        if zakon["id"] in actual_dates:
            zakon = {**zakon, "datum": actual_dates[zakon["id"]]}

        print(f"[{zakon['id']}] Parsovanie: {zakon['nazov']}")

        with open(html_path, encoding="utf-8") as f:
            html_content = f.read()

        chunks = _extract_paragraphs(html_content, zakon)
        stats[zakon["nazov"]] = len(chunks)
        all_chunks.extend(chunks)
        print(f"  → {len(chunks)} chunkov")

    print()
    print("─" * 40)
    print(f"CELKOM: {len(all_chunks)} chunkov")

    if len(all_chunks) == 0:
        print("✗ Žiadne chunky! Skontroluj HTML štruktúru.")
        sys.exit(1)

    os.makedirs("data", exist_ok=True)
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"✓ Uložené: {CHUNKS_FILE}")
    print()
    print("Štatistiky:")
    for nazov, count in stats.items():
        bar = "█" * min(count // 5, 40)
        print(f"  {nazov[:42]:<42} {count:>3} §§  {bar}")
    print()
    print("ĎALŠÍ KROK: python 03_indexer.py")


if __name__ == "__main__":
    main()
