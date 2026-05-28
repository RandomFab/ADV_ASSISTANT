# backend/tests/unit/mcp/test_clients.py

from src.mcp.tools.clients import get_client_info


class TestGetClientInfo:
    """Test suite for get_client_info MCP tool."""

    def test_client_found_with_exact_name(self, mcp_test_env):
        """Test retrieving a client with exact name match."""
        result = get_client_info("Acme Corp")

        assert result["found"] is True
        assert result["nom_entreprise"] == "Acme Corp"
        assert result["commercial_attitre"] == "Jean Dupont"
        assert result["ca_cumule_eur"] == 5000.0  # Only delivered order
        assert len(result["commandes"]) == 2

    def test_client_found_with_fuzzy_search(self, mcp_test_env):
        """Test fuzzy search (ILIKE) for client name."""
        result = get_client_info("acme")
        assert result["found"] is True
        assert result["nom_entreprise"] == "Acme Corp"

    def test_client_found_with_partial_name(self, mcp_test_env):
        """Test partial name matching."""
        result = get_client_info("Ac")
        assert result["found"] is True
        assert result["nom_entreprise"] == "Acme Corp"

    def test_client_not_found(self, mcp_test_env):
        """Test non-existent client."""
        result = get_client_info("NonExistent Inc")
        assert result["found"] is False
        assert "non trouvé" in result["message"].lower()

    def test_ca_cumule_only_livree(self, mcp_test_env):
        """CA cumulé should only count delivered orders."""
        result = get_client_info("Acme Corp")
        # Only CMD-2024-0001 is "livree" with 5000.0
        assert result["ca_cumule_eur"] == 5000.0

    def test_commandes_sorted_by_date_desc(self, mcp_test_env):
        """Commandes should be sorted by date, most recent first."""
        result = get_client_info("Acme Corp")
        commandes = result["commandes"]

        # CMD-2024-0002 (en_attente) should be first (more recent)
        assert commandes[0]["numero_commande"] == "CMD-2024-0002"

    def test_commandes_limit_to_five(self, mcp_test_env, db_with_seed):
        """Should limit to 5 most recent commandes."""
        # Add 5 more orders to exceed the limit
        from src.database.models import Commande, StatutCommandeEnum
        from datetime import datetime, timedelta

        from src.database.models import Client
        client = db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()
        client_id = client.id

        for i in range(3, 8):
            cmd = Commande(
                numero_commande=f"CMD-2024-000{i}",
                client_id=client_id,
                date_commande=datetime.utcnow() - timedelta(days=10-i),
                date_livraison_prevue=datetime.utcnow() + timedelta(days=10),
                statut=StatutCommandeEnum.en_attente,
                montant_total_eur=1000.0
            )
            db_with_seed.add(cmd)
        db_with_seed.commit()

        result = get_client_info("Acme Corp")
        assert len(result["commandes"]) == 5

    def test_reclamations_included_in_commandes(self, mcp_test_env):
        """Réclamations should be nested in commandes."""
        result = get_client_info("Acme Corp")
        commandes = result["commandes"]

        # CMD-2024-0001 has 1 reclamation
        cmd_with_rec = next(
            (c for c in commandes if c["numero_commande"] == "CMD-2024-0001"),
            None
        )
        assert cmd_with_rec is not None
        assert len(cmd_with_rec["reclamations"]) == 1
        assert cmd_with_rec["reclamations"][0]["numero_ticket"] == "REC-2024-0001"

    def test_commandes_with_no_reclamations(self, mcp_test_env):
        """Commandes without reclamations should have empty list."""
        result = get_client_info("Acme Corp")
        commandes = result["commandes"]

        cmd_no_rec = next(
            (c for c in commandes if c["numero_commande"] == "CMD-2024-0002"),
            None
        )
        assert cmd_no_rec is not None
        assert len(cmd_no_rec["reclamations"]) == 0

    def test_response_schema(self, mcp_test_env):
        """Test response has all required fields."""
        result = get_client_info("Acme Corp")

        required_fields = ["found", "nom_entreprise", "commercial_attitre", "ca_cumule_eur", "commandes"]
        for field in required_fields:
            assert field in result
