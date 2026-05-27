from src.database.connection import engine, Base
from src.database import models  # Important: force l'import des modeles pour que SQLAlchemy les connaisse

def init_db():
    print("Creation des tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables creees ✅")

if __name__ == "__main__":
    init_db()