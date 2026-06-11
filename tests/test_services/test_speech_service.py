"""
Tests for Speech Service
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from bot.services.speech_service import SpeechService
import io

@pytest.fixture
def speech_service():
    """Create speech service instance"""
    return SpeechService()

class TestSpeechService:
    """Test speech service functionality"""
    
    def test_init(self, speech_service):
        """Test service initialization"""
        assert speech_service is not None
        assert '.ogg' in speech_service.supported_formats
        assert '.mp3' in speech_service.supported_formats
    
    @pytest.mark.asyncio
    async def test_text_to_speech_english(self, speech_service):
        """Test English text to speech conversion"""
        with patch('bot.services.speech_service.gTTS') as mock_gtts:
            # Setup mock
            mock_tts = MagicMock()
            mock_tts.write_to_fp = MagicMock()
            mock_gtts.return_value = mock_tts
            
            result, error = await speech_service.text_to_speech(
                "Hello World", language='en'
            )
            
            assert result is not None
            assert error is None
            assert isinstance(result, io.BytesIO)
    
    @pytest.mark.asyncio
    async def test_text_to_speech_arabic(self, speech_service):
        """Test Arabic text to speech conversion"""
        with patch('bot.services.speech_service.gTTS') as mock_gtts:
            mock_tts = MagicMock()
            mock_tts.write_to_fp = MagicMock()
            mock_gtts.return_value = mock_tts
            
            result, error = await speech_service.text_to_speech(
                "مرحبا بالعالم", language='ar'
            )
            
            assert result is not None
            assert error is None
    
    @pytest.mark.asyncio
    async def test_text_to_speech_empty_text(self, speech_service):
        """Test TTS with empty text"""
        result, error = await speech_service.text_to_speech("")
        
        # Should handle empty text gracefully
        assert result is None or error is not None
    
    @pytest.mark.asyncio
    async def test_text_to_speech_slow_mode(self, speech_service):
        """Test TTS in slow mode"""
        with patch('bot.services.speech_service.gTTS') as mock_gtts:
            mock_tts = MagicMock()
            mock_tts.write_to_fp = MagicMock()
            mock_gtts.return_value = mock_tts
            
            result, error = await speech_service.text_to_speech(
                "Test", language='en', slow=True
            )
            
            assert result is not None
            assert error is None
            # Verify slow parameter was passed
            mock_gtts.assert_called_with(text="Test", lang='en', slow=True)
    
    @pytest.mark.asyncio
    async def test_voice_to_text_english(self, speech_service):
        """Test English voice to text"""
        # Create a mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'dummy audio data')
            temp_path = f.name
        
        try:
            with patch('bot.services.speech_service.sr.Recognizer') as mock_recognizer:
                mock_recognizer_instance = MagicMock()
                mock_recognizer_instance.recognize_google.return_value = "Hello World"
                mock_recognizer.return_value = mock_recognizer_instance
                
                # Mock AudioFile context manager
                with patch('bot.services.speech_service.sr.AudioFile'):
                    text, lang = await speech_service.voice_to_text(
                        temp_path, language='en'
                    )
                    
                    assert text == "Hello World"
                    assert lang == 'en'
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_voice_to_text_auto_detect(self, speech_service):
        """Test automatic language detection"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'dummy audio data')
            temp_path = f.name
        
        try:
            with patch('bot.services.speech_service.sr.Recognizer') as mock_recognizer:
                mock_recognizer_instance = MagicMock()
                # Arabic first, then English fallback
                mock_recognizer_instance.recognize_google.side_effect = [
                    Exception("Arabic failed"),
                    "Hello World"
                ]
                mock_recognizer.return_value = mock_recognizer_instance
                
                with patch('bot.services.speech_service.sr.AudioFile'):
                    text, lang = await speech_service.voice_to_text(temp_path)
                    
                    assert text == "Hello World"
                    assert lang == 'en'
        finally:
            os.unlink(temp_path)
