# backend/src/monitoring/evidently_reports.py
"""
Génération de rapports Evidently sur la qualité des interactions SteelBot.

On utilise Evidently en mode "rapport de données" (pas data drift ML classique) :
on analyse la distribution des latences, outils, statuts sur une période donnée.
"""

import pandas as pd
from evidently import Report
from evidently.presets import DataSummaryPreset

from src.monitoring.logger import load_interactions
from src.config.paths import REPORTS_DIR


def _interactions_to_dataframe(interactions: list[dict]) -> pd.DataFrame:
    """Convertit la liste d'interactions en DataFrame Pandas pour Evidently."""
    rows = []
    for i in interactions:
        rows.append(
            {
                "latency_ms": i.get("latency_ms", 0),
                "nb_tools_called": len(i.get("tools_called", [])),
                "answer_length": i.get("answer_length", 0),
                "status": i.get("status", "unknown"),
                "has_tools": int(len(i.get("tools_called", [])) > 0),
            }
        )
    return pd.DataFrame(rows)


def generate_report(last_n: int = 200) -> str:
    """
    Génère un rapport Evidently HTML sur les dernières interactions.

    Returns:
        Chemin vers le fichier HTML généré.
    """
    interactions = load_interactions(last_n=last_n)

    if len(interactions) < 1:
        raise ValueError(
            f"Pas assez d'interactions pour un rapport ({len(interactions)} < 1)."
        )

    df = _interactions_to_dataframe(interactions)

    # DataSummaryPreset = rapport de statistiques descriptives sur chaque colonne
    # Distributions, valeurs manquantes, corrélations — parfait pour notre usage
    report = Report(metrics=[DataSummaryPreset()])
    my_eval = report.run(current_data=df)

    output_path = (
        REPORTS_DIR / f"report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    my_eval.save_html(str(output_path))

    return str(output_path)
