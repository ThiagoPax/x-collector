"""Construtor de URLs de busca do X."""
from typing import Optional, Dict
from urllib.parse import urlencode, quote
from datetime import datetime, timedelta
from core.models import CollectionParams, SearchType


class URLBuilder:
    """Constrói URLs de busca para o X."""
    
    BASE_URL = "https://x.com/search"
    
    @staticmethod
    def build_search_url(
        query: str,
        params: CollectionParams
    ) -> str:
        """
        Constrói URL de busca a partir de uma query.
        
        Args:
            query: Query de busca (ex: "from:user since:2024-01-01")
            params: Parâmetros de coleta
            
        Returns:
            URL completa de busca
        """
        # Adicionar filtros à query se necessário
        enhanced_query = URLBuilder._enhance_query(query, params)
        
        # Parâmetros da URL
        url_params = {
            "q": enhanced_query,
            "src": "typed_query",
        }
        
        # Tipo de busca (top ou latest)
        if params.search_type == SearchType.LATEST:
            url_params["f"] = "live"
        # Para TOP, não precisa do parâmetro f
        
        return f"{URLBuilder.BASE_URL}?{urlencode(url_params, quote_via=quote)}"
    
    @staticmethod
    def _enhance_query(query: str, params: CollectionParams) -> str:
        """Adiciona filtros à query baseado nos parâmetros."""
        parts = [query]
        
        # Filtro de idioma
        if params.language:
            parts.append(f"lang:{params.language}")
        
        # Filtro de período em minutos (tem prioridade sobre max_days)
        if params.max_minutes:
            since_time = datetime.utcnow() - timedelta(minutes=params.max_minutes)
            # Formato: YYYY-MM-DD_HH:mm:ss_UTC
            since_str = since_time.strftime("%Y-%m-%d_%H:%M:%S") + "_UTC"
            if "since:" not in query.lower():
                parts.append(f"since:{since_str}")
        # Filtro de data em dias (se não tiver minutos)
        elif params.max_days:
            since_date = (datetime.now() - timedelta(days=params.max_days)).strftime("%Y-%m-%d")
            if "since:" not in query.lower():
                parts.append(f"since:{since_date}")
        
        # Filtros de tipo de post
        filters = []
        if not params.include_replies:
            filters.append("-filter:replies")
        if not params.include_reposts:
            filters.append("-filter:retweets")
        # Quotes não têm filtro direto, serão filtrados na extração
        
        parts.extend(filters)
        
        return " ".join(parts)
    
    @staticmethod
    def is_valid_x_url(url: str) -> bool:
        """Verifica se é uma URL válida do X."""
        valid_domains = ["x.com", "twitter.com", "mobile.twitter.com", "mobile.x.com"]
        url_lower = url.lower()
        return any(domain in url_lower for domain in valid_domains)
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normaliza URL (twitter.com -> x.com)."""
        return url.replace("twitter.com", "x.com").replace("mobile.x.com", "x.com")
    
    @staticmethod
    def extract_query_from_url(url: str) -> Optional[str]:
        """Extrai a query de uma URL de busca."""
        from urllib.parse import urlparse, parse_qs
        
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            if "q" in params:
                return params["q"][0]
        except Exception:
            pass
        return None


def build_example_queries() -> Dict[str, str]:
    """Retorna exemplos de queries avançadas."""
    return {
        "Posts de um usuário": "from:username",
        "Menções a um usuário": "@username",
        "Hashtag específica": "#hashtag",
        "Posts com links": "filter:links",
        "Posts com mídia": "filter:media",
        "Posts com imagens": "filter:images",
        "Posts com vídeos": "filter:videos",
        "Combinação (AND)": "python AND machine learning",
        "Alternativas (OR)": "python OR javascript",
        "Excluir termo": "python -java",
        "Frase exata": '"machine learning"',
        "De um usuário para outro": "from:user1 to:user2",
        "Por período": "from:username since:2024-01-01 until:2024-06-01",
        "Mínimo de likes": "from:username min_faves:100",
        "Mínimo de retweets": "from:username min_retweets:50",
        "Verificados apenas": "from:username filter:verified",
        "Idioma específico": "machine learning lang:pt",
    }
