"""Módulo de envio de e-mails."""
from email_service.sender import (
    EmailConfig,
    EmailSender,
    send_collection_email,
    send_collection_email_sync,
    test_email_config,
)

__all__ = [
    "EmailConfig",
    "EmailSender",
    "send_collection_email",
    "send_collection_email_sync",
    "test_email_config",
]
