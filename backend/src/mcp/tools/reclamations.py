"""
Outil MCP : search_reclamations

Expose les réclamations d'un client à l'agent LLM.
Filtre optionnel sur le statut (ouverte / en_cours / cloturee).
Retourne la liste détaillée + statistiques agrégées (nb ouvertes, taux de réclamation).
"""

from typing import Optional

from src.mcp.mcp_instance import mcp
from src.database.connection import SessionLocal
from src.database.models import Client, Commande
from src.database.models import StatutReclamationEnum
from sqlalchemy.orm import joinedload


@mcp.tool()
def search_reclamations(
    client_name: str, statut: Optional[StatutReclamationEnum] = None
) -> dict:
    """
    Récupère les réclamations d'un client par son nom (recherche floue) et statut.

    Args:
        client_name: Nom du client (ex: "Acme Corp")
        statut: Filtre sur le statut de la réclamation (ouverte / en_cours / cloturee)
    Returns:
        Dictionnaire avec la liste des réclamations et les statistiques.
        Retourne une erreur si le client n'existe pas.
    """

    db = SessionLocal()
    try:
        client = (
            db.query(Client)
            .options(joinedload(Client.commandes).joinedload(Commande.reclamations))
            .filter(Client.nom_entreprise.ilike(f"%{client_name}%"))
            .first()
        )

        if not client:
            return {"found": False, "message": f"Client '{client_name}' non trouvé."}

        reclamations = []
        toutes_reclamations = [
            rec for cmd in client.commandes for rec in cmd.reclamations
        ]
        nb_reclamations_total = len(toutes_reclamations)

        # Applique le filtre statut uniquement pour l'affichage
        if statut:
            toutes_reclamations = [
                r for r in toutes_reclamations if r.statut.value == statut
            ]

        for rec in toutes_reclamations:
            # trouve la commande associée
            cmd = next(cmd for cmd in client.commandes if rec in cmd.reclamations)
            reclamations.append(
                {
                    "numero_ticket": rec.numero_ticket,
                    "type": rec.type.value,
                    "statut": rec.statut.value,
                    "priorite": rec.priorite.value,
                    "date_ouverture": rec.date_ouverture.isoformat(),
                    "date_cloture": rec.date_cloture.isoformat()
                    if rec.date_cloture
                    else None,
                    "commande_numero": cmd.numero_commande,
                }
            )

        nb_commandes = len(client.commandes)
        taux_reclamation = (
            (nb_reclamations_total / nb_commandes) * 100 if nb_commandes > 0 else 0
        )

        return {
            "found": True,
            "client": client.nom_entreprise,
            "reclamations": reclamations,
            "statistiques": {
                "nb_reclamations_total": nb_reclamations_total,
                "nb_commandes": nb_commandes,
                "taux_reclamation": taux_reclamation,
            },
        }
    finally:
        db.close()
