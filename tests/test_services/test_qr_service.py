"""
Tests for QR Code Service
"""

import pytest
from bot.services.qr_service import QRService
import io

@pytest.fixture
def qr_service():
    return QRService()

class TestQRService:
    """Test QR code service"""
    
    def test_generate_qr_with_url(self, qr_service):
        """Test QR code generation with URL"""
        result, error = qr_service.generate_qr("https://example.com")
        
        assert result is not None
        assert error is None
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_generate_qr_with_text(self, qr_service):
        """Test QR code generation with text"""
        result, error = qr_service.generate_qr("Hello World")
        
        assert result is not None
        assert error is None
        assert isinstance(result, bytes)
    
    def test_generate_qr_with_empty_text(self, qr_service):
        """Test QR code with empty text"""
        result, error = qr_service.generate_qr("")
        
        # Should still generate QR code for empty string
        assert result is not None
        assert error is None
    
    def test_generate_custom_qr(self, qr_service):
        """Test custom QR code generation"""
        result, error = qr_service.generate_custom_qr(
            "Test",
            size=20,
            border=2,
            fill_color="blue",
            back_color="yellow"
        )
        
        assert result is not None
        assert error is None
        assert isinstance(result, bytes)
    
    def test_qr_image_is_valid_png(self, qr_service):
        """Test that generated QR is valid PNG"""
        from PIL import Image
        
        result, error = qr_service.generate_qr("Test")
        assert result is not None
        
        # Verify it's a valid PNG image
        img = Image.open(io.BytesIO(result))
        assert img.format == 'PNG'
