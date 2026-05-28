# backend/src/config/paths.py

from pathlib import Path

# Chemin vers la racine du projet backend
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Dossier des logs
LOGS_DIR = ROOT_DIR / "logs"
INTERACTIONS_LOG = LOGS_DIR / "interactions.jsonl"

# S'assurer que le dossier logs existe
LOGS_DIR.mkdir(exist_ok=True)
