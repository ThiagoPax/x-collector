"""Testes para o extractor."""
import pytest
from core.extractor import PostExtractor


class TestPostExtractor:
    """Testes do PostExtractor."""
    
    def test_parse_metric_simple(self):
        """Testa parsing de métricas simples."""
        assert PostExtractor.parse_metric("123") == 123
        assert PostExtractor.parse_metric("0") == 0
        assert PostExtractor.parse_metric("999") == 999
    
    def test_parse_metric_with_k(self):
        """Testa parsing de métricas com K."""
        assert PostExtractor.parse_metric("1K") == 1000
        assert PostExtractor.parse_metric("1.5K") == 1500
        assert PostExtractor.parse_metric("12K") == 12000
    
    def test_parse_metric_with_m(self):
        """Testa parsing de métricas com M."""
        assert PostExtractor.parse_metric("1M") == 1000000
        assert PostExtractor.parse_metric("2.5M") == 2500000
    
    def test_parse_metric_empty(self):
        """Testa parsing de métricas vazias."""
        assert PostExtractor.parse_metric("") is None
        assert PostExtractor.parse_metric(None) is None
        assert PostExtractor.parse_metric("   ") is None
    
    def test_extract_post_id_from_url(self):
        """Testa extração de ID de URL."""
        url = "https://x.com/user/status/1234567890123456789"
        assert PostExtractor.extract_post_id_from_url(url) == "1234567890123456789"
        
        url2 = "https://twitter.com/user/status/9876543210"
        assert PostExtractor.extract_post_id_from_url(url2) == "9876543210"
        
        url3 = "https://x.com/home"
        assert PostExtractor.extract_post_id_from_url(url3) is None
    
    def test_extract_handle_from_url(self):
        """Testa extração de handle de URL."""
        url = "https://x.com/elonmusk/status/123"
        assert PostExtractor.extract_handle_from_url(url) == "elonmusk"
        
        url2 = "https://twitter.com/openai/status/456"
        assert PostExtractor.extract_handle_from_url(url2) == "openai"
