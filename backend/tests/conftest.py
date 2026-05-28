# backend/tests/conftest.py

import pytest
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from fastapi.testclient import TestClient

from src.database.connection import Base
from src.database.models import (
    Client, Produit, Commande, LigneCommande, Reclamation,
    SecteurEnum, FamilleEnum, MatiereEnum, StatutCommandeEnum,
    TypeReclamationEnum, StatutReclamationEnum, PrioriteEnum
)
from src.api.main import app
from src.api.routes import agent_state


# ──────────────────────────────────────────────────────────────────
# Database Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def db_engine():
    """Create in-memory SQLite database engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a fresh database session for each test."""
    SessionLocal = sessionmaker(bind=db_engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def db_with_seed(db_session):
    """Seed database with minimal test data."""
    # Create a client
    client = Client(
        nom_entreprise="Acme Corp",
        secteur=SecteurEnum.automobile,
        zone_geo="Île-de-France",
        commercial_attitre="Jean Dupont",
        conditions_paiement="30j",
        email="contact@acme.com",
        telephone="+33612345678",
        date_creation=datetime.utcnow()
    )
    db_session.add(client)
    db_session.flush()

    # Create a product
    produit = Produit(
        reference="COIL-304-2MM",
        designation="Coil Inox 304 épaisseur 2mm",
        famille=FamilleEnum.coil,
        matiere=MatiereEnum.inox,
        nuance="304",
        epaisseur_mm=2.0,
        prix_unitaire_eur=1200.0,
        poids_kg_ml=4.5,
        stock_disponible=100,
        stock_reserve=20,
        delai_fabrication_jours=5
    )
    db_session.add(produit)
    db_session.flush()

    # Create a delivered order
    commande_livree = Commande(
        numero_commande="CMD-2024-0001",
        client_id=client.id,
        date_commande=datetime.utcnow() - timedelta(days=30),
        date_livraison_prevue=datetime.utcnow() - timedelta(days=20),
        date_livraison_reelle=datetime.utcnow() - timedelta(days=18),
        statut=StatutCommandeEnum.livree,
        montant_total_eur=5000.0
    )
    db_session.add(commande_livree)
    db_session.flush()

    # Create a pending order
    commande_attente = Commande(
        numero_commande="CMD-2024-0002",
        client_id=client.id,
        date_commande=datetime.utcnow(),
        date_livraison_prevue=datetime.utcnow() + timedelta(days=10),
        statut=StatutCommandeEnum.en_attente,
        montant_total_eur=3000.0
    )
    db_session.add(commande_attente)
    db_session.flush()

    # Create order lines
    ligne1 = LigneCommande(
        commande_id=commande_livree.id,
        produit_id=produit.id,
        quantite=10,
        prix_unitaire=1200.0,
        montant_ligne=12000.0
    )
    ligne2 = LigneCommande(
        commande_id=commande_attente.id,
        produit_id=produit.id,
        quantite=5,
        prix_unitaire=1200.0,
        montant_ligne=6000.0
    )
    db_session.add_all([ligne1, ligne2])
    db_session.flush()

    # Create a reclamation
    reclamation = Reclamation(
        numero_ticket="REC-2024-0001",
        client_id=client.id,
        commande_id=commande_livree.id,
        date_ouverture=datetime.utcnow() - timedelta(days=5),
        type=TypeReclamationEnum.defaut_soudure,
        statut=StatutReclamationEnum.ouverte,
        description="Défaut détecté après livraison",
        priorite=PrioriteEnum.haute
    )
    db_session.add(reclamation)
    db_session.commit()

    return db_session


@pytest.fixture
def mock_session_local(db_session, monkeypatch):
    """Monkeypatch SessionLocal to return our test session."""
    from src.database.connection import SessionLocal as original_sessionlocal

    def mock_sessionlocal():
        return db_session

    monkeypatch.setattr(
        "src.database.connection.SessionLocal",
        mock_sessionlocal
    )
    monkeypatch.setattr(
        "src.mcp.tools.clients.SessionLocal",
        mock_sessionlocal
    )
    monkeypatch.setattr(
        "src.mcp.tools.orders.SessionLocal",
        mock_sessionlocal
    )
    monkeypatch.setattr(
        "src.mcp.tools.delivery.SessionLocal",
        mock_sessionlocal
    )
    monkeypatch.setattr(
        "src.mcp.tools.stock.SessionLocal",
        mock_sessionlocal
    )
    monkeypatch.setattr(
        "src.mcp.tools.reclamations.SessionLocal",
        mock_sessionlocal
    )


# ──────────────────────────────────────────────────────────────────
# Logging Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_interactions_log(tmp_path, monkeypatch):
    """Create temporary interactions log file and patch the path."""
    log_file = tmp_path / "interactions.jsonl"
    log_file.touch()

    monkeypatch.setattr(
        "src.config.paths.INTERACTIONS_LOG",
        log_file
    )
    monkeypatch.setattr(
        "src.monitoring.logger.INTERACTIONS_LOG",
        log_file
    )

    return log_file


@pytest.fixture
def sample_interactions_log(tmp_interactions_log):
    """Create sample interactions in the log file."""
    interactions = [
        {
            "request_id": "req-001",
            "question": "Quel est le statut de la commande?",
            "tools_called": ["get_order_status"],
            "answer_length": 150,
            "latency_ms": 450,
            "status": "success",
            "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        },
        {
            "request_id": "req-002",
            "question": "Avez-vous du stock?",
            "tools_called": ["get_stock_level"],
            "answer_length": 100,
            "latency_ms": 300,
            "status": "success",
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        },
        {
            "request_id": "req-003",
            "question": "Info client?",
            "tools_called": [],
            "answer_length": 50,
            "latency_ms": 600,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]

    with open(tmp_interactions_log, "w", encoding="utf-8") as f:
        for interaction in interactions:
            f.write(json.dumps(interaction, ensure_ascii=False) + "\n")

    return tmp_interactions_log


# ──────────────────────────────────────────────────────────────────
# Agent & API Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_agent():
    """Create a mock LangGraph agent."""
    agent = AsyncMock()

    async def mock_ainvoke(input_dict):
        from langchain_core.messages import AIMessage
        return {
            "messages": [
                Mock(content="Test question"),
                AIMessage(content="This is a test response")
            ]
        }

    agent.ainvoke = mock_ainvoke
    return agent


@pytest.fixture
def api_client(mock_agent, monkeypatch):
    """Create FastAPI TestClient with mocked agent."""
    # Inject mocked agent into agent_state
    agent_state["agent"] = mock_agent

    client = TestClient(app)
    yield client

    # Cleanup
    agent_state.clear()


# ──────────────────────────────────────────────────────────────────
# GitHub Mock Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_github_requests(monkeypatch):
    """Mock requests.post for GitHub API calls."""
    mock_post = Mock()
    mock_post.return_value.status_code = 201
    mock_post.return_value.json.return_value = {
        "number": 42,
        "html_url": "https://github.com/test/repo/issues/42"
    }

    monkeypatch.setattr("src.monitoring.alerting.http_requests.post", mock_post)
    return mock_post


@pytest.fixture
def mock_github_env(monkeypatch):
    """Set GitHub environment variables."""
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-abc123")
    monkeypatch.setenv("GITHUB_REPO", "test/repo")


# ──────────────────────────────────────────────────────────────────
# Combined Fixtures
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mcp_test_env(mock_session_local, db_with_seed):
    """Combined fixture for MCP tool testing."""
    return {
        "db_session": db_with_seed,
        "session_local": mock_session_local
    }


@pytest.fixture
def monitoring_test_env(tmp_interactions_log, sample_interactions_log, mock_github_env, mock_github_requests):
    """Combined fixture for monitoring testing."""
    return {
        "log_file": sample_interactions_log,
        "github_post": mock_github_requests
    }
