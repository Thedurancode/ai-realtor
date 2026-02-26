"""
Tests for Property Video Router endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from app.routers import property_videos


class TestPropertyVideoRouter:
    """Test suite for property video endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client without authentication."""
        test_app = FastAPI()
        test_app.include_router(property_videos.router)
        return TestClient(test_app)

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        return db

    @pytest.fixture
    def mock_property(self):
        """Create a mock property."""
        property = Mock()
        property.id = 1
        property.address = "123 Main St"
        property.city = "Miami"
        property.state = "FL"
        property.price = 500000
        property.bedrooms = 3
        property.bathrooms = 2.0
        property.square_feet = 1500
        property.property_type.value = "house"
        property.description = "Beautiful family home"
        return property

    @pytest.fixture
    def mock_enrichment(self):
        """Create a mock enrichment."""
        enrichment = Mock()
        enrichment.zestimate = 520000
        enrichment.year_built = 2020
        enrichment.lot_size = 5000
        enrichment.description = "Stunning property with modern amenities and great features"
        enrichment.photos = '[]'
        return enrichment

    def test_script_preview_success(self, client, mock_db, mock_property):
        """Test script-preview endpoint."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,  # Property query
            None  # Enrichment query
        ]

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            response = client.post(
                "/v1/property-videos/script-preview?property_id=1"
            )

            assert response.status_code == 200
            data = response.json()
            assert "script" in data
            assert "property_id" in data

    def test_script_preview_with_enrichment(self, client, mock_db, mock_property, mock_enrichment):
        """Test script generation with enrichment data."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,
            mock_enrichment
        ]

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            response = client.post(
                "/v1/property-videos/script-preview?property_id=1"
            )

            assert response.status_code == 200
            data = response.json()
            assert "script" in data
            assert "Stunning property" in data["script"]

    def test_script_preview_property_not_found(self, client, mock_db):
        """Test script generation with non-existent property."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            response = client.post(
                "/v1/property-videos/script-preview?property_id=999"
            )

            assert response.status_code == 404

    def test_generate_voiceover_success(self, client, mock_db, mock_property):
        """Test voiceover generation endpoint."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,
            None
        ]

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            with patch('app.services.property_video_service.PropertyVideoService._generate_voiceover', new_callable=AsyncMock) as mock_voiceover:
                mock_voiceover.return_value = "/tmp/test_audio.mp3"

                response = client.post(
                    "/v1/property-videos/voiceover",
                    json={
                        "property_id": 1,
                        "agent_id": 5,
                        "voice_id": "test-voice-id"
                    }
                )

                assert response.status_code == 201
                data = response.json()
                assert "audio_path" in data
                assert "script" in data
                assert "duration_seconds" in data
                assert "word_count" in data
                assert data["property_id"] == 1

    def test_generate_voiceover_property_not_found(self, client, mock_db):
        """Test voiceover generation with non-existent property."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            response = client.post(
                "/v1/property-videos/voiceover",
                json={
                    "property_id": 999,
                    "agent_id": 5
                }
            )

            assert response.status_code == 404

    def test_generate_voiceover_custom_voice(self, client, mock_db, mock_property):
        """Test voiceover generation with custom voice ID."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,
            None
        ]

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            with patch('app.services.property_video_service.PropertyVideoService._generate_voiceover', new_callable=AsyncMock) as mock_voiceover:
                mock_voiceover.return_value = "/tmp/test_audio.mp3"

                response = client.post(
                    "/v1/property-videos/voiceover",
                    json={
                        "property_id": 1,
                        "agent_id": 5,
                        "voice_id": "custom-voice-id-123"
                    }
                )

                assert response.status_code == 201
                data = response.json()
                assert data["voice_id"] == "custom-voice-id-123"

    def test_generate_voiceover_custom_output_dir(self, client, mock_db, mock_property):
        """Test voiceover generation with custom output directory."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,
            None
        ]

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            with patch('app.services.property_video_service.PropertyVideoService._generate_voiceover', new_callable=AsyncMock) as mock_voiceover:
                mock_voiceover.return_value = "/custom/path/test_audio.mp3"

                response = client.post(
                    "/v1/property-videos/voiceover",
                    json={
                        "property_id": 1,
                        "agent_id": 5,
                        "output_dir": "/custom/path"
                    }
                )

                assert response.status_code == 201

    def test_calculate_duration_from_script(self, client, mock_db, mock_property):
        """Test that voiceover endpoint calculates duration correctly."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,
            None
        ]

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            with patch('app.services.property_video_service.PropertyVideoService._generate_voiceover', new_callable=AsyncMock) as mock_voiceover:
                mock_voiceover.return_value = "/tmp/test_audio.mp3"

                response = client.post(
                    "/v1/property-videos/voiceover",
                    json={
                        "property_id": 1,
                        "agent_id": 5
                    }
                )

                assert response.status_code == 201
                data = response.json()
                # Duration should be calculated (word_count / 2.5)
                assert data["duration_seconds"] > 0
                assert data["word_count"] > 0

    def test_default_voice_id(self, client, mock_db, mock_property):
        """Test that default voice ID is used when not specified."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,
            None
        ]

        with patch('app.routers.property_videos.get_db', return_value=mock_db):
            with patch('app.services.property_video_service.PropertyVideoService._generate_voiceover', new_callable=AsyncMock) as mock_voiceover:
                mock_voiceover.return_value = "/tmp/test_audio.mp3"

                response = client.post(
                    "/v1/property-videos/voiceover",
                    json={
                        "property_id": 1,
                        "agent_id": 5
                    }
                )

                assert response.status_code == 201
                data = response.json()
                # Should use default voice ID
                assert data["voice_id"] == "21m00Tcm4TlvDq8ikWAM"

    def test_get_voices(self, client):
        """Test getting available voices endpoint."""
        with patch('app.services.property_video_service.PropertyVideoService.get_available_voices') as mock_get_voices:
            mock_get_voices.return_value = [
                {"voice_id": "voice-1", "name": "Test Voice", "category": "generated"}
            ]

            response = client.get("/v1/property-videos/voices")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["voice_id"] == "voice-1"

    def test_invalid_property_id(self, client):
        """Test endpoints with invalid property ID."""
        response = client.post(
            "/v1/property-videos/script-preview",
            json={
                "property_id": "invalid",
                "agent_id": 5
            }
        )

        # Should return validation error
        assert response.status_code == 422

    def test_missing_required_field_property_id(self, client):
        """Test endpoint with missing property_id field."""
        response = client.post(
            "/v1/property-videos/voiceover",
            json={
                "agent_id": 5
            }
        )

        assert response.status_code == 422

    def test_missing_required_field_property_id(self, client):
        """Test script-preview endpoint without property_id parameter."""
        response = client.post(
            "/v1/property-videos/script-preview"
        )

        assert response.status_code == 422
