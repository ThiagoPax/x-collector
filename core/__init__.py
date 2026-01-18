"""Core module for X Posts Collector."""
from core.models import (
    Post,
    PostMetrics,
    CollectionParams,
    CollectionResult,
    SearchType,
    Job,
    JobStatus,
    Schedule,
    ScheduleType,
    RunHistory,
    RunStatus,
)
from core.collector import XCollector, quick_collect, CollectorConfig
from core.extractor import PostExtractor
from core.url_builder import URLBuilder, build_example_queries
from core.chrome_manager import (
    is_chrome_running,
    get_chrome_status,
    start_chrome,
    stop_chrome,
    restart_chrome,
    get_chrome_log,
)

__all__ = [
    "Post",
    "PostMetrics",
    "CollectionParams",
    "CollectionResult",
    "SearchType",
    "Job",
    "JobStatus",
    "Schedule",
    "ScheduleType",
    "RunHistory",
    "RunStatus",
    "XCollector",
    "quick_collect",
    "CollectorConfig",
    "PostExtractor",
    "URLBuilder",
    "build_example_queries",
    "is_chrome_running",
    "get_chrome_status",
    "start_chrome",
    "stop_chrome",
    "restart_chrome",
    "get_chrome_log",
]
