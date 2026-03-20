"""
cost_cap.py — Middleware pre ochranu pred nekontrolovanými nákladmi

Sleduje denný počet queries a odhadovaný mesačný náklad.
Integruje sa do app.py PRED každým volaním LLM.

Odhad ceny: ~0.003 EUR per query (500 input + 300 output tokenov na Mistral small)
V lokálnom Ollama režime je cena 0, ale limit na počet queries stále platí
pre prípad verejného deployu.

Použitie:
    from cost_cap import check_and_increment

    cap = check_and_increment()
    if not cap["allowed"]:
        st.error(cap["reason"])
        st.stop()
"""

import json
import os
from datetime import date

from config import USAGE_FILE, DAILY_QUERY_LIMIT, MONTHLY_BUDGET_EUR

COST_PER_QUERY_EUR = 0.003  # odhad pre Mistral small API


def _load_usage() -> dict:
    if os.path.exists(USAGE_FILE):
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"daily": {}, "monthly": {}}


def _save_usage(usage: dict) -> None:
    os.makedirs(os.path.dirname(USAGE_FILE) if os.path.dirname(USAGE_FILE) else ".", exist_ok=True)
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(usage, f, indent=2)


def check_and_increment(
    daily_limit: int   = DAILY_QUERY_LIMIT,
    monthly_budget_eur: float = MONTHLY_BUDGET_EUR,
) -> dict:
    """
    Skontroluje limity a pri splnení podmienok inkrementuje počítadlá.

    Vracia:
        {"allowed": True,  "reason": "OK", "daily_used": int, "monthly_cost_eur": float}
        {"allowed": False, "reason": str}
    """
    usage  = _load_usage()
    today  = str(date.today())          # "2026-03-15"
    month  = today[:7]                  # "2026-03"

    daily_count   = usage["daily"].get(today, 0)
    monthly_count = usage["monthly"].get(month, 0)
    monthly_cost  = round(monthly_count * COST_PER_QUERY_EUR, 4)

    # Denný limit
    if daily_count >= daily_limit:
        return {
            "allowed": False,
            "reason": (
                f"Denný limit {daily_limit} otázok bol dosiahnutý. "
                "Skúste to prosím zajtra."
            ),
        }

    # Mesačný budget
    if monthly_cost >= monthly_budget_eur:
        return {
            "allowed": False,
            "reason": (
                f"Mesačný prevádzkový budget {monthly_budget_eur:.0f} € bol vyčerpaný. "
                "Systém bude obnovený na začiatku ďalšieho mesiaca."
            ),
        }

    # OK — inkrementuj
    usage["daily"][today]    = daily_count + 1
    usage["monthly"][month]  = monthly_count + 1
    _save_usage(usage)

    return {
        "allowed":           True,
        "reason":            "OK",
        "daily_used":        daily_count + 1,
        "monthly_cost_eur":  round((monthly_count + 1) * COST_PER_QUERY_EUR, 4),
    }


def get_stats() -> dict:
    """Vráti aktuálnu štatistiku bez zmeny počítadiel. Použiteľné v sidebar."""
    usage  = _load_usage()
    today  = str(date.today())
    month  = today[:7]

    daily_count   = usage["daily"].get(today, 0)
    monthly_count = usage["monthly"].get(month, 0)
    monthly_cost  = round(monthly_count * COST_PER_QUERY_EUR, 4)

    return {
        "daily_used":        daily_count,
        "daily_limit":       DAILY_QUERY_LIMIT,
        "monthly_queries":   monthly_count,
        "monthly_cost_eur":  monthly_cost,
        "monthly_budget_eur": MONTHLY_BUDGET_EUR,
    }
