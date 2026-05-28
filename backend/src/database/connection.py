import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()  # Charge le .env automatiquement

# Construction de l'URL de connexion PostgreSQL
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB')}"
)
print(
    f"DEBUG: DATABASE_URL generated (password hidden): postgresql://{os.getenv('POSTGRES_USER')}:****@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
)

# L'engine est la connexion physique a la base
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Passer a True pour voir le SQL genere en debug
    pool_pre_ping=True,  # Verifie que la connexion est vivante avant chaque requete
)

# La session est ce qu'on utilise pour faire des requêtes
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# Classe de base dont hériteront tous nos modèles
class Base(DeclarativeBase):
    pass
