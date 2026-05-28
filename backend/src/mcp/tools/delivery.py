"""
Outil MCP : get_delivery_estimate

Calcule et expose une estimation de livraison pour une commande donnée.
La logique de calcul dépend du statut actuel de la commande :
en_attente → délai fabrication + transport / en_production → estimation dynamique /
expediee → date prévue / livree → date réelle.
"""

from datetime import date, timedelta
from src.mcp.mcp_instance import mcp
from src.database.connection import SessionLocal
from src.database.models import Commande, LigneCommande
from sqlalchemy.orm import joinedload
@mcp.tool()
def get_delivery_estimate(order_id: str) -> dict:
    """
    Récupère l'estimation de livraison d'une commande par son numéro.
    
    Args:
        order_id: Numéro de commande (ex: CMD-2024-0847)
    
    Returns:
        Dictionnaire avec l'estimation de livraison et les détails associés.
        Retourne une erreur si la commande n'existe pas.
    """
    db = SessionLocal()
    try:
        commande = (
            db.query(Commande)
            .options(joinedload(Commande.client),joinedload(Commande.lignes).joinedload(LigneCommande.produit))
            .filter(Commande.numero_commande == order_id)
            .first()
        )

        if not commande:
            return {
                "found": False,
                "message": f"Commande {order_id} non trouvée."
            }
        
        # Logique d'estimation basée sur le statut
        if commande.statut.value in ["en_attente", "en_production"]:
            # Calcul basé sur le délai de fabrication le plus long + 5 jours de transport
            delai_max = max(ligne.produit.delai_fabrication_jours for ligne in commande.lignes)
            date_fin = (commande.date_commande + timedelta(days=delai_max + 5)).date()
            jours_restants = (date_fin - date.today()).days
            estimation = f"Livraison estimée le {date_fin.isoformat()}"
        elif commande.statut.value == "expediee":
            estimation = f"Date prévue de livraison : {commande.date_livraison_prevue.isoformat()}"
        elif commande.statut.value == "livree":
            estimation = f"Livrée le : {commande.date_livraison_reelle.isoformat()}"
        elif commande.statut.value == "annulee":
            return {"found": True, "statut": "annulee", "estimation_livraison": "Commande annulée."}
        else:
            estimation = "Statut inconnu, impossible d'estimer la livraison."
        
        return {
            "found": True,
            "numero_commande": commande.numero_commande,
            "client": commande.client.nom_entreprise,
            "statut": commande.statut.value,
            "estimation_livraison": estimation
        }
    finally:
        db.close()