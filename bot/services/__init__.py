"""
External services package
"""

from .speech_service import SpeechService
from .ocr_service import OCRService
from .pdf_service import PDFService
from .qr_service import QRService
from .url_service import URLService

__all__ = [
    'SpeechService',
    'OCRService',
    'PDFService',
    'QRService',
    'URLService'
]
