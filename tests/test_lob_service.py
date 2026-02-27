"""
Tests for Lob.com Direct Mail Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.lob_service import LobClient, DirectMailService
from app.schemas.direct_mail import PostcardSize, LetterSize, MailType, MailStatus


class TestLobClient:
    """Test Lob.com API client"""

    def test_init_with_api_key(self):
        """Test client initialization with API key"""
        client = LobClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.test_mode is False

    def test_init_with_test_mode(self):
        """Test client initialization in test mode"""
        client = LobClient(api_key="test_key_123", test_mode=True)
        assert client.api_key == "test_key_123"
        assert client.test_mode is True

    def test_init_without_api_key_raises_error(self):
        """Test that initialization without API key raises error"""
        with patch('app.services.lob_service.settings.lob_api_key', ''):
            with pytest.raises(ValueError, match="LOB_API_KEY must be set"):
                LobClient()

    def test_status_mapping(self):
        """Test Lob status mapping to internal status"""
        client = LobClient(api_key="test_key")

        assert client.STATUS_MAPPING["draft"] == MailStatus.DRAFT
        assert client.STATUS_MAPPING["processed"] == MailStatus.PROCESSING
        assert client.STATUS_MAPPING["mailed"] == MailStatus.MAILED
        assert client.STATUS_MAPPING["in_transit"] == MailStatus.IN_TRANSIT
        assert client.STATUS_MAPPING["delivered"] == MailStatus.DELIVERED
        assert client.STATUS_MAPPING["canceled"] == MailStatus.CANCELLED
        assert client.STATUS_MAPPING["failed"] == MailStatus.FAILED

    @pytest.mark.asyncio
    async def test_verify_address_success(self):
        """Test successful address verification"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "addr_test123",
            "address_line1": "123 Main St",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "90210",
            "deliverability": "deliverable"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = LobClient(api_key="test_key")
            result = await client.verify_address({
                "address_line1": "123 Main St",
                "address_city": "Anytown",
                "address_state": "CA",
                "address_zip": "90210"
            })

            assert result["deliverability"] == "deliverable"
            assert result["address_line1"] == "123 Main St"

    @pytest.mark.asyncio
    async def test_verify_address_invalid(self):
        """Test address verification with invalid address"""
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "error": "Address not found"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = LobClient(api_key="test_key")
            result = await client.verify_address({
                "address_line1": "Invalid",
                "address_city": "Nowhere",
                "address_state": "XX",
                "address_zip": "00000"
            })

            assert result is None

    @pytest.mark.asyncio
    async def test_create_postcard_success(self):
        """Test successful postcard creation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "postcard_test123",
            "url": "https://lob.com/postcards/postcard_test123",
            "expected_delivery_date": "2026-03-01",
            "tracking": {
                "id": "track_test123"
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = LobClient(api_key="test_key")
            result = await client.create_postcard(
                to_address={"name": "John Doe", "address_line1": "123 Main St"},
                from_address={"name": "Agent", "address_line1": "456 Oak Ave"},
                front_html="<html>Test</html>",
                size="4x6"
            )

            assert result["id"] == "postcard_test123"
            assert result["url"] is not None

    @pytest.mark.asyncio
    async def test_create_letter_success(self):
        """Test successful letter creation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "letter_test123",
            "url": "https://lob.com/letters/letter_test123"
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = LobClient(api_key="test_key")
            result = await client.create_letter(
                to_address={"name": "John Doe", "address_line1": "123 Main St"},
                from_address={"name": "Agent", "address_line1": "456 Oak Ave"},
                file_url="https://example.com/letter.pdf"
            )

            assert result["id"] == "letter_test123"

    @pytest.mark.asyncio
    async def test_get_mailpiece(self):
        """Test retrieving mailpiece status"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "postcard_test123",
            "status": "processed",
            "tracking": {
                "status": "in_transit",
                "events": [
                    {"event": "processed", "time": "2026-02-26T10:00:00Z"}
                ]
            }
        }

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            client = LobClient(api_key="test_key")
            result = await client.get_mailpiece("postcard_test123")

            assert result["status"] == "processed"
            assert len(result["tracking"]["events"]) > 0


class TestDirectMailService:
    """Test DirectMailService high-level operations"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.rollback = Mock()
        db.query = Mock()
        return db

    @pytest.fixture
    def mock_agent(self):
        """Mock agent"""
        agent = Mock()
        agent.id = 1
        agent.full_name = "Test Agent"
        agent.brokerage = "Test Realty"
        agent.office_address = "123 Office St"
        agent.office_city = "Office City"
        agent.office_state = "CA"
        agent.office_zip = "90210"
        return agent

    @pytest.fixture
    def mock_property(self):
        """Mock property"""
        prop = Mock()
        prop.id = 1
        prop.address = "123 Main St"
        prop.city = "Anytown"
        prop.state = "CA"
        prop.zip_code = "90210"
        return prop

    def test_format_address_for_lob(self):
        """Test address formatting for Lob API"""
        from app.services.lob_service import DirectMailService

        address = {
            "name": "John Doe",
            "address_line1": "123 Main St",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "90210"
        }

        result = DirectMailService._format_address_for_lob(address)

        assert result["name"] == "John Doe"
        assert result["address_line1"] == "123 Main St"
        assert result["address_city"] == "Anytown"

    def test_extract_variables_from_template(self):
        """Test Jinja2 variable extraction"""
        from app.services.lob_service import DirectMailService
        import re

        html = "<div>{{property_address}} - {{sold_price}} - Fixed text</div>"
        variables = re.findall(r'\{\{(\w+)\}\}', html)

        assert "property_address" in variables
        assert "sold_price" in variables
        assert len(variables) == 2

    @pytest.mark.asyncio
    async def test_send_postcard_success(self, mock_db, mock_agent, mock_property):
        """Test successful postcard send"""
        from app.services.lob_service import DirectMailService
        from app.models.direct_mail import DirectMail, MailType, MailStatus

        # Mock Lob client response
        mock_lob_response = {
            "id": "lob_abc123",
            "url": "https://lob.com/postcards/lob_abc123",
            "expected_delivery_date": "2026-03-01"
        }

        with patch.object(LobClient, 'create_postcard', return_value=mock_lob_response):
            mock_db.query.return_value.filter.return_value.first.return_value = mock_agent

            service = DirectMailService(mock_db)
            result = await service.send_postcard(
                agent_id=1,
                to_address={
                    "name": "Property Owner",
                    "address_line1": "123 Main St",
                    "address_city": "Anytown",
                    "address_state": "CA",
                    "address_zip": "90210"
                },
                front_html="<html>Just Sold!</html>",
                size="4x6",
                property_id=1
            )

            assert result["lob_mailpiece_id"] == "lob_abc123"
            assert result["mail_status"] == MailStatus.PROCESSING
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
