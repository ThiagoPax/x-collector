"""Modelos de dados para o X Posts Collector."""
from __future__ import annotations
from datetime import datetime as dt, timezone
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


def utc_now() -> dt:
    """Retorna datetime atual em UTC."""
    return dt.now(timezone.utc)


class PostMetrics(BaseModel):
    """Métricas de engajamento de um post."""
    likes: Optional[int] = None
    reposts: Optional[int] = None
    replies: Optional[int] = None
    views: Optional[int] = None


class Post(BaseModel):
    """Modelo de um post do X."""
    post_id: str
    url: str
    datetime: Optional[dt] = None
    author_name: str = ""
    author_handle: str = ""
    text: str = ""
    metrics: PostMetrics = Field(default_factory=PostMetrics)
    links: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    mentions: list[str] = Field(default_factory=list)
    media_urls: list[str] = Field(default_factory=list)
    is_reply: bool = False
    is_repost: bool = False
    is_quote: bool = False
    collected_at: dt = Field(default_factory=utc_now)

    def __hash__(self):
        return hash(self.post_id)

    def __eq__(self, other):
        if isinstance(other, Post):
            return self.post_id == other.post_id
        return False


class SearchType(str, Enum):
    """Tipo de busca no X."""
    TOP = "top"
    LATEST = "latest"


class CollectionParams(BaseModel):
    """Parâmetros de coleta."""
    search_type: SearchType = SearchType.LATEST
    max_posts: Optional[int] = 3000
    max_days: Optional[int] = None
    max_minutes: Optional[int] = None  # Período em minutos (10, 60, 1440, etc.)
    include_reposts: bool = True
    include_replies: bool = True
    include_quotes: bool = True
    language: Optional[str] = None


class ScheduleType(str, Enum):
    """Tipo de agendamento."""
    ONCE = "once"
    RECURRING = "recurring"


class JobStatus(str, Enum):
    """Status de um job."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class Schedule(BaseModel):
    """Configuração de agendamento."""
    type: ScheduleType = ScheduleType.ONCE
    run_at: Optional[dt] = None  # Para type=ONCE
    cron: Optional[str] = None  # Para type=RECURRING (ex: "0 7 * * *")
    timezone: str = "America/Sao_Paulo"


class Job(BaseModel):
    """Modelo de um job agendado."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    query_or_url: str
    is_url: bool = False
    params: CollectionParams = Field(default_factory=CollectionParams)
    schedule: Schedule = Field(default_factory=Schedule)
    email_recipients: list[str] = Field(default_factory=list)
    export_formats: list[str] = Field(default_factory=lambda: ["docx"])
    status: JobStatus = JobStatus.ACTIVE
    created_at: dt = Field(default_factory=utc_now)
    last_run: Optional[dt] = None
    dry_run: bool = False


class RunStatus(str, Enum):
    """Status de uma execução."""
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class RunHistory(BaseModel):
    """Histórico de execução de um job."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    job_name: str = ""
    started_at: dt = Field(default_factory=utc_now)
    finished_at: Optional[dt] = None
    status: RunStatus = RunStatus.RUNNING
    posts_collected: int = 0
    export_files: list[str] = Field(default_factory=list)
    email_sent: bool = False
    error_message: Optional[str] = None
    logs: list[str] = Field(default_factory=list)


class CollectionResult(BaseModel):
    """Resultado de uma coleta."""
    posts: list[Post] = Field(default_factory=list)
    query_or_url: str = ""
    params: CollectionParams = Field(default_factory=CollectionParams)
    started_at: dt = Field(default_factory=utc_now)
    finished_at: Optional[dt] = None
    total_collected: int = 0
    stop_reason: str = ""
    errors: list[str] = Field(default_factory=list)
