"""
OCR (Optical Character Recognition) service
"""

import pytesseract
from PIL import Image
import cv2
import numpy as np
import logging
from bot.config import Config

logger = logging.getLogger(__name__)

class OCRService:
    """Service for extracting text from images"""
    
    def __init__(self):
        # Set tesseract path if configured
        if Config.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_PATH
        
        self.supported_languages = {
            'en': 'eng',
            'ar': 'ara',
            'en+ar': 'eng+ara'
        }
    
    async def extract_text(self, image_path: str, language: str = 'en+ar'):
        """Extract text from image"""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(image)
            
            # Get language code
            lang_code = self.supported_languages.get(language, 'eng+ara')
            
            # Extract text
            text = pytesseract.image_to_string(
                processed_image,
                lang=lang_code,
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Clean text
            text = self.clean_text(text)
            
            return text, None
            
        except pytesseract.TesseractNotFoundError:
            return None, "Tesseract OCR is not installed. Please install it on your server."
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return None, str(e)
    
    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert PIL image to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding to preprocess the image
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # Apply dilation to connect text components (useful for Arabic)
            kernel = np.ones((1, 1), np.uint8)
            gray = cv2.dilate(gray, kernel, iterations=1)
            
            # Apply blur to smooth the image
            gray = cv2.medianBlur(gray, 3)
            
            return gray
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return np.array(image)
    
    def clean_text(self, text: str) -> str:
        """Clean extracted text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
    
    def get_available_languages(self) -> list:
        """Get list of available OCR languages"""
        try:
            languages = pytesseract.get_languages()
            return [lang for lang in languages if lang in ['eng', 'ara']]
        except:
            return ['eng', 'ara']
    
    async def extract_text_with_confidence(self, image_path: str, language: str = 'en+ar'):
        """Extract text with confidence scores"""
        try:
            image = Image.open(image_path)
            processed_image = self.preprocess_image(image)
            
            lang_code = self.supported_languages.get(language, 'eng+ara')
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                processed_image,
                lang=lang_code,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = []
            for i, conf in enumerate(data['conf']):
                if conf > 0:
                    confidences.append(conf)
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract text
            text = self.clean_text(' '.join(data['text']))
            
            return {
                'text': text,
                'confidence': avg_confidence,
                'word_count': len(text.split()),
                'language': language
            }, None
            
        except Exception as e:
            logger.error(f"OCR extraction with confidence error: {e}")
            return None, str(e)
