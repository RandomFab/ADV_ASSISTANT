# backend/tests/unit/mcp/test_delivery.py

from datetime import date, timedelta
from src.mcp.tools.delivery import get_delivery_estimate
from src.database.models import Commande, StatutCommandeEnum


class TestGetDeliveryEstimate:
    """Test suite for get_delivery_estimate MCP tool."""

    def test_pending_order_estimation(self, mcp_test_env, db_with_seed):
        """Test estimation for 'en_attente' status."""
        result = get_delivery_estimate("CMD-2024-0002")

        assert result["found"] is True
        assert result["numero_commande"] == "CMD-2024-0002"
        assert result["statut"] == "en_attente"
        assert "Livraison estimée le" in result["estimation_livraison"]

    def test_order_not_found(self, mcp_test_env):
        """Test delivery estimate for non-existent order."""
        result = get_delivery_estimate("CMD-9999-9999")

        assert result["found"] is False
        assert "non trouvée" in result["message"].lower()

    def test_delivered_order_shows_real_date(self, mcp_test_env):
        """Test that delivered order shows actual delivery date."""
        result = get_delivery_estimate("CMD-2024-0001")

        assert result["found"] is True
        assert result["statut"] == "livree"
        assert "Livrée le :" in result["estimation_livraison"]

    def test_cancelled_order(self, mcp_test_env, db_with_seed):
        """Test estimation for cancelled order."""
        # Create a cancelled order
        from src.database.models import Client
        client = db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()

        cancelled_order = Commande(
            numero_commande="CMD-2024-9999",
            client_id=client.id,
            date_commande=date.today() - timedelta(days=5),
            date_livraison_prevue=date.today() + timedelta(days=5),
            statut=StatutCommandeEnum.annulee,
            montant_total_eur=1000.0
        )
        db_with_seed.add(cancelled_order)
        db_with_seed.commit()

        result = get_delivery_estimate("CMD-2024-9999")

        assert result["found"] is True
        assert result["statut"] == "annulee"
        assert "annulée" in result["estimation_livraison"].lower()

    def test_shipped_order_shows_planned_date(self, mcp_test_env, db_with_seed):
        """Test that shipped order shows planned delivery date."""
        from src.database.models import Client
        client = db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()

        shipped_order = Commande(
            numero_commande="CMD-2024-8888",
            client_id=client.id,
            date_commande=date.today() - timedelta(days=15),
            date_livraison_prevue=date.today() + timedelta(days=3),
            statut=StatutCommandeEnum.expediee,
            montant_total_eur=2000.0
        )
        db_with_seed.add(shipped_order)
        db_with_seed.commit()

        result = get_delivery_estimate("CMD-2024-8888")

        assert result["found"] is True
        assert result["statut"] == "expediee"
        assert "Date prévue de livraison" in result["estimation_livraison"]

    def test_pending_order_calculates_max_delay(self, mcp_test_env, db_with_seed):
        """Test that estimation uses max manufacturing delay + 5 days."""
        from src.database.models import Client, LigneCommande
        client = db_with_seed.query(Client).filter_by(nom_entreprise="Acme Corp").first()

        order = Commande(
            numero_commande="CMD-2024-7777",
            client_id=client.id,
            date_commande=date.today(),
            date_livraison_prevue=date.today() + timedelta(days=10),
            statut=StatutCommandeEnum.en_attente,
            montant_total_eur=1000.0
        )
        db_with_seed.add(order)
        db_with_seed.flush()

        # Get a product and add a line with known manufacturing delay
        from src.database.models import Produit
        produit = db_with_seed.query(Produit).filter_by(reference="COIL-304-2MM").first()

        ligne = LigneCommande(
            commande_id=order.id,
            produit_id=produit.id,
            quantite=1,
            prix_unitaire=1200.0,
            montant_ligne=1200.0
        )
        db_with_seed.add(ligne)
        db_with_seed.commit()

        result = get_delivery_estimate("CMD-2024-7777")

        assert result["found"] is True
        # Estimation should be date_commande + max_delai + 5 = today + 5 + 5 = today + 10
        expected_date = (date.today() + timedelta(days=10)).isoformat()
        assert expected_date in result["estimation_livraison"]

    def test_client_name_in_response(self, mcp_test_env):
        """Test that client name is included in response."""
        result = get_delivery_estimate("CMD-2024-0001")

        assert result["client"] == "Acme Corp"

    def test_response_schema(self, mcp_test_env):
        """Test complete response schema."""
        result = get_delivery_estimate("CMD-2024-0001")

        required_fields = [
            "found", "numero_commande", "client", "statut", "estimation_livraison"
        ]
        for field in required_fields:
            assert field in result
