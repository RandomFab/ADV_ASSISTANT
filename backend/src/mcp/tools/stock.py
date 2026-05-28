"""
Outil MCP : get_stock_level

Expose les niveaux de stock d'un produit à l'agent LLM.
Recherche par référence ou mot-clé sur la désignation (ILIKE).
Calcule le stock net (disponible - réservé) et indique le délai de fabrication si rupture.
"""

from src.mcp.mcp_instance import mcp
from src.database.connection import SessionLocal
from src.database.models import Produit

@mcp.tool()
def get_stock_level(reference: str = None, mot_cle: str = None) -> dict:
    """
    Récupère le niveau de stock d'un produit par référence ou mot-clé.
    
    Args:
        reference: Référence du produit
        mot_cle: Mot-clé pour la recherche sur la désignation
    
    Returns:
        Dictionnaire avec les informations de stock.
    """
    db = SessionLocal()
    try:
        query = db.query(Produit)
        if reference:
            query = query.filter(Produit.reference == reference)
        if mot_cle:
            for mot in mot_cle.split():
                query = query.filter(Produit.designation.ilike(f"%{mot}%"))        
        
        produit = query.first()
        if not produit:
            return {
                "found": False,
                "message": "Produit non trouvé."
            }
        
        stock_net = produit.stock_disponible - produit.stock_reserve
        return {
            "found": True,
            "reference": produit.reference,
            "designation": produit.designation,
            "stock_disponible": produit.stock_disponible,
            "stock_reserve": produit.stock_reserve,
            "stock_net": stock_net
        }
    finally:
        db.close()