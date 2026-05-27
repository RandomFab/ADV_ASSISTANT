from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, DateTime, Date,
    ForeignKey, Text, Enum as SAEnum, Boolean,
    func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.connection import Base
import enum

# --- Enums Python -> traduits en contraintes SQL par SQLAlchemy ---

class SecteurEnum(str, enum.Enum):
    btp = "btp"
    automobile = "automobile"
    agroalimentaire = "agroalimentaire"
    energie = "energie"

class StatutCommandeEnum(str, enum.Enum):
    en_attente = "en_attente"
    en_production = "en_production"
    expediee = "expediee"
    livree = "livree"
    annulee = "annulee"

class FamilleEnum(str, enum.Enum):
    coil = "coil"
    tube = "tube"
    tole = "tole"

class MatiereEnum(str, enum.Enum):
    acier = "acier"
    inox = "inox"
    aluminium = "aluminium"

class TypeReclamationEnum(str, enum.Enum):
    defaut_soudure = "defaut_soudure"
    retard_livraison = "retard_livraison"
    erreur_quantite = "erreur_quantite"
    non_conformite_dimensionnelle = "non_conformite_dimensionnelle"
    corrosion = "corrosion"

class StatutReclamationEnum(str, enum.Enum):
    ouverte = "ouverte"
    en_cours = "en_cours"
    cloturee = "cloturee"

class PrioriteEnum(str, enum.Enum):
    basse = "basse"
    moyenne = "moyenne"
    haute = "haute"


# --- Modèles ---

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nom_entreprise: Mapped[str] = mapped_column(String(200), nullable=False)
    secteur: Mapped[SecteurEnum] = mapped_column(SAEnum(SecteurEnum), nullable=False)
    zone_geo: Mapped[str] = mapped_column(String(100))
    commercial_attittre: Mapped[str] = mapped_column(String(100))
    conditions_paiement: Mapped[str] = mapped_column(String(50))  # ex: "30j", "60j fin de mois"
    email: Mapped[str] = mapped_column(String(200))
    telephone: Mapped[str] = mapped_column(String(20))
    date_creation: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relations
    commandes: Mapped[list["Commande"]] = relationship(back_populates="client")
    reclamations: Mapped[list["Reclamation"]] = relationship(back_populates="client")


class Produit(Base):
    __tablename__ = "produits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)  # ex: "Coil Acier S235 ep.2mm"
    famille: Mapped[FamilleEnum] = mapped_column(SAEnum(FamilleEnum), nullable=False)
    matiere: Mapped[MatiereEnum] = mapped_column(SAEnum(MatiereEnum), nullable=False)
    nuance: Mapped[str] = mapped_column(String(20))                # ex: S235, 304, 316L
    epaisseur_mm: Mapped[float] = mapped_column(Float, nullable=False)
    diametre_mm: Mapped[float | None] = mapped_column(Float, nullable=True)  # Uniquement pour les tubes
    prix_unitaire_eur: Mapped[float] = mapped_column(Float, nullable=False)
    poids_kg_ml: Mapped[float] = mapped_column(Float)             # kg par metre lineaire
    stock_disponible: Mapped[int] = mapped_column(Integer, default=0)
    stock_reserve: Mapped[int] = mapped_column(Integer, default=0)
    delai_fabrication_jours: Mapped[int] = mapped_column(Integer, default=5)

    # Relations
    lignes: Mapped[list["LigneCommande"]] = relationship(back_populates="produit")


class Commande(Base):
    __tablename__ = "commandes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_commande: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # CMD-2024-0847
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    date_commande: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_livraison_prevue: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_livraison_reelle: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    statut: Mapped[StatutCommandeEnum] = mapped_column(SAEnum(StatutCommandeEnum), nullable=False)
    montant_total_eur: Mapped[float] = mapped_column(Float, nullable=False)

    # Relations
    client: Mapped["Client"] = relationship(back_populates="commandes")
    lignes: Mapped[list["LigneCommande"]] = relationship(back_populates="commande")
    reclamations: Mapped[list["Reclamation"]] = relationship(back_populates="commande")


class LigneCommande(Base):
    __tablename__ = "lignes_commande"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    commande_id: Mapped[int] = mapped_column(ForeignKey("commandes.id"), nullable=False)
    produit_id: Mapped[int] = mapped_column(ForeignKey("produits.id"), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    prix_unitaire: Mapped[float] = mapped_column(Float, nullable=False)  # Prix au moment de la commande
    montant_ligne: Mapped[float] = mapped_column(Float, nullable=False)

    # Relations
    commande: Mapped["Commande"] = relationship(back_populates="lignes")
    produit: Mapped["Produit"] = relationship(back_populates="lignes")


class Reclamation(Base):
    __tablename__ = "reclamations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_ticket: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)  # REC-2024-0012
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    commande_id: Mapped[int | None] = mapped_column(ForeignKey("commandes.id"), nullable=True)
    date_ouverture: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_cloture: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    type: Mapped[TypeReclamationEnum] = mapped_column(SAEnum(TypeReclamationEnum), nullable=False)
    statut: Mapped[StatutReclamationEnum] = mapped_column(SAEnum(StatutReclamationEnum), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    priorite: Mapped[PrioriteEnum] = mapped_column(SAEnum(PrioriteEnum), nullable=False)

    # Relations
    client: Mapped["Client"] = relationship(back_populates="reclamations")
    commande: Mapped["Commande"] = relationship(back_populates="reclamations")