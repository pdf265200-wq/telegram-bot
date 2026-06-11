"""
QR Code generation service
"""

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image, ImageDraw, ImageFont
import io
import logging

logger = logging.getLogger(__name__)

class QRService:
    """Service for generating QR codes"""
    
    def __init__(self):
        self.default_size = 10
        self.default_border = 4
        
    def generate_qr(self, text: str, fill_color: str = "black", back_color: str = "white"):
        """Generate QR code from text"""
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=self.default_size,
                border=self.default_border,
            )
            
            # Add data
            qr.add_data(text)
            qr.make(fit=True)
            
            # Create image with styling
            img = qr.make_image(
                fill_color=fill_color,
                back_color=back_color,
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer()
            )
            
            # Convert to bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            return img_byte_arr, None
            
        except Exception as e:
            logger.error(f"QR generation error: {e}")
            return None, str(e)
    
    def generate_custom_qr(self, text: str, size: int = 10, border: int = 4,
                          fill_color: str = "black", back_color: str = "white"):
        """Generate QR code with custom parameters"""
        try:
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=size,
                border=border,
            )
            
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(
                fill_color=fill_color,
                back_color=back_color
            )
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            
            return img_byte_arr.getvalue(), None
            
        except Exception as e:
            logger.error(f"Custom QR generation error: {e}")
            return None, str(e)
