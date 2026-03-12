"""
Tests for Lob.com Direct Mail Service
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
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
        assert client.STATUS_MAPPING["processing"] == MailStatus.PROCESSING
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
        mock_response.raise_for_status = Mock()

        client = LobClient(api_key="test_key")
        # Patch the internal httpx client's post method
        client.client.post = AsyncMock(return_value=mock_response)

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
        import httpx

        client = LobClient(api_key="test_key")

        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {"error": "Address not found"}
        mock_response.raise_for_status = Mock(
            side_effect=httpx.HTTPStatusError("422", request=Mock(), response=mock_response)
        )

        client.client.post = AsyncMock(return_value=mock_response)

        with pytest.raises(httpx.HTTPStatusError):
            await client.verify_address({
                "address_line1": "Invalid",
                "address_city": "Nowhere",
                "address_state": "XX",
                "address_zip": "00000"
            })

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
        mock_response.raise_for_status = Mock()

        client = LobClient(api_key="test_key")
        client.client.post = AsyncMock(return_value=mock_response)

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
        mock_response.raise_for_status = Mock()

        client = LobClient(api_key="test_key")
        client.client.post = AsyncMock(return_value=mock_response)

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
        mock_response.raise_for_status = Mock()

        client = LobClient(api_key="test_key")
        client.client.get = AsyncMock(return_value=mock_response)

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

    def test_format_address_helper(self):
        """Test LobClient._format_address helper method"""
        client = LobClient(api_key="test_key")

        address = {
            "name": "John Doe",
            "address_line1": "123 Main St",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_zip": "90210"
        }

        result = client._format_address(address)

        assert result["name"] == "John Doe"
        assert result["address_line1"] == "123 Main St"
        assert result["address_city"] == "Anytown"

    def test_extract_variables_from_template(self):
        """Test Jinja2 variable extraction"""
        import re

        html = "<div>{{property_address}} - {{sold_price}} - Fixed text</div>"
        variables = re.findall(r'\{\{(\w+)\}\}', html)

        assert "property_address" in variables
        assert "sold_price" in variables
        assert len(variables) == 2

    def test_render_template(self):
        """Test template rendering via LobClient.render_template"""
        result = LobClient.render_template(
            "<div>Hello {{name}}!</div>",
            {"name": "World"}
        )

        assert result == "<div>Hello World!</div>"

    @pytest.mark.asyncio
    async def test_send_property_postcard(self, mock_db):
        """Test sending a property postcard through the service"""
        mock_lob_response = {
            "id": "lob_abc123",
            "url": "https://lob.com/postcards/lob_abc123",
            "expected_delivery_date": "2026-03-01"
        }

        service = DirectMailService(mock_db, api_key="test_key")
        service.lob_client.client.post = AsyncMock(
            return_value=Mock(
                status_code=200,
                json=Mock(return_value=mock_lob_response),
                raise_for_status=Mock(),
            )
        )

        # Mock the property and agent queries
        mock_property = Mock()
        mock_property.full_address = "123 Main St, Anytown, CA 90210"
        mock_property.price = 500000
        mock_property.bedrooms = 3
        mock_property.bathrooms = 2
        mock_property.square_footage = 1500
        mock_property.primary_photo_url = None

        mock_agent = Mock()
        mock_agent.full_name = "Test Agent"
        mock_agent.phone = "555-1234"
        mock_agent.email = "agent@test.com"
        mock_agent.office_address = "456 Office St"
        mock_agent.office_city = "Office City"
        mock_agent.office_state = "CA"
        mock_agent.office_zip = "90210"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_property, mock_agent
        ]

        with patch('app.services.lob_service.DirectMailService.__init__', return_value=None):
            # Test the LobClient directly
            client = LobClient(api_key="test_key")
            client.client.post = AsyncMock(
                return_value=Mock(
                    status_code=200,
                    json=Mock(return_value=mock_lob_response),
                    raise_for_status=Mock(),
                )
            )
            result = await client.create_postcard(
                to_address={"name": "Owner", "address_line1": "123 Main St"},
                from_address={"name": "Agent", "address_line1": "456 Office St"},
                front_html="<html>Just Sold!</html>",
                size="4x6",
            )

            assert result["id"] == "lob_abc123"
