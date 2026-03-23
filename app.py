"""
app.py — Streamlit UI: AI Asistent pre stratu zamestnania
"""

import streamlit as st
import streamlit.components.v1 as components
import time

from rag import ask
from cost_cap import check_and_increment, get_stats
from config import LLM_MODE, OLLAMA_MODEL, MISTRAL_MODEL, N_RESULTS, MIN_SIMILARITY

st.set_page_config(
    page_title="AI Asistent — Strata zamestnania",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Lexend:wght@300;400;500;600;700&display=swap');

/* ── Skryť Streamlit chrome ── */
#MainMenu, header[data-testid="stHeader"], footer,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Skryť Material Icons text (face, smart_toy, arrow_right) ── */
/* Avatary chat správ — úplne skryté, nie zmenšené */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] {
    display: none !important;
}
/* Kontajner avatara — zrušiť medzeru ktorú zaberá */
[data-testid="stChatMessage"] > div:first-child {
    display: none !important;
}
/* Skryť Material Icons text (stIconMaterial je skutočný testid Streamlit) */
[data-testid="stIconMaterial"] {
    display: none !important;
}
/* Záloha pre rôzne varianty */
span[translate="no"][color] {
    display: none !important;
}

/* ── Základy ── */
html, body, [class*="css"], * {
    font-family: 'Inter', 'Lexend', sans-serif !important;
}
h1, h2, h3, .hero-title {
    font-family: 'Lexend', 'Inter', sans-serif !important;
}
.stApp {
    background: #050E21;
    color: #ffffff;
}

/* ── Dekoratívny gradient v pozadí ── */
.stApp::before {
    content: '';
    position: fixed;
    top: -200px;
    right: -200px;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}
.stApp::after {
    content: '';
    position: fixed;
    bottom: -150px;
    left: -150px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(59,130,246,0.05) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ── Hlavný obsah ── */
.main .block-container {
    padding-top: 2.5rem;
    padding-bottom: 6rem;
    max-width: 800px;
}

/* ── Hero header ── */
.hero-header {
    text-align: center;
    padding: 2rem 0 1.5rem 0;
    position: relative;
}
.hero-header::after {
    content: '';
    display: block;
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, #06B6D4, #3B82F6);
    margin: 1rem auto 0 auto;
    border-radius: 2px;
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
    margin: 0;
    line-height: 1.2;
    font-family: 'Lexend', sans-serif !important;
}
.hero-title span {
    background: linear-gradient(135deg, #06B6D4, #67E8F9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    color: rgba(186,220,255,0.55);
    font-size: 0.82rem;
    margin-top: 0.5rem;
    letter-spacing: 0.3px;
    font-family: 'Inter', sans-serif !important;
}

/* ── Shield Badge Disclaimer ── */
.shield-badge {
    background: rgba(6,182,212,0.05);
    border: 1px solid rgba(6,182,212,0.22);
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 2rem;
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
}
.shield-icon {
    font-size: 1.4rem;
    flex-shrink: 0;
    margin-top: 0.05rem;
    filter: drop-shadow(0 0 6px rgba(6,182,212,0.4));
}
.shield-text {
    font-size: 0.82rem;
    color: rgba(186,220,255,0.75);
    line-height: 1.6;
    font-family: 'Inter', sans-serif;
}
.shield-text strong {
    color: rgba(186,220,255,0.95);
    font-weight: 600;
    display: block;
    margin-bottom: 0.2rem;
    font-size: 0.85rem;
    letter-spacing: 0.2px;
}

/* ── Section label ── */
.section-label {
    color: rgba(186,220,255,0.4);
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 0.8rem;
    margin-top: 0.5rem;
    font-family: 'Inter', sans-serif;
}

/* ── Bento Grid ── */
.bento-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 0.75rem;
    margin-bottom: 1.2rem;
}
.bento-tile {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(6,182,212,0.18);
    border-radius: 12px;
    padding: 1rem 0.9rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}
.bento-tile:hover {
    background: rgba(6,182,212,0.08);
    border-color: rgba(6,182,212,0.45);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(6,182,212,0.1);
}
.bento-tile-icon {
    font-size: 1.3rem;
}
.bento-tile-category {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #06B6D4;
    font-family: 'Inter', sans-serif;
}
.bento-tile-title {
    font-size: 0.83rem;
    font-weight: 600;
    color: rgba(255,255,255,0.9);
    line-height: 1.3;
    font-family: 'Inter', sans-serif;
}
.bento-tile-desc {
    font-size: 0.74rem;
    color: rgba(186,220,255,0.55);
    line-height: 1.4;
    font-family: 'Inter', sans-serif;
}

/* ── Sample question buttons (fallback pre mobile) ── */
.stButton > button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(6,182,212,0.2) !important;
    color: rgba(186,220,255,0.85) !important;
    border-radius: 10px !important;
    font-size: 0.87rem !important;
    padding: 0.65rem 1.1rem !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    background: rgba(6,182,212,0.1) !important;
    border-color: rgba(6,182,212,0.5) !important;
    color: #ffffff !important;
    transform: translateX(3px) !important;
}

/* ── Chat input ── */
[data-testid="stBottom"] {
    background: #050E21 !important;
    border-top: 1px solid rgba(6,182,212,0.12) !important;
    padding: 1rem 0 !important;
}
[data-testid="stBottom"] > div {
    background: #050E21 !important;
}
.stChatInputContainer, [data-testid="stChatInputContainer"],
div[class*="chatInputContainer"] {
    background: #050E21 !important;
    border: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] {
    background: transparent !important;
    border: none !important;
}
[data-testid="stChatInput"] > div {
    background: rgba(10,20,50,0.9) !important;
    border: 1.5px solid rgba(6,182,212,0.4) !important;
    border-radius: 14px !important;
    box-shadow: 0 0 20px rgba(6,182,212,0.08) !important;
    padding: 0.2rem !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    color: #ffffff !important;
    font-size: 1rem !important;
    min-height: 56px !important;
    padding: 0.9rem 1rem !important;
    line-height: 1.5 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: rgba(186,220,255,0.35) !important;
    font-size: 0.95rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    outline: none !important;
    box-shadow: none !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: #06B6D4 !important;
    box-shadow: 0 0 0 3px rgba(6,182,212,0.15), 0 0 25px rgba(6,182,212,0.1) !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #06B6D4, #0891B2) !important;
    border: none !important;
    border-radius: 10px !important;
    margin: 6px !important;
    color: #ffffff !important;
}
[data-testid="stChatInput"] button:hover {
    background: linear-gradient(135deg, #22D3EE, #06B6D4) !important;
}

/* ── Progress steps ── */
.progress-steps {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 0.8rem 1rem;
    background: rgba(6,182,212,0.04);
    border: 1px solid rgba(6,182,212,0.15);
    border-radius: 10px;
    margin: 0.5rem 0;
}
.progress-step {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 0.82rem;
    font-family: 'Inter', sans-serif;
    color: rgba(186,220,255,0.5);
    transition: color 0.3s ease;
}
.progress-step.active {
    color: rgba(186,220,255,0.95);
}
.progress-step.done {
    color: rgba(6,182,212,0.8);
}
.step-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: rgba(186,220,255,0.2);
    flex-shrink: 0;
    transition: background 0.3s ease;
}
.progress-step.active .step-dot {
    background: #06B6D4;
    box-shadow: 0 0 8px rgba(6,182,212,0.6);
    animation: pulse-dot 1s ease-in-out infinite;
}
.progress-step.done .step-dot {
    background: rgba(6,182,212,0.6);
}
@keyframes pulse-dot {
    0%, 100% { box-shadow: 0 0 4px rgba(6,182,212,0.6); }
    50% { box-shadow: 0 0 12px rgba(6,182,212,0.9); }
}

/* ── Chat správy ── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 14px !important;
    margin-bottom: 0.8rem !important;
    padding: 0.3rem 0.5rem !important;
    backdrop-filter: blur(4px) !important;
}
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 2px solid #06B6D4 !important;
    background: rgba(6,182,212,0.03) !important;
}
/* ── Text odpovede — plná čitateľnosť ── */
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] div {
    color: #E8F0FF !important;
}
[data-testid="stChatMessage"] strong {
    color: #ffffff !important;
}
/* Otázka používateľa — mierne odlíšená */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) div {
    color: rgba(186,220,255,0.75) !important;
}

/* ── Disclaimer pod odpoveďou ── */
.answer-disclaimer {
    color: rgba(186,220,255,0.38);
    font-size: 0.73rem;
    margin-top: 0.6rem;
    font-style: italic;
    font-family: 'Inter', sans-serif;
}

/* ── Expander (zdroje) ── */
.stExpander {
    border: 1px solid rgba(6,182,212,0.18) !important;
    border-radius: 10px !important;
    background: rgba(6,182,212,0.03) !important;
    margin-top: 0.5rem !important;
}
.stExpander summary, .stExpander summary p {
    color: rgba(6,182,212,0.8) !important;
    font-size: 0.83rem !important;
}
.stExpander [data-testid="stExpanderDetails"] {
    color: rgba(186,220,255,0.7) !important;
    font-size: 0.83rem !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070F26 0%, #0A1432 100%) !important;
    border-right: 1px solid rgba(6,182,212,0.12) !important;
}
[data-testid="stSidebar"] .block-container {
    padding-top: 2rem !important;
}
[data-testid="stSidebar"] * {
    color: rgba(186,220,255,0.8) !important;
}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #ffffff !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] a {
    color: #06B6D4 !important;
    text-decoration: none !important;
}
[data-testid="stSidebar"] a:hover { color: #67E8F9 !important; }
hr { border-color: rgba(6,182,212,0.12) !important; }

/* ── Štatistické boxy v sidebar ── */
.stat-box {
    background: rgba(6,182,212,0.06);
    border: 1px solid rgba(6,182,212,0.15);
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    margin: 0.3rem 0;
    font-size: 0.8rem;
    color: rgba(186,220,255,0.7);
    font-family: 'Inter', sans-serif;
}
.stat-box strong {
    color: #06B6D4;
    font-size: 1.1rem;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(6,182,212,0.25); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── JS fix: prepisanie Streamlit svetlosivých input wrapperov ─────────────────
components.html("""
<script>
function fixInputColors() {
    const doc = window.parent.document;
    const textarea = doc.querySelector('textarea[placeholder*="otázku"]');
    if (!textarea) return;
    textarea.style.setProperty('background', 'rgba(10,20,50,0.95)', 'important');
    textarea.style.setProperty('color', '#ffffff', 'important');
    let el = textarea.parentElement;
    for (let i = 0; i < 6; i++) {
        if (!el) break;
        const bg = window.parent.getComputedStyle(el).backgroundColor;
        if (bg === 'rgb(240, 242, 246)' || bg === 'rgb(255, 255, 255)') {
            el.style.setProperty('background-color', 'rgba(10,20,50,0.95)', 'important');
            el.style.setProperty('border', 'none', 'important');
            el.style.setProperty('box-shadow', 'none', 'important');
        }
        el = el.parentElement;
    }
}
fixInputColors();
setInterval(fixInputColors, 300);
</script>
""", height=0)

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
    <div class="hero-title">🏛️ AI Asistent — <span>Strata zamestnania</span></div>
    <div class="hero-sub">Open-source PoC · Pavel Beliš · Technologický demonštrátor · MIT licencia</div>
</div>
""", unsafe_allow_html=True)

# ── Shield Badge Disclaimer ───────────────────────────────────────────────────
st.markdown("""
<div class="shield-badge">
    <div class="shield-icon">🛡️</div>
    <div class="shield-text">
        <strong>Technologický demonštrátor — nie právne poradenstvo</strong>
        Odpovede generuje AI na základe konsolidovaných znení zákonov zo Slov-Lex
        (databáza k 1.&nbsp;1.&nbsp;2026, Zákon o&nbsp;službách zamestnanosti k 1.&nbsp;11.&nbsp;2025).
        Systém nie&nbsp;je klasifikovaný, auditovaný ani schválený podľa Nariadenia (EÚ)&nbsp;2024/1689
        (AI&nbsp;Act). Nie&nbsp;je určený na nasadenie orgánmi verejnej moci bez splnenia regulačných
        požiadaviek. Pre záväzné stanovisko kontaktujte úrad práce, Sociálnu poisťovňu alebo advokáta.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏛️ O projekte")
    st.markdown("""
Európska únia od členských štátov požaduje, aby občan dostal odpoveď
na svoju životnú situáciu **na jednom mieste** — bez preskakovania medzi úradmi.

Tento asistent ukazuje, ako by to mohlo vyzerať pre situáciu
**straty zamestnania** na Slovensku.
    """)

    st.divider()
    st.markdown("**Pokryté zákony:**")
    st.markdown("""
- Zákonník práce (311/2001)
- Zákon o službách zamestnanosti (5/2004)
- Zákon o sociálnom poistení (461/2003)
- Zákon o hmotnej núdzi (417/2013)
- Zákon o náhrade príjmu pri PN (462/2003)
    """)

    st.divider()
    stats = get_stats()
    st.markdown(f"""
<div class="stat-box">Otázky dnes: <strong>{stats['daily_used']}</strong> / {stats['daily_limit']}</div>
""", unsafe_allow_html=True)

    st.divider()
    st.markdown("[pavelbelis.sk](https://pavelbelis.sk) · [GitHub](https://github.com/belispav/slovlex-asistent)")

# ── Bento grid + vzorové otázky ───────────────────────────────────────────────
BENTO_TILES = [
    {
        "icon": "💰",
        "category": "Finančná stabilita",
        "title": "Dávka v nezamestnanosti",
        "desc": "Výška, trvanie, podmienky nároku",
        "question": "Koľko je dávka v nezamestnanosti a ako dlho sa vypláca?",
    },
    {
        "icon": "⚖️",
        "category": "Legislatívne práva",
        "title": "Výpovedná doba",
        "desc": "Zákonné nároky pri ukončení pracovného pomeru",
        "question": "Aká je výpovedná doba ak pracujem u zamestnávateľa 3 roky?",
    },
    {
        "icon": "🗺️",
        "category": "Trh práce",
        "title": "Registrácia na ÚPSVaR",
        "desc": "Kde, kedy a ako sa zaregistrovať",
        "question": "Kedy sa musím zaregistrovať na úrade práce po výpovedi?",
    },
]

EXTRA_QUESTIONS = [
    "Čo mám robiť ak ma zamestnávateľ vyhodil z dňa na deň bez dôvodu?",
    "Mám nárok na podporu ak som dal výpoveď sám?",
]

if not st.session_state.get("messages"):
    st.markdown('<div style="color:rgba(186,220,255,0.4);font-size:0.7rem;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:0.8rem;margin-top:0.5rem;font-family:Inter,sans-serif;">Vyskúšajte napríklad</div>', unsafe_allow_html=True)

    # Bento grid — čistý HTML + inline CSS cez components.html (vyhýba sa Streamlit HTML sanitizácii)
    tiles_html = ""
    for t in BENTO_TILES:
        tiles_html += f"""
  <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(6,182,212,0.18);border-radius:12px;padding:1rem 0.9rem;display:flex;flex-direction:column;gap:0.3rem;">
    <div style="font-size:1.4rem;line-height:1;">{t['icon']}</div>
    <div style="font-size:0.61rem;font-weight:600;letter-spacing:1px;text-transform:uppercase;color:#06B6D4;font-family:Inter,sans-serif;margin-top:0.25rem;">{t['category']}</div>
    <div style="font-size:0.84rem;font-weight:600;color:rgba(255,255,255,0.9);line-height:1.3;font-family:Inter,sans-serif;">{t['title']}</div>
    <div style="font-size:0.72rem;color:rgba(186,220,255,0.55);line-height:1.4;font-family:Inter,sans-serif;">{t['desc']}</div>
  </div>"""

    bento_html = f"""
<style>
  body {{ margin:0; padding:0; background:transparent; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.75rem; }}
</style>
<div class="grid">{tiles_html}</div>"""

    components.html(bento_html, height=150)

    # Tlačidlá pod bento (funkčné Streamlit buttons)
    cols = st.columns(3)
    for i, tile in enumerate(BENTO_TILES):
        with cols[i]:
            if st.button(f"➜ {tile['title']}", key=f"bento_{i}", use_container_width=True):
                st.session_state["prefill"] = tile["question"]
                st.rerun()

    st.markdown('<div style="height:0.3rem"></div>', unsafe_allow_html=True)

    # Extra otázky
    for q in EXTRA_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"extra_{q[:20]}"):
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
default_input = st.session_state.pop("prefill", "")

prompt = st.chat_input(
    "Napíšte svoju otázku o strate zamestnania...",
    key="chat_input",
) or (default_input if default_input else None)

# ── Multi-step progress helper ────────────────────────────────────────────────
PROGRESS_STEPS = [
    "Pripájam sa k legislatívnej databáze SR",
    "Skenujem relevantné paragrafy",
    "Analyzujem faktický kontext otázky",
    "Formulujem odpoveď",
]

def show_progress(container, active_step: int, done_steps: list[int]):
    steps_html = ""
    for i, label in enumerate(PROGRESS_STEPS):
        if i in done_steps:
            dot_style = "width:6px;height:6px;border-radius:50%;background:rgba(6,182,212,0.6);flex-shrink:0;"
            text_color = "rgba(6,182,212,0.8)"
            prefix = "✓ "
        elif i == active_step:
            dot_style = "width:6px;height:6px;border-radius:50%;background:#06B6D4;flex-shrink:0;box-shadow:0 0 8px rgba(6,182,212,0.8);"
            text_color = "rgba(186,220,255,0.95)"
            prefix = ""
        else:
            dot_style = "width:6px;height:6px;border-radius:50%;background:rgba(186,220,255,0.15);flex-shrink:0;"
            text_color = "rgba(186,220,255,0.35)"
            prefix = ""
        steps_html += f'<div style="display:flex;align-items:center;gap:0.6rem;font-size:0.82rem;font-family:Inter,sans-serif;color:{text_color};"><div style="{dot_style}"></div>{prefix}{label}</div>\n'
    container.markdown(
        f'<div style="display:flex;flex-direction:column;gap:0.4rem;padding:0.8rem 1rem;background:rgba(6,182,212,0.04);border:1px solid rgba(6,182,212,0.15);border-radius:10px;margin:0.5rem 0;">{steps_html}</div>',
        unsafe_allow_html=True
    )

# ── Spracovanie otázky ────────────────────────────────────────────────────────
if prompt:
    cap = check_and_increment()
    if not cap["allowed"]:
        st.error(f"🚫 {cap['reason']}")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        progress_placeholder = st.empty()

        # Krok 0
        show_progress(progress_placeholder, active_step=0, done_steps=[])
        time.sleep(0.4)

        # Krok 1
        show_progress(progress_placeholder, active_step=1, done_steps=[0])
        time.sleep(0.3)

        # Krok 2 — tu prebieha skutočná RAG operácia
        show_progress(progress_placeholder, active_step=2, done_steps=[0, 1])
        result = ask(prompt)

        # Krok 3
        show_progress(progress_placeholder, active_step=3, done_steps=[0, 1, 2])
        time.sleep(0.25)

        # Vymazať progress, zobraziť výsledok
        progress_placeholder.empty()

        st.markdown(result["answer"])
        st.markdown('<div class="answer-disclaimer">Výstup AI demonštrátora — nie právne poradenstvo. Legislatívna báza k 1. 1. 2026. Overte si informácie na úrade práce alebo u advokáta.</div>', unsafe_allow_html=True)

        if result["sources"]:
            with st.expander(f"📎 Použité zdroje ({result['chunks_used']} paragrafov)"):
                for source in result["sources"]:
                    st.markdown(f"- {source}")
        elif result.get("below_threshold"):
            st.caption(f"ℹ️ Nenašiel som relevantný paragraf (max. zhoda: {result['similarity_max']:.0%}).")

    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    })

# ── Reset ─────────────────────────────────────────────────────────────────────
if st.session_state.messages:
    if st.button("🗑️ Vymazať históriu", type="secondary"):
        st.session_state.messages = []
        st.rerun()
