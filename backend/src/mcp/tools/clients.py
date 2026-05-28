"""
Outil MCP : get_client_info

Expose la fiche complète d'un client à l'agent LLM.
Inclut le CA cumulé, l'historique des commandes et les réclamations en cours.
Supporte une recherche floue sur le nom (ILIKE PostgreSQL).
"""

from src.mcp.mcp_instance import mcp
from src.database.connection import SessionLocal
from src.database.models import Client, Commande

from sqlalchemy.orm import joinedload


@mcp.tool()
def get_client_info(client_name: str) -> dict:
    """
    Récupère les informations détaillées d'un client par son nom (recherche floue).

    Args:
        client_name: Nom du client (ex: "Acme Corp")

    Returns:
        Dictionnaire avec fiche client, CA cumulé, commandes et réclamations.
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

        ca_cumule = sum(
            cmd.montant_total_eur if cmd.statut.value == "livree" else 0
            for cmd in client.commandes
        )
        commandes_info = []
        for cmd in sorted(
            client.commandes, key=lambda c: c.date_commande, reverse=True
        )[:5]:
            commandes_info.append(
                {
                    "numero_commande": cmd.numero_commande,
                    "date_commande": cmd.date_commande.isoformat(),
                    "montant_total_eur": float(cmd.montant_total_eur),
                    "statut": cmd.statut.value,
                    "reclamations": [
                        {"numero_ticket": rec.numero_ticket, "statut": rec.statut.value}
                        for rec in cmd.reclamations
                    ],
                }
            )
        return {
            "found": True,
            "nom_entreprise": client.nom_entreprise,
            "commercial_attitre": client.commercial_attitre,
            "ca_cumule_eur": float(ca_cumule),
            "commandes": commandes_info,
        }
    finally:
        db.close()
