"""
Outil MCP : get_order_status

Expose le statut détaillé d'une commande à l'agent LLM.
Interroge PostgreSQL via SQLAlchemy (jointures Commande + Client + LigneCommande + Produit).
"""