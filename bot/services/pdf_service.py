"""
PDF processing service
"""

import PyPDF2
import img2pdf
from PIL import Image
import io
import os
import logging
from typing import List

logger = logging.getLogger(__name__)

class PDFService:
    """Service for PDF operations"""
    
    def __init__(self):
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    
    async def images_to_pdf(self, image_paths: List[str], output_path: str = None) -> tuple:
        """Convert images to PDF"""
        try:
            # Validate images
            valid_images = []
            for img_path in image_paths:
                try:
                    img = Image.open(img_path)
                    valid_images.append(img_path)
                except Exception as e:
                    logger.warning(f"Invalid image {img_path}: {e}")
            
            if not valid_images:
                return None, "No valid images provided"
            
            # Convert to PDF
            pdf_bytes = img2pdf.convert(valid_images)
            
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
                return output_path, None
            
            return pdf_bytes, None
            
        except Exception as e:
            logger.error(f"Images to PDF conversion error: {e}")
            return None, str(e)
    
    async def merge_pdfs(self, pdf_paths: List[str], output_path: str = None) -> tuple:
        """Merge multiple PDFs"""
        try:
            merger = PyPDF2.PdfMerger()
            
            for pdf_path in pdf_paths:
                try:
                    merger.append(pdf_path)
                except Exception as e:
                    logger.warning(f"Failed to add {pdf_path}: {e}")
            
            if output_path:
                merger.write(output_path)
                merger.close()
                return output_path, None
            
            # Write to bytes
            pdf_bytes = io.BytesIO()
            merger.write(pdf_bytes)
            merger.close()
            return pdf_bytes.getvalue(), None
            
        except Exception as e:
            logger.error(f"PDF merging error: {e}")
            return None, str(e)
    
    async def extract_text_from_pdf(self, pdf_path: str, pages: List[int] = None) -> tuple:
        """Extract text from PDF"""
        try:
            extracted_text = []
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Get total pages
                total_pages = len(reader.pages)
                
                # Determine which pages to extract
                if pages:
                    target_pages = [p for p in pages if 0 <= p < total_pages]
                else:
                    target_pages = range(total_pages)
                
                for page_num in target_pages:
                    try:
                        page = reader.pages[page_num]
                        text = page.extract_text()
                        if text.strip():
                            extracted_text.append(f"--- Page {page_num + 1} ---\n{text}")
                    except Exception as e:
                        logger.warning(f"Failed to extract text from page {page_num}: {e}")
                
                full_text = '\n\n'.join(extracted_text)
                
                if not full_text.strip():
                    return None, "No text could be extracted from the PDF"
                
                return full_text, None
                
        except Exception as e:
            logger.error(f"PDF text extraction error: {e}")
            return None, str(e)
    
    async def get_pdf_info(self, pdf_path: str) -> dict:
        """Get PDF file information"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                info = {
                    'pages': len(reader.pages),
                    'encrypted': reader.is_encrypted,
                    'metadata': {}
                }
                
                if reader.metadata:
                    info['metadata'] = {
                        'title': reader.metadata.get('/Title', 'N/A'),
                        'author': reader.metadata.get('/Author', 'N/A'),
                        'creator': reader.metadata.get('/Creator', 'N/A'),
                        'producer': reader.metadata.get('/Producer', 'N/A'),
                        'subject': reader.metadata.get('/Subject', 'N/A')
                    }
                
                return info, None
                
        except Exception as e:
            logger.error(f"PDF info extraction error: {e}")
            return None, str(e)
    
    async def split_pdf(self, pdf_path: str, page_range: tuple = None) -> tuple:
        """Split PDF into multiple files or extract specific pages"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                writer = PyPDF2.PdfWriter()
                
                total_pages = len(reader.pages)
                
                if page_range:
                    start, end = page_range
                    pages_to_extract = range(max(0, start), min(end, total_pages))
                else:
                    pages_to_extract = range(total_pages)
                
                for page_num in pages_to_extract:
                    writer.add_page(reader.pages[page_num])
                
                pdf_bytes = io.BytesIO()
                writer.write(pdf_bytes)
                
                return pdf_bytes.getvalue(), None
                
        except Exception as e:
            logger.error(f"PDF splitting error: {e}")
            return None, str(e)
