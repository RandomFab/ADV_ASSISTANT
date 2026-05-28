# backend/src/api/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router, agent_state
from src.api.middleware import LoggingMiddleware
from src.agent.graph import create_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan = code exécuté au démarrage ET à l'arrêt de l'API.
    Tout ce qui est AVANT le yield s'exécute au démarrage.
    Tout ce qui est APRÈS le yield s'exécute à l'arrêt.
    """
    print("🚀 Démarrage SteelBot API...")
    agent_state["agent"] = await create_agent()
    print("✅ Agent LangGraph initialisé")
    
    yield  # L'API tourne ici
    
    print("🛑 Arrêt de l'API")
    agent_state.clear()

app = FastAPI(
    title="SteelBot API",
    description="API de l'agent ADV intelligent pour la métallurgie",
    version="0.1.0",
    lifespan=lifespan
)

# CORS — nécessaire pour que Streamlit (port 8501) puisse appeler l'API (port 8001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod : restreindre aux origines connues
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.include_router(router)