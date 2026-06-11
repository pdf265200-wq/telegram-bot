"""
URL Shortening service
"""

import pyshorteners
import validators
import logging

logger = logging.getLogger(__name__)

class URLService:
    """Service for URL shortening"""
    
    def __init__(self):
        self.shortener = pyshorteners.Shortener()
        
    def shorten_url(self, url: str, service: str = 'tinyurl'):
        """Shorten a URL using specified service"""
        try:
            # Validate URL
            if not self.is_valid_url(url):
                return None, "Invalid URL format"
            
            # Check if URL is already short
            if len(url) < 30:
                return url, None
            
            # Try different services
            short_url = None
            error = None
            
            if service == 'tinyurl':
                try:
                    short_url = self.shortener.tinyurl.short(url)
                except Exception as e:
                    logger.warning(f"TinyURL failed: {e}")
                    error = f"TinyURL service error: {str(e)}"
            
            elif service == 'isgd':
                try:
                    short_url = self.shortener.isgd.short(url)
                except Exception as e:
                    logger.warning(f"is.gd failed: {e}")
                    error = f"is.gd service error: {str(e)}"
            
            elif service == 'dagd':
                try:
                    short_url = self.shortener.dagd.short(url)
                except Exception as e:
                    logger.warning(f"Da.gd failed: {e}")
                    error = f"Da.gd service error: {str(e)}"
            
            if short_url:
                return short_url, None
            else:
                return None, error or "Failed to shorten URL with all services"
            
        except Exception as e:
            logger.error(f"URL shortening error: {e}")
            return None, str(e)
    
    def is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL"""
        return validators.url(url) == True
    
    def expand_url(self, short_url: str):
        """Expand a shortened URL"""
        try:
            expanded_url = self.shortener.tinyurl.expand(short_url)
            return expanded_url, None
        except Exception as e:
            logger.error(f"URL expansion error: {e}")
            return None, str(e)
    
    def get_url_info(self, url: str):
        """Get basic URL information"""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            return {
                'scheme': parsed.scheme,
                'domain': parsed.netloc,
                'path': parsed.path,
                'is_secure': parsed.scheme == 'https',
                'length': len(url)
            }, None
        except Exception as e:
            return None, str(e)
