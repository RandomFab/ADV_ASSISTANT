"""
Instance partagée du serveur FastMCP.

Ce module est le point central de l'architecture MCP : il crée l'unique instance
FastMCP utilisée par tous les modules tools. Le fait de l'isoler ici évite les
imports circulaires — server.py et tous les tools/*.py importent depuis ce module,
jamais les uns depuis les autres.
"""

from fastmcp import FastMCP

mcp = FastMCP("SteelBot MCP Server")