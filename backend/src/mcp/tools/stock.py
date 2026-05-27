"""
Outil MCP : get_stock_level

Expose les niveaux de stock d'un produit à l'agent LLM.
Recherche par référence ou mot-clé sur la désignation (ILIKE).
Calcule le stock net (disponible - réservé) et indique le délai de fabrication si rupture.
"""