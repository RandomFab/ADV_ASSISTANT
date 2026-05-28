# backend/tests/unit/mcp/test_reclamations.py

from datetime import datetime, timedelta
from src.mcp.tools.reclamations import search_reclamations
from src.database.models import (
    Reclamation,
    Client,
    Commande,
    StatutReclamationEnum,
    TypeReclamationEnum,
    PrioriteEnum,
    StatutCommandeEnum,
)


class TestSearchReclamations:
    """Test suite for search_reclamations MCP tool."""

    def test_client_found_with_reclamations(self, mcp_test_env):
        """Test retrieving reclamations for existing client."""
        result = search_reclamations("Acme Corp")

        assert result["found"] is True
        assert result["client"] == "Acme Corp"
        assert len(result["reclamations"]) > 0
        assert "statistiques" in result

    def test_client_not_found(self, mcp_test_env):
        """Test searching for non-existent client."""
        result = search_reclamations("NonExistentClient Inc")

        assert result["found"] is False
        assert "non trouvé" in result["message"].lower()

    def test_fuzzy_search_client(self, mcp_test_env):
        """Test fuzzy search for client name."""
        result = search_reclamations("acme")

        assert result["found"] is True
        assert result["client"] == "Acme Corp"

    def test_reclamation_complete_data(self, mcp_test_env):
        """Test that reclamation has all required fields."""
        result = search_reclamations("Acme Corp")
        reclamations = result["reclamations"]

        if reclamations:
            rec = reclamations[0]
            required_fields = [
                "numero_ticket",
                "type",
                "statut",
                "priorite",
                "date_ouverture",
                "date_cloture",
                "commande_numero",
            ]
            for field in required_fields:
                assert field in rec

    def test_reclamation_details(self, mcp_test_env):
        """Test reclamation details are correctly populated."""
        result = search_reclamations("Acme Corp")
        reclamations = result["reclamations"]

        # Find the reclamation we seeded
        rec = next(
            (r for r in reclamations if r["numero_ticket"] == "REC-2024-0001"), None
        )
        assert rec is not None
        assert rec["type"] == "defaut_soudure"
        assert rec["statut"] == "ouverte"
        assert rec["priorite"] == "haute"
        assert rec["commande_numero"] == "CMD-2024-0001"

    def test_filter_by_status_opened(self, mcp_test_env):
        """Test filtering reclamations by 'ouverte' status."""
        result = search_reclamations("Acme Corp", StatutReclamationEnum.ouverte)

        if result["reclamations"]:
            for rec in result["reclamations"]:
                assert rec["statut"] == "ouverte"

    def test_filter_by_status_closed(self, mcp_test_env, db_with_seed):
        """Test filtering reclamations by 'cloturee' status."""
        # Create a closed reclamation
        client = (
            db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()
        )
        commande = (
            db_with_seed.query(Commande)
            .filter_by(numero_commande="CMD-2024-0001")
            .first()
        )

        closed_rec = Reclamation(
            numero_ticket="REC-2024-0002",
            client_id=client.id,
            commande_id=commande.id,
            date_ouverture=datetime.utcnow() - timedelta(days=10),
            date_cloture=datetime.utcnow() - timedelta(days=2),
            type=TypeReclamationEnum.retard_livraison,
            statut=StatutReclamationEnum.cloturee,
            description="Retard résolu",
            priorite=PrioriteEnum.moyenne,
        )
        db_with_seed.add(closed_rec)
        db_with_seed.commit()

        result = search_reclamations("Acme Corp", StatutReclamationEnum.cloturee)

        assert result["found"] is True
        assert len(result["reclamations"]) > 0
        for rec in result["reclamations"]:
            assert rec["statut"] == "cloturee"

    def test_statistics_count(self, mcp_test_env):
        """Test that statistics are correctly calculated."""
        result = search_reclamations("Acme Corp")
        stats = result["statistiques"]

        assert "nb_reclamations_total" in stats
        assert "nb_commandes" in stats
        assert "taux_reclamation" in stats

    def test_reclamation_rate_calculation(self, mcp_test_env):
        """Test reclamation rate is correctly calculated."""
        result = search_reclamations("Acme Corp")
        stats = result["statistiques"]

        # Client has 2 commandes and at least 1 reclamation
        nb_rec = stats["nb_reclamations_total"]
        nb_cmd = stats["nb_commandes"]
        expected_taux = (nb_rec / nb_cmd) * 100 if nb_cmd > 0 else 0

        assert stats["taux_reclamation"] == expected_taux

    def test_zero_division_protection(self, mcp_test_env, db_with_seed):
        """Test that zero division is protected when client has no commandes."""
        # Create a client with no commandes
        client_empty = Client(
            nom_entreprise="Empty Client",
            secteur="btp",
            zone_geo="Paris",
            commercial_attitre="Agent Test",
            conditions_paiement="30j",
            email="empty@test.com",
            telephone="+33600000000",
            date_creation=datetime.utcnow(),
        )
        db_with_seed.add(client_empty)
        db_with_seed.commit()

        result = search_reclamations("Empty Client")

        assert result["found"] is True
        stats = result["statistiques"]
        assert stats["taux_reclamation"] == 0.0  # No division by zero

    def test_client_without_reclamations(self, mcp_test_env, db_with_seed):
        """Test client with no reclamations."""
        # Create client with commande but no reclamations
        client = Client(
            nom_entreprise="Clean Client",
            secteur="automobile",
            zone_geo="Lyon",
            commercial_attitre="Agent Clean",
            conditions_paiement="60j",
            email="clean@test.com",
            telephone="+33700000000",
            date_creation=datetime.utcnow(),
        )
        db_with_seed.add(client)
        db_with_seed.flush()

        commande = Commande(
            numero_commande="CMD-2024-CLEAN",
            client_id=client.id,
            date_commande=datetime.utcnow(),
            date_livraison_prevue=datetime.utcnow() + timedelta(days=10),
            statut=StatutCommandeEnum.en_attente,
            montant_total_eur=1000.0,
        )
        db_with_seed.add(commande)
        db_with_seed.commit()

        result = search_reclamations("Clean Client")

        assert result["found"] is True
        assert len(result["reclamations"]) == 0
        assert result["statistiques"]["nb_reclamations_total"] == 0

    def test_date_cloture_null_when_open(self, mcp_test_env):
        """Test that open reclamations have null date_cloture."""
        result = search_reclamations("Acme Corp")

        # REC-2024-0001 is open
        rec = next(
            (
                r
                for r in result["reclamations"]
                if r["numero_ticket"] == "REC-2024-0001"
            ),
            None,
        )
        if rec:
            assert rec["date_cloture"] is None

    def test_response_schema(self, mcp_test_env):
        """Test complete response schema."""
        result = search_reclamations("Acme Corp")

        required_fields = ["found", "client", "reclamations", "statistiques"]
        for field in required_fields:
            assert field in result
