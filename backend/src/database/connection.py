import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()  # Charge le .env automatiquement

# Construction de l'URL de connexion PostgreSQL
DATABASE_URL = (
    f"postgresql://{os.getenv('PG_USERNAME')}:{os.getenv('PG_PASSWORD')}"
    f"@{os.getenv('PG_HOST', 'localhost')}:{os.getenv('PG_PORT', '5432')}"
    f"/{os.getenv('PG_DATABASE')}"
)

# L'engine est la connexion physique à la base
engine = create_engine(
    DATABASE_URL,
    echo=False,       # Passer à True pour voir le SQL généré en debug
    pool_pre_ping=True  # Vérifie que la connexion est vivante avant chaque requête
)

# La session est ce qu'on utilise pour faire des requêtes
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Classe de base dont hériteront tous nos modèles
class Base(DeclarativeBase):
    pass