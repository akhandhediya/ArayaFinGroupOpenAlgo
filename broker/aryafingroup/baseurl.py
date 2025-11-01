"""Arya broker base URLs configuration."""

from urllib.parse import urlparse

class URLConfig:
    """Configuration object for Arya broker URLs."""
    HOST_LOOKUP_URL = "http://xtstradingnse.aryafingroup.in:3000/hostlookup"
    BASE_URL = "http://xtstradingnse.aryafingroup.in:3000"
    
    @classmethod
    def _update_derived_urls(cls):
        """Update derived URLs based on current BASE_URL."""
        # Extract just the scheme and netloc (domain) part
        parsed = urlparse(cls.BASE_URL)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        cls.MARKET_DATA_URL = f"{base_domain}/apimarketdata"
        cls.INTERACTIVE_URL = f"{cls.BASE_URL}"
    
    @classmethod
    def update_base_url(cls, new_base_url):
        """Update base URL and regenerate all derived URLs."""
        cls.BASE_URL = new_base_url
        cls._update_derived_urls()

# Initialize derived URLs
URLConfig._update_derived_urls()
