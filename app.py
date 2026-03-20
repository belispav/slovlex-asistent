"""
app.py — Streamlit UI: AI Asistent pre stratu zamestnania

Spustenie:
    streamlit run app.py

Prerekvizity:
    - python 04_rag.py "test" musí vrátiť odpoveď (Ollama alebo Mistral API)
    - chroma_db/ musí existovať s dátami z 03_indexer.py
"""

import os
import streamlit as st

from rag import ask          # noqa: E402  (rag importuje config, model atď.)
from cost_cap import check_and_increment, get_stats
from config import LLM_MODE, OLLAMA_MODEL, MISTRAL_MODEL, N_RESULTS, MIN_SIMILARITY

# ── Konfigurácia stránky ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Asistent — Strata zamestnania",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.title("🏛️ AI Asistent — Strata zamestnania")
st.caption("Proof of Concept · Pavel Beliš pre MIRRI SR · Open Source · MIT licencia")

st.warning(
    "⚠️ **Dôležité upozornenie:** Tento systém je technologický demonstrátor (PoC). "
    "**Neposkytuje záväzné právne poradenstvo.** "
    "Pre oficiálne informácie kontaktujte úrad práce, Sociálnu poisťovňu alebo advokáta. "
    "Odpovede sú generované umelou inteligenciou a môžu obsahovať nepresnosti.",
    icon="⚠️",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("ℹ️ O projekte")
    st.markdown("""
**Čo je toto?**
Open-source AI asistent demonštrujúci koncept konverzačného rozhrania
pre prioritné životné situácie podľa NKIVS 2026–2030 (Fínsky model).

**Zákony v databáze:**
- Zákonník práce (311/2001)
- Zákon o službách zamestnanosti (5/2004)
- Zákon o sociálnom poistení (461/2003)
- Zákon o hmotnej núdzi (417/2013)
- Zákon o náhrade príjmu pri PN (462/2003)

**Technológie:**
Mistral 7B · BGE-M3 · ChromaDB · Streamlit
    """)

    st.divider()

    # Technické info
    st.caption("**Konfigurácia:**")
    st.caption(f"LLM: `{OLLAMA_MODEL if LLM_MODE == 'local' else MISTRAL_MODEL}`")
    st.caption(f"Režim: `{LLM_MODE}`")
    st.caption(f"Retrieval: top-{N_RESULTS} chunks, min. relevancia {MIN_SIMILARITY:.0%}")

    st.divider()

    # Usage stats
    stats = get_stats()
    st.caption("**Využitie dnes:**")
    st.caption(f"{stats['daily_used']} / {stats['daily_limit']} otázok")
    if LLM_MODE == "api":
        st.caption(f"Mesačný náklad: ~{stats['monthly_cost_eur']:.3f} € / {stats['monthly_budget_eur']:.0f} €")

    st.divider()
    st.caption("GitHub: github.com/pavelbelis/slovlex-asistent _(bude zverejnené)_")
    st.markdown("[Kontakt](mailto:belispav@gmail.com)")

# ── Vzorové otázky ────────────────────────────────────────────────────────────
SAMPLE_QUESTIONS = [
    "Aká je výpovedná doba ak pracujem u zamestnávateľa 3 roky?",
    "Kedy sa musím zaregistrovať na úrade práce po výpovedi?",
    "Koľko je dávka v nezamestnanosti a ako dlho sa vypláca?",
    "Čo mám robiť ak ma zamestnávateľ vyhodil z dňa na deň bez dôvodu?",
    "Mám nárok na podporu ak som dal výpoveď sám?",
]

if not st.session_state.get("messages"):
    st.markdown("**Vzorové otázky na vyskúšanie:**")
    cols = st.columns(1)
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"sample_{q[:20]}"):
            st.session_state["prefill"] = q
            st.rerun()

# ── Chat história ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Použité zdroje z legislatívy"):
                for source in msg["sources"]:
                    st.markdown(f"- {source}")

# ── Input ─────────────────────────────────────────────────────────────────────
# Prefill z tlačidla vzorových otázok
default_input = st.session_state.pop("prefill", "")

prompt = st.chat_input(
    "Opýtajte sa na čokoľvek ohľadom straty zamestnania...",
    key="chat_input",
) or (default_input if default_input else None)

if prompt:
    # ── Cost cap check ────────────────────────────────────────────────────────
    cap = check_and_increment()
    if not cap["allowed"]:
        st.error(f"🚫 {cap['reason']}")
        st.stop()

    # ── Zobraziť otázku ───────────────────────────────────────────────────────
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ── Generovať odpoveď ─────────────────────────────────────────────────────
    with st.chat_message("assistant"):
        with st.spinner("Prehľadávam legislatívu..."):
            result = ask(prompt)

        st.markdown(result["answer"])
        st.caption("⚠️ Nie je to právne poradenstvo. Pre záväzné informácie kontaktujte úrad práce alebo advokáta.")

        if result["sources"]:
            with st.expander(f"📎 Použité zdroje ({result['chunks_used']} paragrafov)"):
                for source in result["sources"]:
                    st.markdown(f"- {source}")
        elif result.get("below_threshold"):
            st.caption(
                f"ℹ️ Žiadny relevantný paragraf nenájdený "
                f"(max. zhoda: {result['similarity_max']:.0%} < {MIN_SIMILARITY:.0%} prah)."
            )

    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    })

# ── Reset tlačidlo ────────────────────────────────────────────────────────────
if st.session_state.messages:
    if st.button("🗑️ Vymazať históriu", type="secondary"):
        st.session_state.messages = []
        st.rerun()
