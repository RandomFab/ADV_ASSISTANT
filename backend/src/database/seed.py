import random
from datetime import datetime, timedelta
from faker import Faker
from src.database.connection import SessionLocal
from src.database.models import (
    Client, Produit, Commande, LigneCommande, Reclamation,
    SecteurEnum, FamilleEnum, MatiereEnum, StatutCommandeEnum,
    TypeReclamationEnum, StatutReclamationEnum, PrioriteEnum
)

fake = Faker("fr_FR")
random.seed(42)  # Reproductibilité — même seed = mêmes données à chaque run


# --- Helpers ---

def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))

def weighted_month() -> int:
    """Saisonnalité métallurgie : pic Q1/Q4, creux août"""
    weights = [10, 9, 8, 7, 6, 5, 4, 2, 6, 7, 9, 10]  # Jan→Déc
    return random.choices(range(1, 13), weights=weights)[0]


# --- Générateurs ---

def generate_clients(n: int = 40) -> list[Client]:
    secteurs = list(SecteurEnum)
    zones = ["Île-de-France", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine",
             "Occitanie", "Hauts-de-France", "Grand Est", "Bretagne", "PACA"]
    conditions = ["30j", "60j", "60j fin de mois", "45j fin de mois", "comptant"]
    commerciaux = ["Sophie Martin", "Thomas Dubois", "Marie Lambert", "Pierre Moreau"]

    clients = []
    for _ in range(n):
        clients.append(Client(
            nom_entreprise=fake.company(),
            secteur=random.choice(secteurs),
            zone_geo=random.choice(zones),
            commercial_attitre=random.choice(commerciaux),
            conditions_paiement=random.choice(conditions),
            email=fake.company_email(),
            telephone=fake.phone_number(),
            date_creation=random_date(datetime(2020, 1, 1), datetime(2023, 1, 1))
        ))
    return clients


def generate_produits() -> list[Produit]:
    """Produits réalistes métallurgie — références fixes pour la cohérence"""
    produits_data = [
        # Coils acier
        ("COIL-S235-1.5", "Coil Acier S235 ép.1.5mm", FamilleEnum.coil, MatiereEnum.acier, "S235", 1.5, None, 850, 11.8, 45, 5),
        ("COIL-S235-2.0", "Coil Acier S235 ép.2mm", FamilleEnum.coil, MatiereEnum.acier, "S235", 2.0, None, 920, 15.7, 38, 5),
        ("COIL-S355-2.0", "Coil Acier S355 ép.2mm", FamilleEnum.coil, MatiereEnum.acier, "S355", 2.0, None, 1050, 15.7, 30, 7),
        ("COIL-S355-3.0", "Coil Acier S355 ép.3mm", FamilleEnum.coil, MatiereEnum.acier, "S355", 3.0, None, 1100, 23.6, 25, 7),
        # Coils inox
        ("COIL-304-1.0", "Coil Inox 304 ép.1mm", FamilleEnum.coil, MatiereEnum.inox, "304", 1.0, None, 2800, 7.9, 20, 10),
        ("COIL-304-2.0", "Coil Inox 304 ép.2mm", FamilleEnum.coil, MatiereEnum.inox, "304", 2.0, None, 3100, 15.8, 15, 10),
        ("COIL-316L-1.5", "Coil Inox 316L ép.1.5mm", FamilleEnum.coil, MatiereEnum.inox, "316L", 1.5, None, 3800, 11.9, 12, 14),
        # Coils alu
        ("COIL-ALU-1.0", "Coil Aluminium 1050 ép.1mm", FamilleEnum.coil, MatiereEnum.aluminium, "1050", 1.0, None, 1900, 2.7, 30, 7),
        ("COIL-ALU-2.0", "Coil Aluminium 5754 ép.2mm", FamilleEnum.coil, MatiereEnum.aluminium, "5754", 2.0, None, 2200, 5.4, 22, 7),
        # Tubes acier soudés
        ("TUBE-S235-33", "Tube Soudé S235 Ø33mm ép.2mm", FamilleEnum.tube, MatiereEnum.acier, "S235", 2.0, 33.0, 1200, 1.48, 60, 5),
        ("TUBE-S235-48", "Tube Soudé S235 Ø48mm ép.2mm", FamilleEnum.tube, MatiereEnum.acier, "S235", 2.0, 48.0, 1350, 2.22, 50, 5),
        ("TUBE-S235-60", "Tube Soudé S235 Ø60mm ép.3mm", FamilleEnum.tube, MatiereEnum.acier, "S235", 3.0, 60.0, 1500, 4.19, 40, 7),
        ("TUBE-S355-76", "Tube Soudé S355 Ø76mm ép.3mm", FamilleEnum.tube, MatiereEnum.acier, "S355", 3.0, 76.0, 1800, 5.40, 35, 7),
        # Tubes inox
        ("TUBE-304-42", "Tube Inox 304 Ø42mm ép.2mm", FamilleEnum.tube, MatiereEnum.inox, "304", 2.0, 42.0, 4200, 1.98, 20, 12),
        ("TUBE-316L-48", "Tube Inox 316L Ø48mm ép.2mm", FamilleEnum.tube, MatiereEnum.inox, "316L", 2.0, 48.0, 5100, 2.22, 15, 14),
        # Tôles acier
        ("TOLE-S235-3", "Tôle Acier S235 ép.3mm", FamilleEnum.tole, MatiereEnum.acier, "S235", 3.0, None, 980, 23.6, 50, 3),
        ("TOLE-S235-5", "Tôle Acier S235 ép.5mm", FamilleEnum.tole, MatiereEnum.acier, "S235", 5.0, None, 1050, 39.3, 40, 3),
        ("TOLE-S355-4", "Tôle Acier S355 ép.4mm", FamilleEnum.tole, MatiereEnum.acier, "S355", 4.0, None, 1150, 31.4, 35, 5),
        # Tôles inox
        ("TOLE-304-2", "Tôle Inox 304 ép.2mm", FamilleEnum.tole, MatiereEnum.inox, "304", 2.0, None, 3200, 15.8, 18, 10),
        ("TOLE-316L-3", "Tôle Inox 316L ép.3mm", FamilleEnum.tole, MatiereEnum.inox, "316L", 3.0, None, 4500, 23.7, 10, 14),
    ]

    produits = []
    for ref, desig, famille, matiere, nuance, ep, diam, prix, poids, stock, delai in produits_data:
        produits.append(Produit(
            reference=ref,
            designation=desig,
            famille=famille,
            matiere=matiere,
            nuance=nuance,
            epaisseur_mm=ep,
            diametre_mm=diam,
            prix_unitaire_eur=prix,
            poids_kg_ml=poids,
            stock_disponible=stock,
            stock_reserve=random.randint(0, stock // 3),
            delai_fabrication_jours=delai
        ))
    return produits


def generate_commandes(clients: list[Client], produits: list[Produit], n: int = 600) -> list[Commande]:
    commandes = []
    # start_date = datetime(2023, 1, 1)
    # end_date = datetime(2025, 1, 1)

    for i in range(n):
        # Saisonnalité
        month = weighted_month()
        year = random.choice([2023, 2024])
        day = random.randint(1, 28)
        date_commande = datetime(year, month, day)

        # Délai de livraison prévu : 10 à 30 jours
        delai_livraison = random.randint(10, 30)
        date_livraison_prevue = date_commande + timedelta(days=delai_livraison)

        # Statut cohérent avec la date
        aujourd_hui = datetime(2025, 1, 1)
        age_jours = (aujourd_hui - date_commande).days

        if age_jours > 60:
            # Commande ancienne : majoritairement livrée
            statut = random.choices(
                [StatutCommandeEnum.livree, StatutCommandeEnum.annulee],
                weights=[90, 10]
            )[0]
        elif age_jours > 20:
            statut = random.choices(
                [StatutCommandeEnum.livree, StatutCommandeEnum.expediee, StatutCommandeEnum.en_production],
                weights=[60, 25, 15]
            )[0]
        else:
            statut = random.choices(
                [StatutCommandeEnum.en_production, StatutCommandeEnum.en_attente, StatutCommandeEnum.expediee],
                weights=[50, 30, 20]
            )[0]

        # Date de livraison réelle si livrée
        date_livraison_reelle = None
        if statut == StatutCommandeEnum.livree:
            retard = random.randint(-3, 10)  # Parfois en avance, souvent à l'heure, parfois en retard
            date_livraison_reelle = date_livraison_prevue + timedelta(days=retard)

        # Lignes de commande : 2 à 5 produits
        nb_lignes = random.randint(2, 5)
        produits_choisis = random.sample(produits, nb_lignes)
        montant_total = 0
        lignes = []

        for produit in produits_choisis:
            quantite = random.randint(5, 100)
            prix = produit.prix_unitaire_eur * random.uniform(0.95, 1.05)  # Légère variation de prix
            montant_ligne = round(quantite * prix, 2)
            montant_total += montant_ligne
            lignes.append(LigneCommande(
                produit=produit,
                quantite=quantite,
                prix_unitaire=round(prix, 2),
                montant_ligne=montant_ligne
            ))

        commande = Commande(
            numero_commande=f"CMD-{year}-{str(i+1).zfill(4)}",
            client=random.choice(clients),
            date_commande=date_commande,
            date_livraison_prevue=date_livraison_prevue,
            date_livraison_reelle=date_livraison_reelle,
            statut=statut,
            montant_total_eur=round(montant_total, 2),
            lignes=lignes
        )
        commandes.append(commande)

    return commandes


def generate_reclamations(clients: list[Client], commandes: list[Commande], n: int = 60) -> list[Reclamation]:
    # On ne prend que les commandes livrées ou expédiées pour les réclamations
    commandes_eligibles = [c for c in commandes if c.statut in (
        StatutCommandeEnum.livree, StatutCommandeEnum.expediee
    )]

    reclamations = []
    for i in range(min(n, len(commandes_eligibles))):
        commande = random.choice(commandes_eligibles)
        date_ouverture = commande.date_commande + timedelta(days=random.randint(5, 30))

        statut = random.choice(list(StatutReclamationEnum))
        date_cloture = None
        if statut == StatutReclamationEnum.cloturee:
            date_cloture = date_ouverture + timedelta(days=random.randint(3, 30))

        reclamations.append(Reclamation(
            numero_ticket=f"REC-{date_ouverture.year}-{str(i+1).zfill(4)}",
            client=commande.client,
            commande=commande,
            date_ouverture=date_ouverture,
            date_cloture=date_cloture,
            type=random.choice(list(TypeReclamationEnum)),
            statut=statut,
            description=fake.sentence(nb_words=12),
            priorite=random.choices(
                list(PrioriteEnum),
                weights=[50, 35, 15]  # Majorité basse priorité, peu de haute
            )[0]
        ))

    return reclamations


# --- Main ---

def seed():
    db = SessionLocal()
    try:
        print("🌱 Génération des données...")

        clients = generate_clients(40)
        db.add_all(clients)
        db.flush()  # flush pour obtenir les IDs sans commit
        print(f"  ✅ {len(clients)} clients")

        produits = generate_produits()
        db.add_all(produits)
        db.flush()
        print(f"  ✅ {len(produits)} produits")

        commandes = generate_commandes(clients, produits, 600)
        db.add_all(commandes)
        db.flush()
        print(f"  ✅ {len(commandes)} commandes")

        reclamations = generate_reclamations(clients, commandes, 60)
        db.add_all(reclamations)
        db.flush()
        print(f"  ✅ {len(reclamations)} réclamations")

        db.commit()
        print("\n🎉 Base de données peuplée avec succès !")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()