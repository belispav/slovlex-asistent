"""
tests/retest_critical.py — Re-test kritických otázok s novým promptom v2

Testuje iba TQ07, TQ15 (nesprávne) + TQ02, TQ06, TQ08, TQ17 (čiastočné).
Šetrí tokeny — netestuje všetky.

Spustenie: python tests/retest_critical.py
"""
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from rag import ask

RETEST_IDS = {
    "TQ02": "Aká je výpovedná doba ak pracujem menej ako 1 rok?",
    "TQ06": "Čo môžem robiť ak si myslím, že moja výpoveď bola neplatná?",
    "TQ07": "Skončil som pracovný pomer dohodou — mám nárok na dávku v nezamestnanosti?",
    "TQ08": "Z akých dôvodov môže zamestnávateľ dať zamestnancovi výpoveď?",
    "TQ15": "Musím počas výpovednej doby chodiť do práce?",
    "TQ17": "Čo dostanem od zamestnávateľa počas prvých dní práceneschopnosti?",
    "TQ20": "Na aké dokumenty a platby mám nárok pri skončení pracovného pomeru?",
}

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("RE-TEST kritických otázok — prompt v2 + filter prechodných §")
print("=" * 70)

results = []
for qid, question in RETEST_IDS.items():
    print(f"\n[{qid}] {question}")
    t0 = time.time()
    r = ask(question)
    elapsed = round(time.time() - t0, 1)

    print(f"  → {r['answer'][:250]}{'...' if len(r['answer']) > 250 else ''}")
    print(f"  sim={r['similarity_max']:.2%}  time={elapsed}s  below={r['below_threshold']}")

    results.append({
        "id": qid,
        "question": question,
        "answer": r["answer"],
        "sim": r["similarity_max"],
        "time_s": elapsed,
        "below": r["below_threshold"],
        "sources": " | ".join(r["sources"]) if r["sources"] else "",
    })

    # Rate limit buffer
    time.sleep(3)

out = RESULTS_DIR / "retest_critical.json"
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✓ Výsledky uložené: {out}")
print("\nManual check needed:")
print("  TQ07: odpoveď má obsahovať 'áno, máte nárok' + §104 ZSP + 730 dní")
print("  TQ15: odpoveď má obsahovať 'musíte pracovať' alebo 'povinnosti trvajú'")
print("  TQ17: odpoveď má obsahovať '25%' a '55%' alebo 'DNV'")
