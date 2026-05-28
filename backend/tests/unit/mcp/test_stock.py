# backend/tests/unit/mcp/test_stock.py

from src.mcp.tools.stock import get_stock_level


class TestGetStockLevel:
    """Test suite for get_stock_level MCP tool."""

    def test_search_by_exact_reference(self, mcp_test_env):
        """Test finding product by exact reference."""
        result = get_stock_level(reference="COIL-304-2MM")

        assert result["found"] is True
        assert result["reference"] == "COIL-304-2MM"
        assert result["stock_disponible"] == 100
        assert result["stock_reserve"] == 20

    def test_search_by_keyword(self, mcp_test_env):
        """Test finding product by keyword in designation."""
        result = get_stock_level(mot_cle="inox")

        assert result["found"] is True
        assert "304" in result["designation"].lower() or "inox" in result["designation"].lower()

    def test_search_by_multiple_keywords(self, mcp_test_env, db_with_seed):
        """Test finding product by multiple keywords."""
        result = get_stock_level(mot_cle="coil inox")

        assert result["found"] is True
        assert "coil" in result["designation"].lower()
        assert "inox" in result["designation"].lower()

    def test_stock_net_calculation(self, mcp_test_env):
        """Test that stock_net = stock_disponible - stock_reserve."""
        result = get_stock_level(reference="COIL-304-2MM")

        expected_net = result["stock_disponible"] - result["stock_reserve"]
        assert result["stock_net"] == expected_net
        assert result["stock_net"] == 80  # 100 - 20

    def test_product_not_found(self, mcp_test_env):
        """Test searching for non-existent product."""
        result = get_stock_level(reference="NONEXISTENT-REF")

        assert result["found"] is False
        assert "non trouvé" in result["message"].lower()

    def test_keyword_not_found(self, mcp_test_env):
        """Test keyword search with no matches."""
        result = get_stock_level(mot_cle="titanium")

        assert result["found"] is False

    def test_case_insensitive_keyword(self, mcp_test_env):
        """Test that keyword search is case-insensitive."""
        result1 = get_stock_level(mot_cle="inox")
        result2 = get_stock_level(mot_cle="INOX")

        assert result1["found"] == result2["found"]
        if result1["found"]:
            assert result1["reference"] == result2["reference"]

    def test_partial_keyword_match(self, mcp_test_env):
        """Test partial keyword matching."""
        result = get_stock_level(mot_cle="304")

        assert result["found"] is True
        assert "304" in result["designation"]

    def test_response_schema(self, mcp_test_env):
        """Test complete response schema."""
        result = get_stock_level(reference="COIL-304-2MM")

        required_fields = [
            "found", "reference", "designation", "stock_disponible",
            "stock_reserve", "stock_net"
        ]
        for field in required_fields:
            assert field in result

    def test_zero_stock_reserve(self, mcp_test_env, db_with_seed):
        """Test product with zero stock reserved."""
        from src.database.models import Produit

        # Create a product with no reserved stock
        produit = Produit(
            reference="TEST-ZERO-RESERVE",
            designation="Test Product Zero Reserve",
            famille="coil",
            matiere="acier",
            nuance="S235",
            epaisseur_mm=1.0,
            prix_unitaire_eur=500.0,
            poids_kg_ml=2.5,
            stock_disponible=50,
            stock_reserve=0,
            delai_fabrication_jours=3
        )
        db_with_seed.add(produit)
        db_with_seed.commit()

        result = get_stock_level(reference="TEST-ZERO-RESERVE")

        assert result["found"] is True
        assert result["stock_net"] == 50

    def test_stock_reserve_greater_than_available(self, mcp_test_env, db_with_seed):
        """Test edge case where reserved stock > available (inconsistent state)."""
        from src.database.models import Produit

        produit = Produit(
            reference="TEST-NEGATIVE-NET",
            designation="Test Negative Net Stock",
            famille="coil",
            matiere="acier",
            nuance="S235",
            epaisseur_mm=1.0,
            prix_unitaire_eur=500.0,
            poids_kg_ml=2.5,
            stock_disponible=10,
            stock_reserve=20,  # Reserve > Available
            delai_fabrication_jours=3
        )
        db_with_seed.add(produit)
        db_with_seed.commit()

        result = get_stock_level(reference="TEST-NEGATIVE-NET")

        assert result["found"] is True
        assert result["stock_net"] == -10  # Negative net stock
