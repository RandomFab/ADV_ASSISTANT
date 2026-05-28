"""
Outil MCP : get_order_status

Expose le statut détaillé d'une commande à l'agent LLM.
Interroge PostgreSQL via SQLAlchemy (jointures Commande + Client + LigneCommande + Produit).
"""

from src.mcp.mcp_instance import mcp
from src.database.connection import SessionLocal
from src.database.models import Commande, LigneCommande

from sqlalchemy.orm import joinedload


@mcp.tool()
def get_order_status(order_id: str) -> dict:
    """
    Récupère le statut complet d'une commande par son numéro.

    Args:
        order_id: Numéro de commande (ex: CMD-2024-0847)

    Returns:
        Dictionnaire avec statut, client, lignes de commande et montants.
        Retourne une erreur si la commande n'existe pas.
    """

    db = SessionLocal()
    try:
        commande = (
            db.query(Commande)
            .options(
                joinedload(Commande.client),
                joinedload(Commande.lignes).joinedload(LigneCommande.produit),
            )
            .filter(Commande.numero_commande == order_id)
            .first()
        )

        if not commande:
            return {"found": False, "message": f"Commande {order_id} non trouvée."}

        return {
            "found": True,
            "numero_commande": commande.numero_commande,
            "statut": commande.statut.value,
            "date_commande": commande.date_commande.isoformat(),
            "date_livraison_prevue": (
                commande.date_livraison_prevue.isoformat()
                if commande.date_livraison_prevue
                else None
            ),
            "date_livraison_reelle": (
                commande.date_livraison_reelle.isoformat()
                if commande.date_livraison_reelle
                else None
            ),
            "montant_total_eur": float(commande.montant_total_eur),
            "client": {
                "nom": commande.client.nom_entreprise,
                "commercial": commande.client.commercial_attitre,
                "email": commande.client.email,
            },
            "lignes": [
                {
                    "produit_ref": ligne.produit.reference,
                    "produit_designation": ligne.produit.designation,
                    "quantite": ligne.quantite,
                    "prix_unitaire": float(ligne.prix_unitaire),
                    "montant_ligne": float(ligne.montant_ligne),
                }
                for ligne in commande.lignes
            ],
        }
    finally:
        # TOUJOURS fermer la session — sinon fuite de connexions
        db.close()
