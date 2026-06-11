"""
Bot command handlers package
"""

from . import start
from . import voice_to_text
from . import text_to_speech
from . import qr_code
from . import url_shortener
from . import file_info
from . import ocr
from . import pdf_tools
from . import admin

__all__ = [
    'start',
    'voice_to_text',
    'text_to_speech',
    'qr_code',
    'url_shortener',
    'file_info',
    'ocr',
    'pdf_tools',
    'admin'
]
