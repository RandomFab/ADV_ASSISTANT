"""
Outil MCP : get_delivery_estimate

Calcule et expose une estimation de livraison pour une commande donnée.
La logique de calcul dépend du statut actuel de la commande :
en_attente → délai fabrication + transport / en_production → estimation dynamique /
expediee → date prévue / livree → date réelle.
"""