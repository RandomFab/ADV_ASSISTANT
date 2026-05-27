"""
Outil MCP : get_client_info

Expose la fiche complète d'un client à l'agent LLM.
Inclut le CA cumulé, l'historique des commandes et les réclamations en cours.
Supporte une recherche floue sur le nom (ILIKE PostgreSQL).
"""