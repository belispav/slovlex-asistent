"""
config.py — Centrálna konfigurácia projektu
Všetky hodnoty sa dajú prepísať cez environment variables (.env súbor alebo shell export).
"""
import os
from pathlib import Path

# ── Načítaj .env súbor ak existuje ────────────────────────────────────────────
_env_file = Path(__file__).parent / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

# ── LLM REŽIM ─────────────────────────────────────────────────────────────────
# "local"  → Ollama bežiaci na tvojom PC (na vývoj)
# "api"    → Mistral API (na produkčný deploy na VPS)
LLM_MODE = os.getenv("LLM_MODE", "local")

# ── MISTRAL API (pre deploy) ───────────────────────────────────────────────────
MISTRAL_API_KEY   = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL     = "mistral-small-latest"
MISTRAL_API_URL   = "https://api.mistral.ai/v1/chat/completions"

# ── OLLAMA (lokálny vývoj) ─────────────────────────────────────────────────────
OLLAMA_URL        = "http://localhost:11434/api/generate"
OLLAMA_MODEL      = "mistral:7b-instruct-v0.3-q4_K_M"

# ── EMBEDDING ──────────────────────────────────────────────────────────────────
EMBED_MODEL       = "BAAI/bge-m3"          # najlepší multilingual model
CHROMA_DB_PATH    = "./chroma_db"
COLLECTION_NAME   = "strata_zamestnania"

# ── RETRIEVAL ──────────────────────────────────────────────────────────────────
N_RESULTS         = 5                      # počet chunkov na query
MIN_SIMILARITY    = 0.40                   # pod týmto prahom = "neviem odpovedať"
                                           # (ChromaDB distance: 0=identické, 2=opačné;
                                           #  pre cosine: relevantný = distance < 0.6,
                                           #  čiže similarity = 1 - distance > 0.40)

# ── COST CAP ───────────────────────────────────────────────────────────────────
DAILY_QUERY_LIMIT   = int(os.getenv("DAILY_QUERY_LIMIT",   "200"))
MONTHLY_BUDGET_EUR  = float(os.getenv("MONTHLY_BUDGET_EUR", "20.0"))

# ── DÁTA ───────────────────────────────────────────────────────────────────────
RAW_HTML_DIR  = "data/raw_html"
CHUNKS_FILE   = "data/chunks.json"
USAGE_FILE    = "data/usage.json"

# ── ZÁKONY NA STIAHNUTIE ───────────────────────────────────────────────────────
# Každý zákon má: id, nazov, rok, cislo, datum (konsolidované znenie k tomuto dátumu)
# POZOR: datum treba skontrolovať na slov-lex.sk — vždy použiť posledné platné znenie.
ZAKONY = [
    {
        "id":     "zp",
        "nazov":  "Zákonník práce",
        "cislo":  "311/2001",
        "rok":    2001,
        "cislo_num": 311,
        "datum":  "20260101",   # ← overiť krokom 1.2!
        "url_portal": "https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2001/311/",
    },
    {
        "id":     "sluzby_zam",
        "nazov":  "Zákon o službách zamestnanosti",
        "cislo":  "5/2004",
        "rok":    2004,
        "cislo_num": 5,
        "datum":  "20251101",
        "url_portal": "https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2004/5/",
    },
    {
        "id":     "soc_poist",
        "nazov":  "Zákon o sociálnom poistení",
        "cislo":  "461/2003",
        "rok":    2003,
        "cislo_num": 461,
        "datum":  "20260101",
        "url_portal": "https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2003/461/",
    },
    {
        "id":     "hmotna_nudza",
        "nazov":  "Zákon o pomoci v hmotnej núdzi",
        "cislo":  "417/2013",
        "rok":    2013,
        "cislo_num": 417,
        "datum":  "20260101",
        "url_portal": "https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2013/417/",
    },
    {
        "id":     "nahrada_pn",
        "nazov":  "Zákon o náhrade príjmu pri dočasnej PN",
        "cislo":  "462/2003",
        "rok":    2003,
        "cislo_num": 462,
        "datum":  "20260101",
        "url_portal": "https://www.slov-lex.sk/pravne-predpisy/SK/ZZ/2003/462/",
    },
]
