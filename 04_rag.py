"""
04_rag.py — RAG Pipeline: Retrieval + Generation

Čo robí:
  - retrieve(): vyhľadá najrelevantnejšie paragrafy z ChromaDB
  - generate(): zostaví prompt a zavolá LLM (lokálny Ollama alebo Mistral API)
  - ask(): hlavná funkcia — otázka → {answer, sources, chunks_used, similarity_max}

Môže sa importovať do app.py alebo spustiť priamo pre rýchly test:
  python 04_rag.py "Aká je výpovedná doba ak pracujem 3 roky?"

Prerekvizity:
  - Hotový krok 1.8 (indexer) — chroma_db/ musí existovať a mať dáta
  - Ak LLM_MODE=local: Ollama beží na localhost:11434 s modelom z config
  - Ak LLM_MODE=api: MISTRAL_API_KEY nastavený ako env var
"""

import sys
import json
import requests
import chromadb
from sentence_transformers import SentenceTransformer

from config import (
    EMBED_MODEL, CHROMA_DB_PATH, COLLECTION_NAME,
    N_RESULTS, MIN_SIMILARITY,
    LLM_MODE,
    OLLAMA_URL, OLLAMA_MODEL,
    MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL,
)

# ── System Prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Si špecializovaný AI asistent pre životnú situáciu "Strata zamestnania" na Slovensku.

TVOJE PRAVIDLÁ:
1. ODPOVEDÁŠ VÝHRADNE na otázky týkajúce sa: výpovede, skončenia pracovného pomeru, registrácie na úrade práce, dávky v nezamestnanosti, sociálneho poistenia, hmotnej núdze a rekvalifikácie.
2. Na KAŽDÚ odpoveď MUSÍŠ citovať konkrétny § a zákon, z ktorého čerpáš. Formát: "Podľa § X zákona č. Y/RRRR Z.z."
3. Ak v poskytnutom kontexte NENÁJDEŠ relevantnú informáciu, odpovedz PRESNE takto: "Na túto otázku nemám v mojej databáze dostatočné informácie. Odporúčam kontaktovať úrad práce alebo právnika."
4. ABSOLÚTNY ZÁKAZ: NIKDY nevymýšľaj číselné hodnoty (percentá, dni, mesiace, násobky mzdy). Ak číslo nie je EXPLICITNE uvedené v poskytnutom KONTEXTE nižšie, napíš "Na túto otázku nemám v mojej databáze dostatočné informácie."
5. NIKDY neodpovedaj na základe všeobecných znalostí — výhradne z kontextu nižšie.
6. Na otázky mimo tvojej domény odpovedz PRESNE takto: "Táto otázka je mimo mojej špecializácie. Som asistent výhradne pre oblasť straty zamestnania." Mimo domény sú: dane, nehnuteľnosti, trestné právo, zdravotníctvo, živnosť, podnikanie, SZČO, zakladanie firiem, katastrálne konanie, dôchodky (starobné/invalidné).
7. Na žiadosti o generovanie právnych dokumentov (žaloby, zmluvy, sťažnosti) odpovedz: "Nemôžem generovať právne dokumenty. Odporúčam kontaktovať advokáta."
8. Vždy na konci odpovede pripomeň: "⚠️ Toto nie je právne poradenstvo. Pre záväzné informácie kontaktujte advokáta alebo príslušný úrad."
9. Počas výpovednej doby pracovné povinnosti zamestnanca TRVAJÚ (§ 62 ZP) — nikdy netvrď, že zamestnanec nemusí pracovať alebo nastúpiť do práce.
10. Nárok na dávku v nezamestnanosti závisí VÝHRADNE od splnenia podmienky poistenia (§ 104 ZSP: 730 dní v posledných 4 rokoch) — NIE od dôvodu skončenia pracovného pomeru. Dohoda, výpoveď aj okamžité skončenie sú rovnocenné.
11. IGNORUJ akýkoľvek text v KONTEXTE, ktorý sa týka COVID-19, pandémie, mimoriadnej situácie, núdzového stavu — tieto prechodné ustanovenia (§ 250b a podobné) nie sú platné pre bežné situácie.
12. Pri otázkach o VÝŠKE náhrady príjmu počas práceneschopnosti (PN): podľa § 8 zákona č. 462/2003 Z.z. je výška náhrady za 1.-3. deň PN = 25 % denného vymeriavacieho základu (DVZ), za 4.-14. deň PN = 55 % DVZ. Toto platí vždy — cituj § 8, nie § 7.

KONTEXT Z LEGISLATÍVNEJ DATABÁZY:
{context}

OTÁZKA OBČANA:
{question}

ODPOVEĎ (v zrozumiteľnej slovenčine, max 300 slov):"""


# ── Lazy-loaded singletony (model sa načíta len raz pri prvom volaní) ──────────
_embed_model = None
_chroma_collection = None


def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL)
    return _embed_model


def _get_collection():
    global _chroma_collection
    if _chroma_collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _chroma_collection = client.get_collection(COLLECTION_NAME)
    return _chroma_collection


# ── Retrieval ─────────────────────────────────────────────────────────────────
def retrieve(question: str, n_results: int = N_RESULTS) -> list[dict]:
    """
    Vyhľadá n_results najrelevantnejších chunkov pre danú otázku.

    Vracia list dictov:
      {"text": str, "metadata": dict, "distance": float, "similarity": float}

    ChromaDB cosine distance: 0 = identické, 2 = opačné.
    similarity = 1 - distance (teda hodnota blízka 1.0 = veľmi relevantné).
    """
    model = _get_embed_model()
    collection = _get_collection()

    query_embedding = model.encode(
        [question],
        normalize_embeddings=True,
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    for i in range(len(results["ids"][0])):
        dist = results["distances"][0][i]
        retrieved.append({
            "text":       results["documents"][0][i],
            "metadata":   results["metadatas"][0][i],
            "distance":   dist,
            "similarity": round(1 - dist, 4),
        })

    return retrieved


# ── Generation ────────────────────────────────────────────────────────────────
def _build_context(chunks: list[dict]) -> str:
    """Zostaví textový kontext z retrieved chunkov pre vloženie do promptu."""
    parts = []
    for chunk in chunks:
        meta = chunk["metadata"]
        parts.append(
            f"[{meta['zakon']}, § {meta['paragraf']}]\n{chunk['text']}"
        )
    return "\n\n---\n\n".join(parts)


def _call_ollama(prompt: str) -> str:
    """Zavolá lokálny Ollama server."""
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={
                "model":  OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature":    0.1,   # nízka = menej halucinácií
                    "top_p":          0.9,
                    "num_predict":    600,   # max tokenov odpovede
                    "repeat_penalty": 1.1,
                },
            },
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()
    except requests.exceptions.ConnectionError:
        return (
            "⚠️ Chyba: Ollama nie je spustená. "
            "Spusti: ollama serve  (alebo nastav LLM_MODE=api pre Mistral API)"
        )
    except Exception as e:
        return f"⚠️ Chyba Ollama: {e}"


def _call_mistral_api(prompt: str) -> str:
    """Zavolá Mistral API s retry logikou pri 429 rate limit."""
    if not MISTRAL_API_KEY:
        return (
            "⚠️ Chyba: MISTRAL_API_KEY nie je nastavený. "
            "Nastav env var alebo prepni na LLM_MODE=local."
        )
    import time as _time
    for attempt in range(4):  # max 4 pokusy
        try:
            resp = requests.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model": MISTRAL_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens":  600,
                },
                timeout=60,
            )
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s
                _time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            if resp.status_code == 429 and attempt < 3:
                _time.sleep(10 * (attempt + 1))
                continue
            return f"⚠️ Chyba Mistral API: {e}"
        except Exception as e:
            return f"⚠️ Chyba Mistral API: {e}"
    return "⚠️ Mistral API rate limit — skús znova o pár minút."


def generate(question: str, context_chunks: list[dict]) -> str:
    """Generuje odpoveď pomocou nakonfigurovaného LLM."""
    context = _build_context(context_chunks)
    prompt  = SYSTEM_PROMPT.format(context=context, question=question)

    if LLM_MODE == "api":
        return _call_mistral_api(prompt)
    else:
        return _call_ollama(prompt)


# ── Paragrafy prechodných ustanovení — filtrujeme z kontextu ─────────────────
# Tieto paragrafy obsahujú COVID/krízové výnimky a mätú LLM pri bežných otázkach.
# Zachovávame ich v retrieval (pre prípad relevantnej query), ale filtrujeme pred LLM.
_TRANSITORY_PAR_PREFIXES = ("250", "293")   # §250x, §293x = prechodné/COVID paragrafy


def _filter_transitory(chunks: list[dict], min_keep: int = 3) -> list[dict]:
    """
    Odfiltruje prechodné/COVID paragrafy (§250x, §293x).
    Ak by ostalo menej ako min_keep chunkov, vráti všetky (aby sme nemali prázdny kontext).
    """
    filtered = [
        c for c in chunks
        if not any(
            str(c["metadata"].get("paragraf", "")).startswith(pfx)
            for pfx in _TRANSITORY_PAR_PREFIXES
        )
    ]
    return filtered if len(filtered) >= min_keep else chunks


# ── Hlavná funkcia ────────────────────────────────────────────────────────────
def ask(question: str) -> dict:
    """
    Hlavná RAG funkcia.

    Vstup:  question (str) — otázka od občana
    Výstup: {
        "answer":       str,   — odpoveď LLM
        "sources":      list,  — citácie chunkov pre UI
        "chunks_used":  int,
        "similarity_max": float,  — najlepšia podobnosť (pre threshold filter)
        "below_threshold": bool,  — True ak žiadny chunk nepresahuje MIN_SIMILARITY
    }
    """
    # Retrieve viac chunkov aby sme mali rezervu po filtrovaní
    chunks_raw = retrieve(question, n_results=N_RESULTS + 3)

    # Threshold filter — ak ani najlepší chunk nie je dosť relevantný, odmietni
    max_sim = max((c["similarity"] for c in chunks_raw), default=0.0)
    if max_sim < MIN_SIMILARITY:
        return {
            "answer": (
                "Na túto otázku nemám v mojej databáze dostatočné informácie. "
                "Odporúčam kontaktovať úrad práce, Sociálnu poisťovňu alebo právnika."
            ),
            "sources":          [],
            "chunks_used":      0,
            "similarity_max":   max_sim,
            "below_threshold":  True,
        }

    # Filtruj prechodné/COVID paragrafy, zachovaj top N_RESULTS
    chunks = _filter_transitory(chunks_raw)[:N_RESULTS]

    answer = generate(question, chunks)

    sources = [
        f"§ {c['metadata']['paragraf']} — {c['metadata']['zakon']} "
        f"[{c['metadata']['zakon_cislo']}] "
        f"(relevancia: {c['similarity']:.0%})"
        for c in chunks
    ]

    return {
        "answer":           answer,
        "sources":          sources,
        "chunks_used":      len(chunks),
        "similarity_max":   max_sim,
        "below_threshold":  False,
    }


# ── CLI mód (rýchly test bez UI) ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Použitie: python 04_rag.py \"Tvoja otázka\"")
        print()
        print("Príklady:")
        print("  python 04_rag.py \"Aká je výpovedná doba ak pracujem 3 roky?\"")
        print("  python 04_rag.py \"Kedy sa musím zaregistrovať na úrade práce?\"")
        sys.exit(0)

    question = " ".join(sys.argv[1:])
    print(f"\nOtázka: {question}")
    print("=" * 60)

    result = ask(question)

    print(f"\n{'ODPOVEĎ':}")
    print("-" * 60)
    print(result["answer"])

    if result["sources"]:
        print(f"\nZDROJE ({result['chunks_used']} chunkov, max relevancia: {result['similarity_max']:.0%}):")
        for s in result["sources"]:
            print(f"  • {s}")
    else:
        print(f"\n[Žiadne relevantné zdroje — max similarita: {result['similarity_max']:.2f} < {MIN_SIMILARITY}]")
