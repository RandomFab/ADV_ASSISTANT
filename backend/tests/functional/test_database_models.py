# backend/tests/functional/test_database_models.py

from datetime import datetime, timedelta
from src.database.models import (
    Client,
    Produit,
    Commande,
    LigneCommande,
    Reclamation,
    SecteurEnum,
    FamilleEnum,
    MatiereEnum,
    StatutCommandeEnum,
    TypeReclamationEnum,
    StatutReclamationEnum,
    PrioriteEnum,
)


class TestClientModel:
    """Test suite for Client model."""

    def test_create_client(self, db_session):
        """Test creating a client."""
        client = Client(
            nom_entreprise="Test Corp",
            secteur=SecteurEnum.automobile,
            zone_geo="Paris",
            commercial_attitre="Agent Test",
            conditions_paiement="30j",
            email="test@corp.com",
            telephone="+33600000000",
        )
        db_session.add(client)
        db_session.commit()

        retrieved = (
            db_session.query(Client).filter_by(nom_entreprise="Test Corp").first()
        )
        assert retrieved is not None
        assert retrieved.nom_entreprise == "Test Corp"

    def test_client_enum_values(self, db_session):
        """Test client with different sector enums."""
        for secteur in [
            SecteurEnum.btp,
            SecteurEnum.automobile,
            SecteurEnum.agroalimentaire,
        ]:
            client = Client(
                nom_entreprise=f"Corp {secteur.value}",
                secteur=secteur,
                zone_geo="Test",
                commercial_attitre="Test",
                conditions_paiement="30j",
                email="test@test.com",
                telephone="+33600000000",
            )
            db_session.add(client)

        db_session.commit()

        clients = db_session.query(Client).all()
        assert len(clients) >= 3

    def test_client_relationships(self, db_session, db_with_seed):
        """Test client relationships with commandes and reclamations."""
        client = (
            db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()
        )

        assert len(client.commandes) > 0
        assert hasattr(client, "reclamations")


class TestProduitModel:
    """Test suite for Produit model."""

    def test_create_product(self, db_session):
        """Test creating a product."""
        produit = Produit(
            reference="TEST-001",
            designation="Test Product",
            famille=FamilleEnum.coil,
            matiere=MatiereEnum.acier,
            nuance="S235",
            epaisseur_mm=2.0,
            prix_unitaire_eur=500.0,
            poids_kg_ml=3.5,
            stock_disponible=100,
            stock_reserve=10,
        )
        db_session.add(produit)
        db_session.commit()

        retrieved = db_session.query(Produit).filter_by(reference="TEST-001").first()
        assert retrieved is not None
        assert retrieved.designation == "Test Product"

    def test_product_enum_values(self, db_session):
        """Test product with different families and materials."""
        families = [FamilleEnum.coil, FamilleEnum.tube, FamilleEnum.tole]
        matieres = [MatiereEnum.acier, MatiereEnum.inox, MatiereEnum.aluminium]

        for family in families:
            for matiere in matieres:
                produit = Produit(
                    reference=f"PROD-{family.value}-{matiere.value}",
                    designation=f"{family.value} {matiere.value}",
                    famille=family,
                    matiere=matiere,
                    nuance="Test",
                    epaisseur_mm=1.0,
                    prix_unitaire_eur=100.0,
                    poids_kg_ml=1.0,
                )
                db_session.add(produit)

        db_session.commit()

        produits = db_session.query(Produit).all()
        assert len(produits) >= 9

    def test_product_stock_calculation(self, db_session):
        """Test product stock fields."""
        produit = Produit(
            reference="STOCK-TEST",
            designation="Stock Test",
            famille=FamilleEnum.coil,
            matiere=MatiereEnum.acier,
            nuance="S235",
            epaisseur_mm=2.0,
            prix_unitaire_eur=500.0,
            poids_kg_ml=3.5,
            stock_disponible=100,
            stock_reserve=30,
        )
        db_session.add(produit)
        db_session.commit()

        retrieved = db_session.query(Produit).filter_by(reference="STOCK-TEST").first()
        assert retrieved.stock_disponible == 100
        assert retrieved.stock_reserve == 30
        # Net calculation should be: 100 - 30 = 70
        net = retrieved.stock_disponible - retrieved.stock_reserve
        assert net == 70


class TestCommandeModel:
    """Test suite for Commande model."""

    def test_create_order(self, db_session, db_with_seed):
        """Test creating an order."""
        client = db_with_seed.query(Client).first()

        commande = Commande(
            numero_commande="TEST-CMD-001",
            client_id=client.id,
            date_commande=datetime.utcnow(),
            date_livraison_prevue=datetime.utcnow() + timedelta(days=10),
            statut=StatutCommandeEnum.en_attente,
            montant_total_eur=1000.0,
        )
        db_with_seed.add(commande)
        db_with_seed.commit()

        retrieved = (
            db_with_seed.query(Commande)
            .filter_by(numero_commande="TEST-CMD-001")
            .first()
        )
        assert retrieved is not None
        assert retrieved.statut == StatutCommandeEnum.en_attente

    def test_order_enum_values(self, db_session, db_with_seed):
        """Test order with different status enums."""
        client = db_with_seed.query(Client).first()

        for statut in StatutCommandeEnum:
            commande = Commande(
                numero_commande=f"CMD-ENUM-{statut.value}",
                client_id=client.id,
                date_commande=datetime.utcnow(),
                date_livraison_prevue=datetime.utcnow() + timedelta(days=10),
                statut=statut,
                montant_total_eur=500.0,
            )
            db_with_seed.add(commande)

        db_with_seed.commit()

        commandes = db_with_seed.query(Commande).all()
        assert len(commandes) >= 5

    def test_order_client_relationship(self, db_session, db_with_seed):
        """Test order relationship with client."""
        commande = db_with_seed.query(Commande).first()

        assert commande.client is not None
        assert commande.client.nom_entreprise is not None

    def test_order_lines_relationship(self, db_session, db_with_seed):
        """Test order relationship with lines."""
        commande = db_with_seed.query(Commande).first()

        # Commande should have lines
        assert hasattr(commande, "lignes")


class TestLigneCommandeModel:
    """Test suite for LigneCommande model."""

    def test_create_order_line(self, db_session, db_with_seed):
        """Test creating an order line."""
        commande = db_with_seed.query(Commande).first()
        produit = db_with_seed.query(Produit).first()

        ligne = LigneCommande(
            commande_id=commande.id,
            produit_id=produit.id,
            quantite=5,
            prix_unitaire=100.0,
            montant_ligne=500.0,
        )
        db_with_seed.add(ligne)
        db_with_seed.commit()

        retrieved = (
            db_with_seed.query(LigneCommande)
            .filter_by(commande_id=commande.id, produit_id=produit.id)
            .order_by(LigneCommande.id.desc())
            .first()
        )

        assert retrieved is not None
        assert retrieved.quantite == 5

    def test_ligne_relationships(self, db_session, db_with_seed):
        """Test line relationships with commande and produit."""
        ligne = db_with_seed.query(LigneCommande).first()

        assert ligne.commande is not None
        assert ligne.produit is not None


class TestReclamationModel:
    """Test suite for Reclamation model."""

    def test_create_reclamation(self, db_session, db_with_seed):
        """Test creating a reclamation."""
        client = db_with_seed.query(Client).first()
        commande = db_with_seed.query(Commande).first()

        reclamation = Reclamation(
            numero_ticket="REC-TEST-001",
            client_id=client.id,
            commande_id=commande.id,
            date_ouverture=datetime.utcnow(),
            type=TypeReclamationEnum.defaut_soudure,
            statut=StatutReclamationEnum.ouverte,
            description="Test defect",
            priorite=PrioriteEnum.haute,
        )
        db_with_seed.add(reclamation)
        db_with_seed.commit()

        retrieved = (
            db_with_seed.query(Reclamation)
            .filter_by(numero_ticket="REC-TEST-001")
            .first()
        )

        assert retrieved is not None
        assert retrieved.statut == StatutReclamationEnum.ouverte

    def test_reclamation_enum_values(self, db_session, db_with_seed):
        """Test reclamation with different type enums."""
        client = db_with_seed.query(Client).first()

        for rec_type in TypeReclamationEnum:
            reclamation = Reclamation(
                numero_ticket=f"REC-TYPE-{rec_type.value}",
                client_id=client.id,
                date_ouverture=datetime.utcnow(),
                type=rec_type,
                statut=StatutReclamationEnum.ouverte,
                description="Test",
                priorite=PrioriteEnum.moyenne,
            )
            db_with_seed.add(reclamation)

        db_with_seed.commit()

        reclamations = db_with_seed.query(Reclamation).all()
        assert len(reclamations) >= 5

    def test_reclamation_status_enum(self, db_session, db_with_seed):
        """Test reclamation status values."""
        client = db_with_seed.query(Client).first()

        for statut in StatutReclamationEnum:
            reclamation = Reclamation(
                numero_ticket=f"REC-STATUS-{statut.value}",
                client_id=client.id,
                date_ouverture=datetime.utcnow(),
                type=TypeReclamationEnum.retard_livraison,
                statut=statut,
                description="Test",
                priorite=PrioriteEnum.basse,
            )
            db_with_seed.add(reclamation)

        db_with_seed.commit()

        reclamations = (
            db_with_seed.query(Reclamation)
            .filter(Reclamation.numero_ticket.like("REC-STATUS%"))
            .all()
        )
        assert len(reclamations) >= 3

    def test_reclamation_closed_with_date(self, db_session, db_with_seed):
        """Test closed reclamation has close date."""
        client = db_with_seed.query(Client).first()

        close_date = datetime.utcnow()
        reclamation = Reclamation(
            numero_ticket="REC-CLOSED-001",
            client_id=client.id,
            date_ouverture=close_date - timedelta(days=5),
            date_cloture=close_date,
            type=TypeReclamationEnum.defaut_soudure,
            statut=StatutReclamationEnum.cloturee,
            description="Fixed",
            priorite=PrioriteEnum.basse,
        )
        db_with_seed.add(reclamation)
        db_with_seed.commit()

        retrieved = (
            db_with_seed.query(Reclamation)
            .filter_by(numero_ticket="REC-CLOSED-001")
            .first()
        )

        assert retrieved.date_cloture is not None

    def test_reclamation_client_relationship(self, db_session, db_with_seed):
        """Test reclamation relationship with client."""
        reclamation = db_with_seed.query(Reclamation).first()

        assert reclamation.client is not None


class TestDatabaseIntegration:
    """Integration tests for database relationships."""

    def test_full_workflow(self, db_session, db_with_seed):
        """Test complete workflow: client -> commande -> ligne -> produit."""
        # Get client
        client = (
            db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()
        )
        assert client is not None

        # Verify commandes
        assert len(client.commandes) > 0

        # Get first commande
        commande = client.commandes[0]
        assert commande.client_id == client.id

        # Verify lines
        assert len(commande.lignes) > 0

        # Get first line
        ligne = commande.lignes[0]
        assert ligne.commande_id == commande.id
        assert ligne.produit_id is not None

        # Verify product
        produit = ligne.produit
        assert produit is not None
        assert produit.id == ligne.produit_id

    def test_cascade_relationships(self, db_session, db_with_seed):
        """Test that relationships cascade properly."""
        client = (
            db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()
        )

        # Verify all related objects are accessible
        assert len(client.commandes) > 0

        for commande in client.commandes:
            assert commande.client_id == client.id
            assert len(commande.lignes) > 0

            for ligne in commande.lignes:
                assert ligne.commande_id == commande.id
                assert ligne.produit is not None
