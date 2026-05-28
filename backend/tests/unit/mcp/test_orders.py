# backend/tests/unit/mcp/test_orders.py

from src.mcp.tools.orders import get_order_status


class TestGetOrderStatus:
    """Test suite for get_order_status MCP tool."""

    def test_order_found(self, mcp_test_env):
        """Test retrieving an existing order."""
        result = get_order_status("CMD-2024-0001")

        assert result["found"] is True
        assert result["numero_commande"] == "CMD-2024-0001"
        assert result["statut"] == "livree"
        assert result["client"]["nom"] == "Acme Corp"
        assert result["client"]["commercial"] == "Jean Dupont"
        assert len(result["lignes"]) > 0

    def test_order_not_found(self, mcp_test_env):
        """Test retrieving a non-existent order."""
        result = get_order_status("CMD-9999-9999")

        assert result["found"] is False
        assert "non trouvée" in result["message"].lower()

    def test_order_with_delivery_dates(self, mcp_test_env):
        """Test order with both planned and actual delivery dates."""
        result = get_order_status("CMD-2024-0001")

        assert result["date_livraison_prevue"] is not None
        assert result["date_livraison_reelle"] is not None
        # date_livraison_reelle should be after date_livraison_prevue
        assert result["date_livraison_reelle"] > result["date_livraison_prevue"]

    def test_order_without_actual_delivery_date(self, mcp_test_env):
        """Test order without actual delivery date (not yet delivered)."""
        result = get_order_status("CMD-2024-0002")

        assert result["date_livraison_prevue"] is not None
        assert result["date_livraison_reelle"] is None

    def test_order_lines_populated(self, mcp_test_env):
        """Test that order lines are fully populated."""
        result = get_order_status("CMD-2024-0001")
        lignes = result["lignes"]

        assert len(lignes) == 1
        ligne = lignes[0]
        assert "produit_ref" in ligne
        assert "produit_designation" in ligne
        assert "quantite" in ligne
        assert "prix_unitaire" in ligne
        assert "montant_ligne" in ligne

    def test_ligne_quantite_and_amounts(self, mcp_test_env):
        """Test line quantity and amount calculations."""
        result = get_order_status("CMD-2024-0001")
        ligne = result["lignes"][0]

        assert ligne["quantite"] == 10
        assert ligne["prix_unitaire"] == 1200.0
        assert ligne["montant_ligne"] == 12000.0

    def test_product_reference_serialized(self, mcp_test_env):
        """Test that product reference is correctly serialized."""
        result = get_order_status("CMD-2024-0001")
        ligne = result["lignes"][0]

        assert ligne["produit_ref"] == "COIL-304-2MM"
        assert "304" in ligne["produit_designation"].lower()

    def test_montant_total_is_float(self, mcp_test_env):
        """Test that montant_total_eur is serialized as float (not Decimal)."""
        result = get_order_status("CMD-2024-0001")

        assert isinstance(result["montant_total_eur"], float)
        assert result["montant_total_eur"] == 5000.0

    def test_client_info_included(self, mcp_test_env):
        """Test that client information is included."""
        result = get_order_status("CMD-2024-0001")
        client = result["client"]

        assert client["nom"] == "Acme Corp"
        assert client["commercial"] == "Jean Dupont"
        assert client["email"] == "contact@acme.com"

    def test_response_schema(self, mcp_test_env):
        """Test complete response schema."""
        result = get_order_status("CMD-2024-0001")

        required_fields = [
            "found",
            "numero_commande",
            "statut",
            "date_commande",
            "date_livraison_prevue",
            "date_livraison_reelle",
            "montant_total_eur",
            "client",
            "lignes",
        ]
        for field in required_fields:
            assert field in result
