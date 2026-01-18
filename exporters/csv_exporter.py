"""Exportador para CSV."""
from __future__ import annotations
import csv
import os
from datetime import datetime
from pathlib import Path
from core.models import Post, CollectionResult


class CsvExporter:
    """Exporta posts para CSV."""
    
    # Colunas do CSV
    COLUMNS = [
        "post_id",
        "url",
        "datetime",
        "author_name",
        "author_handle",
        "text",
        "likes",
        "reposts",
        "replies",
        "views",
        "hashtags",
        "mentions",
        "links",
        "media_urls",
        "is_reply",
        "is_repost",
        "is_quote",
        "collected_at",
    ]
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir or os.getenv("EXPORTS_DIR", "./exports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        result: CollectionResult,
        filename: str = None,
        delimiter: str = ",",
    ) -> str:
        """
        Exporta resultado da coleta para CSV.
        
        Args:
            result: Resultado da coleta
            filename: Nome do arquivo (opcional)
            delimiter: Delimitador (padrão: vírgula)
            
        Returns:
            Caminho do arquivo gerado
        """
        return self.export_posts(result.posts, filename, delimiter)
    
    def export_posts(
        self,
        posts: list[Post],
        filename: str = None,
        delimiter: str = ",",
    ) -> str:
        """Exporta lista de posts para CSV."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coleta_x_{timestamp}.csv"
        
        if not filename.endswith(".csv"):
            filename += ".csv"
        
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=delimiter)
            
            # Header
            writer.writerow(self.COLUMNS)
            
            # Dados
            for post in posts:
                row = [
                    post.post_id,
                    post.url,
                    post.datetime.isoformat() if post.datetime else "",
                    post.author_name,
                    post.author_handle,
                    post.text.replace("\n", " "),  # Remover quebras de linha
                    post.metrics.likes if post.metrics.likes is not None else "",
                    post.metrics.reposts if post.metrics.reposts is not None else "",
                    post.metrics.replies if post.metrics.replies is not None else "",
                    post.metrics.views if post.metrics.views is not None else "",
                    "|".join(post.hashtags),
                    "|".join(post.mentions),
                    "|".join(post.links),
                    "|".join(post.media_urls),
                    post.is_reply,
                    post.is_repost,
                    post.is_quote,
                    post.collected_at.isoformat(),
                ]
                writer.writerow(row)
        
        return str(filepath)


def export_to_csv(
    result: CollectionResult,
    output_dir: str = None,
    filename: str = None,
) -> str:
    """Função helper para exportar para CSV."""
    exporter = CsvExporter(output_dir)
    return exporter.export(result, filename)
