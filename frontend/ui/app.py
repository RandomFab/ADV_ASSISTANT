# backend/src/ui/app.py
import streamlit as st
import requests
import json
from datetime import datetime

# ─────────────────────────────────────────
# Configuration de la page
# ─────────────────────────────────────────
st.set_page_config(
    page_title="SteelBot — Assistant ADV",
    page_icon="🏭",
    layout="wide",         # Utilise toute la largeur — indispensable pour le panneau latéral
    initial_sidebar_state="expanded",
)

API_URL = "http://127.0.0.1:8001"

# ─────────────────────────────────────────
# CSS — Style sobre et professionnel
# ─────────────────────────────────────────
st.markdown("""
<style>
    /* Police générale */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', system-ui, sans-serif;
    }

    /* Titre principal */
    .steelbot-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        border-left: 4px solid #e94560;
    }
    .steelbot-title {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .steelbot-subtitle {
        color: #a0aec0;
        font-size: 0.9rem;
        margin: 0.3rem 0 0 0;
    }

    /* Messages du chat */
    .chat-message {
        padding: 1rem 1.2rem;
        border-radius: 10px;
        margin-bottom: 0.8rem;
        line-height: 1.6;
    }
    .user-message {
        background: #e8f4fd;
        border-left: 3px solid #3498db;
        color: #1a1a2e;
    }
    .bot-message {
        background: #f8f9fa;
        border-left: 3px solid #e94560;
        color: #2d3748;
    }

    /* Badge outils */
    .tool-badge {
        display: inline-block;
        background: #0f3460;
        color: #e2e8f0;
        font-size: 0.75rem;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        margin: 0.2rem;
        font-family: 'Courier New', monospace;
    }

    /* Statut */
    .status-ok { color: #38a169; font-weight: 600; }
    .status-ko { color: #e53e3e; font-weight: 600; }

    /* Boutons questions exemples */
    .stButton > button {
        width: 100%;
        text-align: left;
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        color: #2d3748;
        padding: 0.5rem 0.8rem;
        font-size: 0.85rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #edf2f7;
        border-color: #e94560;
        color: #1a1a2e;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# Initialisation du session_state
# ─────────────────────────────────────────
# session_state persiste entre les rechargements de page.
# Sans ça, l'historique des messages disparaît à chaque interaction.
if "messages" not in st.session_state:
    st.session_state.messages = []          # [{role, content, tools_called, latency_ms}]
if "question_from_button" not in st.session_state:
    st.session_state.question_from_button = None


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────
def check_api_health() -> dict:
    """Vérifie que l'API est up et retourne le statut."""
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            return {"ok": True, "data": r.json()}
    except Exception:
        pass
    return {"ok": False, "data": None}


def call_chat(question: str) -> dict:
    """Envoie une question à l'API et retourne la réponse structurée."""
    try:
        r = requests.post(
            f"{API_URL}/chat",
            json={"question": question},
            timeout=60,     # L'agent peut prendre jusqu'à ~20s sur une question complexe
        )
        r.raise_for_status()
        return {"ok": True, "data": r.json()}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "L'agent a mis trop de temps à répondre (timeout 60s)."}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "Impossible de joindre l'API. Est-elle démarrée sur le port 8001 ?"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────
# Sidebar — Statut + Raisonnement + Exemples
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏭 SteelBot")
    st.markdown("*Assistant ADV — Transformation métallurgique*")
    st.divider()

    # Statut de l'API
    st.markdown("### 📡 Statut système")
    health = check_api_health()
    if health["ok"]:
        st.markdown('<span class="status-ok">● API en ligne</span>', unsafe_allow_html=True)
        if health["data"] and health["data"].get("agent") == "ready":
            st.markdown('<span class="status-ok">● Agent prêt</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-ko">● Agent non initialisé</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-ko">● API hors ligne</span>', unsafe_allow_html=True)
        st.caption("Démarrer l'API : `uvicorn src.api.main:app --port 8001`")

    st.divider()

    # Questions exemples — boutons cliquables pour la démo
    st.markdown("### 💡 Questions exemples")
    st.caption("Cliquez pour pré-remplir la question")

    questions_exemples = [
        "Où en est la commande CMD-2024-0002 ?",
        "Fais-moi un résumé complet du client Verdier",
        "On a du coil inox 304 en stock ?",
        "Quelles sont les réclamations ouvertes du client Lefebvre ?",
        "Quelle est l'estimation de livraison pour CMD-2023-0081 ?",
    ]

    for q in questions_exemples:
        if st.button(q, key=f"btn_{q[:20]}"):
            st.session_state.question_from_button = q

    st.divider()

    # Panneau raisonnement — affiché après chaque réponse de l'agent
    st.markdown("### 🔍 Raisonnement de l'agent")
    st.caption("Outils MCP appelés lors de la dernière réponse")

    if st.session_state.messages:
        last_bot_msg = next(
            (m for m in reversed(st.session_state.messages) if m["role"] == "assistant"),
            None
        )
        if last_bot_msg and last_bot_msg.get("tools_called"):
            for tool in last_bot_msg["tools_called"]:
                st.markdown(f'<span class="tool-badge">🔧 {tool}</span>', unsafe_allow_html=True)
            if last_bot_msg.get("latency_ms"):
                st.caption(f"⏱ Temps de réponse agent : {last_bot_msg['latency_ms']} ms")
        else:
            st.caption("Aucun outil appelé pour le moment.")

    # Bouton reset conversation
    st.divider()
    if st.button("🗑 Effacer la conversation", type="secondary"):
        st.session_state.messages = []
        st.session_state.question_from_button = None
        st.rerun()


# ─────────────────────────────────────────
# Zone principale — En-tête + Chat
# ─────────────────────────────────────────
st.markdown("""
<div class="steelbot-header">
    <p class="steelbot-title">🏭 SteelBot</p>
    <p class="steelbot-subtitle">Assistant IA pour l'Administration des Ventes · Transformation métallurgique</p>
</div>
""", unsafe_allow_html=True)

# Affichage de l'historique des messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="chat-message user-message">👤 <strong>Vous</strong><br>{msg["content"]}</div>',
            unsafe_allow_html=True
        )
    else:
        # Réponse de l'agent
        tools_html = ""
        if msg.get("tools_called"):
            tools_html = "<br><small style='color:#718096'>Outils utilisés : " + \
                         " ".join(f'<span class="tool-badge">{t}</span>' for t in msg["tools_called"]) + \
                         "</small>"
        st.markdown(
            f'<div class="chat-message bot-message">🤖 <strong>SteelBot</strong><br>{msg["content"]}{tools_html}</div>',
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────
# Input utilisateur
# ─────────────────────────────────────────
# Gestion du pré-remplissage depuis les boutons exemples
default_value = st.session_state.question_from_button or ""
if st.session_state.question_from_button:
    st.session_state.question_from_button = None   # Reset pour ne pas boucler

question = st.chat_input(
    "Posez une question sur une commande, un client, un stock...",
)

# On accepte aussi la question depuis les boutons si elle a été pré-remplie
# (st.chat_input ne supporte pas de valeur par défaut, on utilise un text_input en fallback)
if not question and default_value:
    question = default_value


# ─────────────────────────────────────────
# Traitement de la question
# ─────────────────────────────────────────
if question:
    # 1. Ajouter le message utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": question})

    # 2. Appeler l'API
    with st.spinner("SteelBot réfléchit... 🔄"):
        result = call_chat(question)

    # 3. Traiter la réponse
    if result["ok"]:
        data = result["data"]
        st.session_state.messages.append({
            "role": "assistant",
            "content": data.get("answer", "Pas de réponse."),
            "tools_called": data.get("tools_called", []),
            "latency_ms": data.get("latency_ms"),
        })
    else:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Erreur : {result['error']}",
            "tools_called": [],
        })

    # 4. Rerun pour afficher les nouveaux messages
    st.rerun()