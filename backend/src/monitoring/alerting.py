# backend/src/monitoring/alerting.py
"""
Vérification des seuils de monitoring et création automatique de GitHub Issues.

Les seuils sont définis ici en constantes — en production, ils iraient dans un fichier
de config ou des variables d'environnement.
"""

import os
import json
import requests as http_requests
from datetime import datetime, timezone
from src.monitoring.logger import load_interactions, compute_metrics

# ── Seuils d'alerte (reproduits depuis la roadmap) ───────────────────────────
SEUILS = {
    "latence_moyenne_ms": 500,   # > 10 secondes → UX dégradée
    "taux_erreur_pct": 5.0,         # > 5% → agent défaillant
    "taux_sans_outil_pct": 20.0,    # > 20% → agent qui hallucine
}

def _create_github_issue(title: str, body: str) -> dict:
    """
    Crée une Issue GitHub via l'API REST.
    Nécessite GITHUB_TOKEN et GITHUB_REPO dans les variables d'environnement.
    """
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_REPO = os.getenv("GITHUB_REPO")
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return {
            "created": False,
            "reason": "GITHUB_TOKEN ou GITHUB_REPO non configurés — Issue non créée."
        }

    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "title": title,
        "body": body,
        "labels": ["alert", "monitoring"],
    }

    try:
        r = http_requests.post(url, headers=headers, json=payload, timeout=10)
        r.raise_for_status()
        issue = r.json()
        return {
            "created": True,
            "issue_number": issue["number"],
            "url": issue["html_url"],
        }
    except Exception as e:
        return {"created": False, "reason": str(e)}


def _build_issue_body(alert_type: str, metrics: dict, valeur_actuelle: float, seuil: float) -> str:
    """Formate le body de la GitHub Issue avec les métriques contextuelles."""
    timestamp = datetime.now(timezone.utc).isoformat()
    metrics_json = json.dumps(metrics, indent=2, ensure_ascii=False)
    
    return f"""## 🚨 Alerte SteelBot — {alert_type}

**Détectée le** : {timestamp}
**Valeur actuelle** : `{valeur_actuelle}`
**Seuil configuré** : `{seuil}`

## Métriques sur la période analysée

```json
{metrics_json}
```

## Action recommandée
- Vérifier les logs dans `logs/interactions.jsonl`
- Redémarrer l'agent si nécessaire (`uvicorn src.api.main:app --reload --port 8001`)
- Vérifier que le serveur MCP est actif sur le port 8000

---
*Issue créée automatiquement par le système de monitoring SteelBot*"""


def run_monitoring_check(last_n: int = 100) -> dict:
    """
    Point d'entrée principal du monitoring.
    
    1. Charge les N dernières interactions
    2. Calcule les métriques
    3. Vérifie chaque seuil
    4. Crée une GitHub Issue pour chaque seuil dépassé

    Returns:
        Résumé du check avec les alertes déclenchées.
    """
    interactions = load_interactions(last_n=last_n)
    metrics = compute_metrics(interactions)
    
    if metrics.get("nb_interactions", 0) == 0:
        return {"status": "ok", "nb_interactions_analysees": 0, "message": "Aucune interaction à analyser.", "alertes": []}

    alertes_declenchees = []

    # ── Check latence ─────────────────────────────────────────────────────
    latence_moy = metrics["latence"]["moyenne_ms"]
    if latence_moy > SEUILS["latence_moyenne_ms"]:
        title = f"[ALERTE] Latence moyenne > {SEUILS['latence_moyenne_ms']/1000:.0f}s détectée"
        body = _build_issue_body("Latence excessive", metrics, latence_moy, SEUILS["latence_moyenne_ms"])
        result = _create_github_issue(title, body)
        alertes_declenchees.append({
            "type": "latence",
            "valeur": latence_moy,
            "seuil": SEUILS["latence_moyenne_ms"],
            "github_issue": result,
        })

    # ── Check taux d'erreur ───────────────────────────────────────────────
    taux_erreur = metrics["erreurs"]["taux_pct"]
    if taux_erreur > SEUILS["taux_erreur_pct"]:
        title = f"[ALERTE] Taux d'erreur > {SEUILS['taux_erreur_pct']}% détecté"
        body = _build_issue_body("Taux d'erreur élevé", metrics, taux_erreur, SEUILS["taux_erreur_pct"])
        result = _create_github_issue(title, body)
        alertes_declenchees.append({
            "type": "taux_erreur",
            "valeur": taux_erreur,
            "seuil": SEUILS["taux_erreur_pct"],
            "github_issue": result,
        })

    # ── Check taux sans outil ─────────────────────────────────────────────
    taux_sans_outil = metrics["outils"]["taux_sans_outil_pct"]
    if taux_sans_outil > SEUILS["taux_sans_outil_pct"]:
        title = f"[ALERTE] {taux_sans_outil:.1f}% des requêtes sans outil appelé"
        body = _build_issue_body("Agent sans outil", metrics, taux_sans_outil, SEUILS["taux_sans_outil_pct"])
        result = _create_github_issue(title, body)
        alertes_declenchees.append({
            "type": "sans_outil",
            "valeur": taux_sans_outil,
            "seuil": SEUILS["taux_sans_outil_pct"],
            "github_issue": result,
        })

    return {
        "status": "alert" if alertes_declenchees else "ok",
        "nb_interactions_analysees": metrics["nb_interactions"],
        "metriques": metrics,
        "alertes": alertes_declenchees,
    }