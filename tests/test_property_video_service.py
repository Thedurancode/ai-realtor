"""
Tests for PropertyVideoService.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import os
from app.services.property_video_service import PropertyVideoService


class TestPropertyVideoService:
    """Test suite for PropertyVideoService."""

    @pytest.fixture
    def service(self):
        """Create a PropertyVideoService instance with mocked API keys."""
        with patch.dict('os.environ', {
            'RENDER_API_KEY': 'test-render-key',
            'ELEVENLABS_API_KEY': 'test-eth-labs-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key'
        }):
            return PropertyVideoService()

    @pytest.fixture
    def mock_property(self):
        """Create a mock property object."""
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
        """Create a mock Zillow enrichment object."""
        enrichment = Mock()
        enrichment.zestimate = 520000
        enrichment.year_built = 2020
        enrichment.lot_size = 5000
        enrichment.description = "Stunning property with modern amenities and great features"
        enrichment.photos = '[]'
        # Make description subscriptable
        enrichment.__getitem__ = lambda self, key: str(self.description)[key]
        return enrichment

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = Mock()
        db.query.return_value.filter_by.return_value.first.return_value = None
        return db

    def test_generate_script_basic_property(self, service, mock_property, mock_enrichment):
        """Test script generation with basic property info."""
        script = service._generate_script(mock_property, mock_enrichment)

        assert script is not None
        assert len(script) > 0
        assert "123 Main St" in script
        assert "Miami" in script
        assert "$500,000" in script or "500,000" in script
        assert "3 bedrooms" in script.lower() or "3 bedroom" in script.lower()

    def test_generate_script_with_enrichment(self, service, mock_property, mock_enrichment):
        """Test script generation includes enrichment data."""
        script = service._generate_script(mock_property, mock_enrichment)

        assert script is not None
        # Should mention description from enrichment
        assert "Stunning property" in script

    def test_generate_script_without_enrichment(self, service, mock_property):
        """Test script generation works without enrichment data."""
        script = service._generate_script(mock_property, None)

        assert script is not None
        assert len(script) > 0
        assert "123 Main St" in script

    def test_generate_script_with_square_feet(self, service, mock_property):
        """Test script includes square footage."""
        script = service._generate_script(mock_property, None)

        assert script is not None
        assert "1,500" in script or "1500" in script

    def test_generate_script_with_bathrooms(self, service, mock_property):
        """Test script handles bathroom count correctly."""
        script = service._generate_script(mock_property, None)

        assert script is not None
        assert "2 bathrooms" in script or "2 bathroom" in script

    @pytest.mark.asyncio
    async def test_generate_voiceover_success(self, service):
        """Test successful voiceover generation."""
        script = "This is a test script for voiceover generation."

        with patch('app.services.property_video_service.ElevenLabs') as mock_elevenlabs:
            # Mock the audio generator
            mock_audio = MagicMock()
            mock_audio.__iter__ = Mock(return_value=iter([b'audio_data']))
            mock_client = Mock()
            mock_client.text_to_speech.convert = Mock(return_value=mock_audio)
            mock_elevenlabs.return_value = mock_client

            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                audio_path = await service._generate_voiceover(
                    script=script,
                    voice_id="test-voice-id",
                    output_dir="/tmp"
                )

                assert audio_path is not None
                assert "/tmp/" in audio_path
                assert ".mp3" in audio_path

    @pytest.mark.asyncio
    async def test_generate_voiceover_with_chunks(self, service):
        """Test voiceover generation handles audio chunks correctly."""
        script = "Test script with chunks."

        with patch('app.services.property_video_service.ElevenLabs') as mock_elevenlabs:
            # Mock multiple audio chunks
            mock_audio = MagicMock()
            mock_audio.__iter__ = Mock(return_value=iter([b'chunk1', b'chunk2', b'chunk3']))
            mock_client = Mock()
            mock_client.text_to_speech.convert = Mock(return_value=mock_audio)
            mock_elevenlabs.return_value = mock_client

            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file

                audio_path = await service._generate_voiceover(
                    script=script,
                    voice_id="test-voice-id"
                )

                assert audio_path is not None

    @pytest.mark.asyncio
    async def test_generate_voiceover_no_api_key(self, service):
        """Test voiceover generation fails without API key."""
        service.elevenlabs_api_key = None

        with pytest.raises(ValueError, match="ELEVENLABS_API_KEY environment variable not set"):
            await service._generate_voiceover(
                script="Test script",
                voice_id="test-voice-id"
            )

    @pytest.mark.asyncio
    async def test_render_video_success(self, service):
        """Test successful video rendering."""
        props = {
            "logoUrl": "https://example.com/logo.png",
            "companyName": "Test Realty",
            "propertyPhotos": []
        }
        duration_frames = 1800  # 60 seconds at 30fps

        with patch('app.services.property_video_service.asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful subprocess execution
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))

            mock_subprocess.return_value = mock_process

            with patch('shutil.copy'):
                with patch('os.makedirs'):
                    video_path = await service._render_video(
                        props=props,
                        duration_frames=duration_frames,
                        output_path="/tmp/test_video.mp4"
                    )

                    assert video_path is not None
                    assert ".mp4" in video_path

    @pytest.mark.asyncio
    async def test_render_video_failure(self, service):
        """Test video rendering failure handling."""
        props = {"test": "props"}
        duration_frames = 1800

        with patch('app.services.property_video_service.asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock failed subprocess execution
            mock_process = Mock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"Rendering failed"))

            mock_subprocess.return_value = mock_process

            with pytest.raises(Exception, match="Remotion render failed"):
                await service._render_video(
                    props=props,
                    duration_frames=duration_frames
                )

    @pytest.mark.asyncio
    async def test_render_video_directory_output(self, service):
        """Test video rendering with directory output path."""
        props = {
            "logoUrl": "https://example.com/logo.png",
            "companyName": "Test Realty",
            "propertyPhotos": []
        }
        duration_frames = 1800

        with patch('app.services.property_video_service.asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            with patch('os.path.exists', return_value=True):
                with patch('os.path.isdir', return_value=True):
                    with patch('shutil.copy'):
                        video_path = await service._render_video(
                            props=props,
                            duration_frames=duration_frames,
                            output_path="/tmp/output_dir/"
                        )

                        assert video_path is not None
                        assert "property_video_" in video_path

    @pytest.mark.asyncio
    async def test_render_video_file_output(self, service):
        """Test video rendering with specific file output path."""
        props = {
            "logoUrl": "https://example.com/logo.png",
            "companyName": "Test Realty",
            "propertyPhotos": []
        }
        duration_frames = 1800

        with patch('app.services.property_video_service.asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process

            with patch('shutil.copy'):
                with patch('os.makedirs'):
                    video_path = await service._render_video(
                        props=props,
                        duration_frames=duration_frames,
                        output_path="/tmp/output_dir/my_video.mp4"
                    )

                    assert video_path is not None
                    assert video_path == "/tmp/output_dir/my_video.mp4"

    @pytest.mark.asyncio
    async def test_generate_property_video_full_flow(self, service, mock_db, mock_property, mock_enrichment):
        """Test full property video generation flow."""
        # Setup mocks
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_property,  # Property query
            None,  # Brand query
            mock_enrichment  # Enrichment query
        ]

        with patch.object(service, '_generate_voiceover', new_callable=AsyncMock) as mock_voiceover:
            mock_voiceover.return_value = "/tmp/audio.mp3"

            with patch.object(service, '_render_video', new_callable=AsyncMock) as mock_render:
                mock_render.return_value = "/tmp/video.mp4"

                with patch('app.services.property_video_service.asyncio.create_subprocess_exec') as mock_ffmpeg:
                    mock_process = Mock()
                    mock_process.returncode = 0
                    mock_process.communicate = AsyncMock(return_value=(b"", b""))
                    mock_ffmpeg.return_value = mock_process

                    with patch('shutil.move'):
                        result = await service.generate_property_video(
                            db=mock_db,
                            property_id=1,
                            agent_id=5
                        )

                        assert result is not None
                        assert "video_path" in result
                        assert "audio_path" in result
                        assert "script" in result
                        assert result["property_id"] == 1

    def test_get_available_voices_no_api_key(self, service):
        """Test getting voices returns empty list without API key."""
        service.elevenlabs_api_key = None
        voices = service.get_available_voices()
        assert voices == []

    def test_get_available_voices_success(self, service):
        """Test getting available voices from ElevenLabs."""
        with patch('app.services.property_video_service.ElevenLabs') as mock_elevenlabs:
            mock_voice = Mock()
            mock_voice.voice_id = "voice-123"
            mock_voice.name = "Test Voice"
            mock_voice.category = "generated"

            mock_voices = Mock()
            mock_voices.voices = [mock_voice]

            mock_client = Mock()
            mock_client.voices.get_all.return_value = mock_voices
            mock_elevenlabs.return_value = mock_client

            voices = service.get_available_voices()

            assert len(voices) == 1
            assert voices[0]["voice_id"] == "voice-123"
            assert voices[0]["name"] == "Test Voice"
            assert voices[0]["category"] == "generated"

    def test_get_available_voices_error_handling(self, service):
        """Test getting voices handles errors gracefully."""
        with patch('app.services.property_video_service.ElevenLabs') as mock_elevenlabs:
            mock_client = Mock()
            mock_client.voices.get_all.side_effect = Exception("API Error")
            mock_elevenlabs.return_value = mock_client

            voices = service.get_available_voices()
            assert voices == []
