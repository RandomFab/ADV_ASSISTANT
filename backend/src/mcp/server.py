"""
Point d'entrée du serveur MCP SteelBot.

Ce fichier a deux responsabilités :
1. Importer tous les modules tools pour déclencher l'enregistrement des outils
   sur l'instance mcp (effet de bord volontaire des imports).
2. Lancer le serveur MCP via mcp.run().

Le transport par défaut est stdio (local/dev). En production Docker,
FastMCP basculera sur SSE/HTTP.
"""

from src.mcp.mcp_instance import mcp

import src.mcp.tools.orders
import src.mcp.tools.reclamations
import src.mcp.tools.clients
import src.mcp.tools.stock
import src.mcp.tools.delivery