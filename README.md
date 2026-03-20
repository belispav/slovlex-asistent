# Slov-Lex AI Asistent — Strata zamestnania

**Proof of Concept · Open Source · MIT licencia**

Konverzačný AI asistent pre prioritnú životnú situáciu „Strata zamestnania" podľa NKIVS 2026–2030 (Fínsky model). Demonštruje, ako môže štátna správa poskytovať občanom okamžité, presné a zdrojované odpovede na právne otázky bez ľudského operátora.

> ⚠️ **Dôležité:** Tento systém je technologický demonstrátor (PoC). Neposkytuje záväzné právne poradenstvo. Pre oficiálne informácie kontaktujte úrad práce, Sociálnu poisťovňu alebo advokáta.

---

## Výsledky

| Metrika | Výsledok |
|---|---|
| Accuracy (20 testovacích otázok) | **92% (17/20)** |
| Halucinácie | **0** |
| Guardrail spoľahlivosť (10 out-of-scope otázok) | **9/10** |
| LLM | Mistral API `mistral-small-latest` |
| Embedding model | `BAAI/bge-m3` |
| Vector DB | ChromaDB |

---

## Architektúra

```
slov-lex.sk (HTML)
      ↓ 01_scraper.py
data/raw_html/*.html
      ↓ 02_chunker.py
data/chunks.json (~500 chunkov, 1 § = 1 chunk)
      ↓ 03_indexer.py (BAAI/bge-m3 embeddings)
chroma_db/ (ChromaDB vector store)
      ↓ 04_rag.py (retrieve + generate)
app.py (Streamlit UI)
```

**RAG pipeline:**
1. Query → BGE-M3 embedding
2. ChromaDB similarity search (top-5 chunks, prah 0.40)
3. Ak max relevancia < prah → odmietnutie bez generovania
4. Mistral API generovanie s povinnou citáciou §§
5. Guardrails: out-of-scope otázky odmietnuté v system prompte

---

## Zákony v databáze

| Zákon | Číslo |
|---|---|
| Zákonník práce | 311/2001 Z.z. |
| Zákon o službách zamestnanosti | 5/2004 Z.z. |
| Zákon o sociálnom poistení | 461/2003 Z.z. |
| Zákon o pomoci v hmotnej núdzi | 417/2013 Z.z. |
| Zákon o náhrade príjmu pri dočasnej PN | 462/2003 Z.z. |

Dáta pochádzajú z verejne prístupného `static.slov-lex.sk` (konsolidované znenia zákonov).

---

## Inštalácia (lokálne, Windows/Linux/Mac)

### Prerekvizity

- Python 3.10+
- Mistral API kľúč (zadarmo na [console.mistral.ai](https://console.mistral.ai)) **alebo** Ollama s `mistral:7b-instruct-v0.3-q4_K_M`

### Kroky

```bash
# 1. Klonovanie repozitára
git clone https://github.com/pavelbelis/slovlex-asistent.git
cd slovlex-asistent

# 2. Inštalácia závislostí
pip install -r requirements.txt

# 3. Konfigurácia
cp .env.example .env
# Editujte .env — nastavte MISTRAL_API_KEY a LLM_MODE=api

# 4. Stiahnutie zákonov
python 01_scraper.py

# 5. Chunking
python 02_chunker.py

# 6. Indexácia (embedding ~10 min pri prvom spustení)
python 03_indexer.py

# 7. Test RAG pipeline
python 04_rag.py "Aká je výpovedná doba ak pracujem u zamestnávateľa 3 roky?"

# 8. Spustenie UI
streamlit run app.py
```

### .env konfigurácia

```env
# Mistral API (pre produkčný deploy)
LLM_MODE=api
MISTRAL_API_KEY=your_key_here

# Alebo lokálny Ollama
# LLM_MODE=local

# Limity
DAILY_QUERY_LIMIT=200
MONTHLY_BUDGET_EUR=20.0
```

---

## Deploy na VPS (Hetzner CX22)

```bash
# Ubuntu 22.04, Python 3.10+
git clone https://github.com/pavelbelis/slovlex-asistent.git
cd slovlex-asistent
pip install -r requirements.txt

# Nastaviť .env s MISTRAL_API_KEY a LLM_MODE=api
# Pre-indexovať dáta: python 01_scraper.py && python 02_chunker.py && python 03_indexer.py

# Spustenie na pozadí
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

Pre produkčné nasadenie odporúčam nginx reverse proxy + systemd service.

---

## Štruktúra projektu

```
slovlex-asistent/
├── 01_scraper.py        # Stiahnutie zákonov zo slov-lex.sk
├── 02_chunker.py        # Parsing HTML na paragrafy (§)
├── 03_indexer.py        # BGE-M3 embedding + ChromaDB import
├── 04_rag.py            # RAG pipeline (retrieve + generate)
├── app.py               # Streamlit chatové UI
├── config.py            # Centrálna konfigurácia
├── cost_cap.py          # Daily/monthly budget ochrana
├── rag.py               # Import alias pre 04_rag.py
├── requirements.txt
├── .env.example
├── data/
│   ├── raw_html/        # Stiahnuté HTML zákony
│   └── chunks.json      # Sparsované paragrafy
├── chroma_db/           # Vector store (po indexácii)
└── tests/               # Testovacie skripty a výsledky
```

---

## Kontext: NKIVS 2026–2030

Projekt demonštruje technickú realizovateľnosť konceptu z Národnej koncepcie informatizácie verejnej správy 2026–2030 — konkrétne prioritnú životnú situáciu č. 1 „Strata zamestnania". Fínsky model e-governmentu predpokladá, že občan dostane odpoveď na svoju situáciu na jednom mieste, bez preskakovania medzi úradmi.

**Autor:** Pavel Beliš
**Kontakt:** belispav@gmail.com
**Licencia:** MIT

---

## Licencia

MIT License — viď [LICENSE](LICENSE)
