"""Testes para os exportadores."""
import pytest
import tempfile
import json
import csv
from pathlib import Path
from datetime import datetime
from core.models import Post, PostMetrics, CollectionResult, CollectionParams
from exporters import DocxExporter, JsonExporter, CsvExporter


@pytest.fixture
def sample_posts():
    """Posts de exemplo para testes."""
    return [
        Post(
            post_id="123456789",
            url="https://x.com/user1/status/123456789",
            datetime=datetime(2024, 1, 15, 14, 30),
            author_name="Usuário Teste",
            author_handle="user1",
            text="Este é um post de teste #teste @mention",
            metrics=PostMetrics(likes=100, reposts=20, replies=5, views=1000),
            hashtags=["#teste"],
            mentions=["@mention"],
            is_reply=False,
            is_repost=False,
        ),
        Post(
            post_id="987654321",
            url="https://x.com/user2/status/987654321",
            datetime=datetime(2024, 1, 16, 10, 0),
            author_name="Outro Usuário",
            author_handle="user2",
            text="Outro post de teste",
            is_reply=True,
        ),
    ]


@pytest.fixture
def sample_result(sample_posts):
    """Resultado de coleta de exemplo."""
    return CollectionResult(
        posts=sample_posts,
        query_or_url="from:user1",
        params=CollectionParams(max_posts=100),
        total_collected=len(sample_posts),
        stop_reason="max_posts",
    )


class TestDocxExporter:
    """Testes do exportador DOCX."""
    
    def test_export_creates_file(self, sample_result):
        """Testa se o arquivo DOCX é criado."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = DocxExporter(tmpdir)
            filepath = exporter.export(sample_result, "test.docx")
            
            assert Path(filepath).exists()
            assert filepath.endswith(".docx")
    
    def test_export_with_empty_posts(self):
        """Testa exportação com lista vazia."""
        result = CollectionResult(posts=[], query_or_url="test", total_collected=0)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = DocxExporter(tmpdir)
            filepath = exporter.export(result)
            
            assert Path(filepath).exists()


class TestJsonExporter:
    """Testes do exportador JSON."""
    
    def test_export_creates_valid_json(self, sample_result):
        """Testa se o JSON é válido."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = JsonExporter(tmpdir)
            filepath = exporter.export(sample_result)
            
            with open(filepath) as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "posts" in data
            assert len(data["posts"]) == 2
    
    def test_export_posts_only(self, sample_posts):
        """Testa exportação apenas de posts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = JsonExporter(tmpdir)
            filepath = exporter.export_posts_only(sample_posts)
            
            with open(filepath) as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) == 2


class TestCsvExporter:
    """Testes do exportador CSV."""
    
    def test_export_creates_valid_csv(self, sample_result):
        """Testa se o CSV é válido."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CsvExporter(tmpdir)
            filepath = exporter.export(sample_result)
            
            with open(filepath) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert "post_id" in rows[0]
            assert "text" in rows[0]
    
    def test_export_has_correct_columns(self, sample_result):
        """Testa se as colunas estão corretas."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exporter = CsvExporter(tmpdir)
            filepath = exporter.export(sample_result)
            
            with open(filepath) as f:
                reader = csv.reader(f)
                header = next(reader)
            
            assert "post_id" in header
            assert "url" in header
            assert "author_handle" in header
            assert "text" in header
            assert "likes" in header
