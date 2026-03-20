"""
tests/debug_retrieval.py — Retrieval debug pre konkrétne otázky

Spustenie (z koreňa projektu):
    python tests/debug_retrieval.py

Skontroluje čo retrieval vracia pre TQ04/TQ05/TQ07 — kritické halucinujúce otázky.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag import retrieve

PROBLEMATIC = [
    ("TQ04", "Ako sa vypočíta výška dávky v nezamestnanosti?"),
    ("TQ05", "Ako dlho môžem poberať dávku v nezamestnanosti a aká je jej výška?"),
    ("TQ07", "Skončil som pracovný pomer dohodou — mám nárok na dávku v nezamestnanosti?"),
    ("TQ15", "Musím počas výpovednej doby chodiť do práce?"),
]

print("=" * 80)
print("RETRIEVAL DEBUG — čo dostáva LLM ako kontext")
print("=" * 80)

for qid, question in PROBLEMATIC:
    print(f"\n{'─'*80}")
    print(f"{qid}: {question}")
    print(f"{'─'*80}")

    chunks = retrieve(question, n_results=5)
    for i, c in enumerate(chunks, 1):
        meta = c["metadata"]
        print(f"\n[{i}] § {meta['paragraf']} — {meta['zakon']} [{meta.get('zakon_cislo','')}]  sim={c['similarity']:.2%}")
        print(f"    {c['text'][:400]}")
        if len(c['text']) > 400:
            print(f"    ...[+{len(c['text'])-400} znakov]")

    max_sim = max(c["similarity"] for c in chunks)
    print(f"\n  → max_similarity = {max_sim:.2%}  (MIN_SIMILARITY = 40%)")
    if max_sim < 0.40:
        print(f"  → GUARDRAIL by odmietol (pod prahom)")
    else:
        print(f"  → Prechádzá do LLM")

print(f"\n{'='*80}")
print("ZÁVER: ak §108/§105 chunks neobsahujú percentá → problém v indexácii alebo chunkovaní")
print("Riešenie: znížiť N_RESULTS threshold alebo re-indexovať §108/§105 ako samostatné chunks")
