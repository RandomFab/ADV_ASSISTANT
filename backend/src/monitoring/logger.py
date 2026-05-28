# backend/src/monitoring/logger.py
"""
Lecture et agrégation des logs d'interaction.

Source : logs/interactions.jsonl (une ligne JSON par requête /chat)
Calcule les métriques qui seront vérifiées contre les seuils d'alerte.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter
from src.config.paths import INTERACTIONS_LOG


def load_interactions(last_n: int = None, since_hours: int = None) -> list[dict]:
    """
    Charge les interactions depuis le fichier JSONL.

    Args:
        last_n: Garder uniquement les N dernières interactions
        since_hours: Garder uniquement les interactions des X dernières heures
    """
    if not INTERACTIONS_LOG.exists():
        return []

    interactions = []
    with open(INTERACTIONS_LOG, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    interactions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # Ligne corrompue, on l'ignore

    # Filtre temporel
    if since_hours:
        cutoff = datetime.utcnow() - timedelta(hours=since_hours)
        interactions = [
            i for i in interactions
            if datetime.fromisoformat(i.get("timestamp", "2000-01-01T00:00:00")).replace(tzinfo=None) >= cutoff
        ]

    # Filtre sur les N dernières
    if last_n:
        interactions = interactions[-last_n:]

    return interactions


def compute_metrics(interactions: list[dict]) -> dict:
    """
    Calcule les métriques de monitoring à partir des interactions.

    Retourne un dict avec toutes les métriques et un résumé des seuils dépassés.
    """
    if not interactions:
        return {
            "nb_interactions": 0,
            "message": "Aucune interaction à analyser."
        }

    nb_total = len(interactions)
    
    # ── Latence ──────────────────────────────────────────────────────────
    latences = [i["latency_ms"] for i in interactions if "latency_ms" in i]
    latence_moyenne = sum(latences) / len(latences) if latences else 0
    latence_max = max(latences) if latences else 0

    # ── Taux d'erreur ─────────────────────────────────────────────────────
    nb_erreurs = sum(1 for i in interactions if i.get("status") == "error")
    taux_erreur = (nb_erreurs / nb_total) * 100 if nb_total > 0 else 0

    # ── Outils appelés ───────────────────────────────────────────────────
    # Comptage de tous les tool calls sur la période
    all_tools = []
    for i in interactions:
        all_tools.extend(i.get("tools_called", []))
    
    nb_sans_outil = sum(1 for i in interactions if not i.get("tools_called"))
    taux_sans_outil = (nb_sans_outil / nb_total) * 100 if nb_total > 0 else 0
    tools_frequence = dict(Counter(all_tools).most_common())

    # ── Longueur des réponses ────────────────────────────────────────────
    longueurs = [i.get("answer_length", 0) for i in interactions]
    nb_reponses_courtes = sum(1 for l in longueurs if l < 100)   # Probablement tronquée
    nb_reponses_longues = sum(1 for l in longueurs if l > 5000)  # Verbosité excessive

    return {
        "nb_interactions": nb_total,
        "periode": {
            "premiere": interactions[0].get("timestamp"),
            "derniere": interactions[-1].get("timestamp"),
        },
        "latence": {
            "moyenne_ms": round(latence_moyenne, 1),
            "max_ms": latence_max,
        },
        "erreurs": {
            "nb": nb_erreurs,
            "taux_pct": round(taux_erreur, 2),
        },
        "outils": {
            "nb_appels_total": len(all_tools),
            "frequence": tools_frequence,
            "nb_interactions_sans_outil": nb_sans_outil,
            "taux_sans_outil_pct": round(taux_sans_outil, 2),
        },
        "reponses": {
            "nb_trop_courtes": nb_reponses_courtes,
            "nb_trop_longues": nb_reponses_longues,
        }
    }