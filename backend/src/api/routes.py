# backend/src/api/routes.py

import json
import time
import uuid
import logging
from fastapi import APIRouter, HTTPException
from src.api.schemas import ChatRequest, ChatResponse
from src.config.paths import INTERACTIONS_LOG
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


logger = logging.getLogger("steelbot")

router = APIRouter()

# Stockage global de l'agent — initialisé par main.py au démarrage
agent_state = {}

# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    agent = agent_state.get("agent")
    if not agent:
        raise HTTPException(status_code=503, detail="Agent non disponible")

    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.question)]}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur agent : {str(e)}")

    # Extraction de la réponse finale (dernier message AIMessage)
    messages = result["messages"]
    final_answer = next(
        (m.content for m in reversed(messages) if isinstance(m, AIMessage)),
        "Pas de réponse"
    )

    # Extraction des outils appelés (messages ToolMessage)
    tools_called = [
        m.name for m in messages
        if hasattr(m, "name") and m.name is not None
        and not isinstance(m, AIMessage)
    ]

    latency_ms = round((time.time() - start_time) * 1000)

    # Log structuré métier — c'est cette donnée qu'Evidently analysera en Jour 6
    log_entry = {
        "request_id": request_id,
        "question": request.question,
        "tools_called": tools_called,
        "answer_length": len(final_answer),
        "latency_ms": latency_ms,
        "status": "success"
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False))

    # Sauvegarde dans le fichier d'interactions pour analyse ultérieure
    with open(INTERACTIONS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return ChatResponse(
        request_id=request_id,
        question=request.question,
        answer=final_answer,
        tools_called=tools_called,
        latency_ms=latency_ms
    )


@router.get("/health")
async def health():
    agent = agent_state.get("agent")
    return {
        "status": "ok",
        "agent": "ready" if agent else "not initialized",
        "mcp_server": "http://127.0.0.1:8000/sse"
    }