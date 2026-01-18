"""Exportador para JSON."""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from core.models import Post, CollectionResult


class DateTimeEncoder(json.JSONEncoder):
    """Encoder customizado para datetime."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class JsonExporter:
    """Exporta posts para JSON."""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or os.getenv("EXPORTS_DIR", "./exports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        result: CollectionResult,
        filename: str = None,
        pretty: bool = True,
    ) -> str:
        """
        Exporta resultado da coleta para JSON.
        
        Args:
            result: Resultado da coleta
            filename: Nome do arquivo (opcional)
            pretty: Se True, formata com indentação
            
        Returns:
            Caminho do arquivo gerado
        """
        # Converter para dict serializável
        data = {
            "metadata": {
                "query_or_url": result.query_or_url,
                "params": result.params.model_dump(),
                "started_at": result.started_at,
                "finished_at": result.finished_at,
                "total_collected": result.total_collected,
                "stop_reason": result.stop_reason,
                "errors": result.errors,
            },
            "posts": [post.model_dump() for post in result.posts],
        }
        
        # Gerar nome do arquivo
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coleta_x_{timestamp}.json"
        
        if not filename.endswith(".json"):
            filename += ".json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, cls=DateTimeEncoder, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, cls=DateTimeEncoder, ensure_ascii=False)
        
        return str(filepath)
    
    def export_posts_only(
        self,
        posts: list[Post],
        filename: str = None,
        pretty: bool = True,
    ) -> str:
        """Exporta apenas a lista de posts."""
        data = [post.model_dump() for post in posts]
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"posts_x_{timestamp}.json"
        
        if not filename.endswith(".json"):
            filename += ".json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, cls=DateTimeEncoder, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, cls=DateTimeEncoder, ensure_ascii=False)
        
        return str(filepath)


def export_to_json(
    result: CollectionResult,
    output_dir: str = None,
    filename: str = None,
) -> str:
    """Função helper para exportar para JSON."""
    exporter = JsonExporter(output_dir)
    return exporter.export(result, filename)
