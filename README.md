# Slov-Lex AI Asistent — Strata zamestnania

**Proof of Concept · Open Source · MIT licencia**

Technológia na sprístupnenie právnych informácií občanom bežnou rečou existuje, je dostupná a funkčná. Tento open-source demonstrátor to dokazuje na prioritnej životnej situácii „Strata zamestnania" podľa NKIVS 2026–2030.

Občan sa opýta bežnou rečou — systém prehľadá 5 slovenských zákonov a odpovie s presnými citáciami (§, odsek, písmeno). Ak otázka presahuje scope, odmietne odpovedať. Žiadne vymýšľanie.

Technické riešenie je pritom tá jednoduchšia časť. Náročnejšia — a kľúčová — je pripraviť ľudí a procesy v organizáciách na to, aby takéto nástroje vedeli zadefinovať, prijať a efektívne využívať.

> ⚠️ **Dôležité:** Tento systém je technologický demonstrátor (PoC). Nie je klasifikovaný, auditovaný ani schválený podľa AI Act (2024/1689). Neposkytuje záväzné právne poradenstvo. Pre oficiálne informácie kontaktujte úrad práce, Sociálnu poisťovňu alebo advokáta.

---

## Výsledky

| Metrika | Výsledok |
|---|---|
| Accuracy (ilustratívny test, 20 otázok) | **92% (17/20)** |
| Halucinácie | **0** |
| Guardrail spoľahlivosť (10 out-of-scope otázok) | **9/10** |
| LLM | Mistral API `mistral-small-latest` |
| Embedding model | `BAAI/bge-m3` |
| Vector DB | ChromaDB |

> ⚠️ Uvedené výsledky sú z **ilustratívneho testu na 20 otázkach** — nie z validačnej metodiky podľa čl. 9 AI Act. Pre produkčné nasadenie by bolo potrebné nezávislé testovanie na reprezentatívnej vzorke vrátane adversariálnych vstupov.

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

Dáta pochádzajú z verejne prístupného `static.slov-lex.sk`. Konsolidované znenia sú k **1. 1. 2026** (Zákon o službách zamestnanosti k 1. 11. 2025). Databáza nie je automaticky aktualizovaná pri novelizáciách.

---

## Inštalácia (lokálne, Windows/Linux/Mac)

### Prerekvizity

- Python 3.10+
- Mistral API kľúč (zadarmo na [console.mistral.ai](https://console.mistral.ai)) **alebo** Ollama s `mistral:7b-instruct-v0.3-q4_K_M`

### Kroky

```bash
# 1. Klonovanie repozitára
git clone https://github.com/belispav/slovlex-asistent.git
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
git clone https://github.com/belispav/slovlex-asistent.git
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

Projekt demonštruje, čo je dnes technicky možné — konkrétne na prioritnej životnej situácii č. 1 „Strata zamestnania" z NKIVS 2026–2030. Fínsky model e-governmentu predpokladá, že občan dostane odpoveď na svoju situáciu na jednom mieste, bez preskakovania medzi úradmi.

Jeden človek, open-source stack, niekoľko dní práce. Princíp RAG pipeline nad legislatívou je technicky aplikovateľný na ďalšie životné situácie definované v NKIVS — samotná technológia je však len jedna vrstva. Produkčné nasadenie vyžaduje klasifikáciu rizika (AI Act), compliance procesy, integráciu s existujúcou infraštruktúrou a organizačnú pripravenosť.

Tento PoC **nie je integrovaný** so slovensko.sk, ÚPVS, KAV, ID.GOV.SK ani s backendovými systémami OVM. Demonštruje výhradne technickú feasibilitu RAG pipeline nad slovenskou legislatívou, nie naplnenie cieľov NKIVS ako celku.

---

## Regulačný kontext (AI Act, GDPR)

Tento projekt je **technologický demonštrátor (PoC)** — nie produkt určený na nasadenie v produkčnom prostredí orgánov verejnej moci.

**AI Act (Nariadenie EÚ 2024/1689):**
- Systémy poskytujúce informácie v oblasti zamestnanosti a sociálnej pomoci občanom v zraniteľnej situácii sa podľa čl. 6 a Prílohy III potenciálne klasifikujú ako **vysokorizikové**.
- Akýkoľvek nasadzovateľ (čl. 3 bod 4) — vrátane OVM — by musel pred produkčným nasadením splniť povinnosti podľa čl. 6, 9, 11, 26, 27 AI Act, vrátane technickej dokumentácie (Príloha IV), FRIA (čl. 27) a registrácie (čl. 60).
- Open-source kód pod MIT licenciou neurčuje zodpovednosť za výstupy systému nasadeného tretími stranami.

**GDPR (Nariadenie EÚ 2016/679):**
- Pri nasadení s interakciou s občanmi by bola povinná DPIA podľa čl. 35 GDPR.
- Aktuálne demo **nespracúva osobné údaje** — otázky sa neukladajú, neprofilujú, neprenášajú.

**FRIA — Fundamental Rights Impact Assessment (čl. 27 AI Act):**
- Nasadzovateľ vysokorizikového AI systému vo verejnom sektore je povinný vykonať FRIA **pred nasadením** — ide o samostatnú požiadavku oddelenú od DPIA (GDPR).
- Tento PoC nie je nasadený orgánom verejnej moci, preto FRIA nie je aplikovateľná. Pri produkčnom nasadení OVM by bola povinná.

**Zákon č. 69/2018 Z.z. o kybernetickej bezpečnosti:**
- Pri produkčnom nasadení OVM by bola potrebná analýza supply chain a politického rizika dodávateľov (§ 20).

**Supply chain — pôvod komponentov:**
- **BAAI/bge-m3** (embedding model) — pochádza z Beijing Academy of Artificial Intelligence (BAAI), Čína. Pri nasadení v kontexte OVM by bol relevantný § 20 zákona 69/2018 (analýza politického rizika dodávateľa z tretej krajiny). V tomto PoC model beží lokálne a nespracúva osobné údaje — slúži výhradne na vektorovú podobnosť textu zákonov.
- **ChromaDB** — open-source vektorová databáza (Apache 2.0 licencia), beží lokálne.
- **Streamlit** — open-source UI framework (Apache 2.0 licencia), Snowflake Inc., USA.
- **Mistral API** — komerčný LLM poskytovateľ, Mistral AI, Francúzsko (EÚ). Pri OVM nasadení by bola potrebná zmluva so sprostredkovateľom podľa čl. 28 GDPR a overenie jurisdikcie spracovania dát.

Autor si je vedomý regulačného rámca. Tento PoC slúži ako vstup do diskusie o referenčnej architektúre, nie ako hotový produkt na nasadenie.

---

## Často kladené regulačné otázky

**Prečo je systém verejne prístupný, ak nie je klasifikovaný podľa AI Act?**
Systém je technologický demonštrátor (PoC) s prominentným disclaimerom v UI. Slúži na demonštráciu technickej feasibility RAG pipeline, nie na poskytovanie záväzných informácií. UI explicitne odkazuje na kompetentné orgány (ÚPSVaR, Sociálna poisťovňa) ako autoritatívne zdroje.

**Čo ak občan zadá osobné údaje do otázky?**
Systém nie je navrhnutý na spracovanie osobných údajov. Otázky sa neukladajú na strane servera. V produkčnom režime (Mistral API) sa text otázky posiela na API Mistral AI (Francúzsko, EÚ). Pre OVM nasadenie by bola potrebná zmluva so sprostredkovateľom (čl. 28 GDPR) a prípadne technické opatrenia na filtrovanie PII pred odoslaním na API.

**Prečo nie je implementovaný mechanizmus automatickej aktualizácie zákonov?**
PoC demonštruje RAG pipeline, nie produkčný systém s lifecycle managementom. Automatická aktualizácia by vyžadovala monitoring novelizácií na Slov-Lex, reindexáciu a regresnú validáciu — to presahuje scope jednorázového demonštrátora. Dátum platnosti zákonov je uvedený v UI aj v README.

**Kto nesie zodpovednosť, ak niekto nasadí tento kód v produkčnom prostredí?**
Podľa čl. 26 AI Act nesie zodpovednosť **nasadzovateľ** (deployer), nie autor open-source kódu. MIT licencia explicitne vylučuje záruku. Akýkoľvek nasadzovateľ — vrátane OVM — musí pred produkčným nasadením vykonať vlastnú klasifikáciu rizika, FRIA (čl. 27), DPIA (čl. 35 GDPR) a splniť požiadavky čl. 6, 9, 11, 14 AI Act.

**Prečo nie je adresovaná integrácia s KAV (Konsolidovaná analytická vrstva)?**
KAV je súčasťou SP3 NKIVS (Dátová infraštruktúra, 120M EUR) a jej referenčná architektúra nie je k aprílu 2026 verejne špecifikovaná. Tento PoC demonštruje izolovaný RAG pipeline — analýza integrácie s KAV bude relevantná, keď bude dostupná špecifikácia API a dátových rozhraní KAV.

---

**Autor:** Pavel Beliš
**Kontakt:** belispav@gmail.com
**Licencia:** MIT

---

## Licencia

MIT License — viď [LICENSE](LICENSE)
