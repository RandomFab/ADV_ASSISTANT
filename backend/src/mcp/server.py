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
import src.mcp.tools.orders  # noqa: F401
import src.mcp.tools.clients  # noqa: F401
import src.mcp.tools.stock  # noqa: F401
import src.mcp.tools.delivery  # noqa: F401
import src.mcp.tools.reclamations  # noqa: F401


if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
