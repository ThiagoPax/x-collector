"""Serviço de envio de e-mails com relatório diagnóstico."""
from __future__ import annotations
import os
import asyncio
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Union
import aiosmtplib
from dotenv import load_dotenv

load_dotenv()


class EmailConfig:
    """Configurações de e-mail do .env."""
    
    @staticmethod
    def get_config() -> dict:
        return {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "user": os.getenv("SMTP_USER", ""),
            "password": os.getenv("SMTP_PASS", ""),
            "from_email": os.getenv("FROM_EMAIL", ""),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        }
    
    @staticmethod
    def is_configured() -> bool:
        config = EmailConfig.get_config()
        return bool(config["user"] and config["password"] and config["from_email"])


class EmailSender:
    """Envia e-mails com anexos."""
    
    def __init__(self):
        self.config = EmailConfig.get_config()
    
    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        attachments: List[str] = None,
        html_body: str = None,
    ) -> bool:
        """
        Envia um e-mail.
        
        Args:
            to: Lista de destinatários
            subject: Assunto
            body: Corpo do e-mail (texto)
            attachments: Lista de caminhos de arquivos para anexar
            html_body: Corpo HTML (opcional)
            
        Returns:
            True se enviado com sucesso
        """
        if not EmailConfig.is_configured():
            print("⚠️ E-mail não configurado. Verifique as variáveis de ambiente.")
            return False
        
        try:
            # Criar mensagem
            msg = MIMEMultipart("alternative")
            msg["From"] = self.config["from_email"]
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject
            
            # Corpo do e-mail (texto e HTML)
            msg.attach(MIMEText(body, "plain", "utf-8"))
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            # Anexos
            if attachments:
                for filepath in attachments:
                    path = Path(filepath)
                    if not path.exists():
                        print(f"⚠️ Arquivo não encontrado: {filepath}")
                        continue
                    
                    # Ler arquivo
                    with open(filepath, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={path.name}",
                    )
                    msg.attach(part)
            
            # Enviar
            await aiosmtplib.send(
                msg,
                hostname=self.config["host"],
                port=self.config["port"],
                username=self.config["user"],
                password=self.config["password"],
                start_tls=self.config["use_tls"],
            )
            
            print(f"✅ E-mail enviado para: {', '.join(to)}")
            return True
        
        except Exception as e:
            print(f"❌ Erro ao enviar e-mail: {e}")
            return False


async def send_collection_email(
    recipients: List[str],
    result = None,
    query_or_url: str = "",
    attachments: List[str] = None,
    job_name: str = None,
    query: str = None,
    posts_count: int = None,
    diagnostic_report = None,
) -> bool:
    """
    Envia e-mail com resultado de coleta.
    
    Suporta duas formas de chamada:
    1. Com 'result' (CollectionResult) - nova forma
    2. Com 'job_name', 'query', 'posts_count' - forma antiga (retrocompatível)
    
    Args:
        recipients: Lista de destinatários
        result: CollectionResult (opcional)
        query_or_url: Query/URL usada (se result fornecido)
        attachments: Arquivos para anexar
        job_name: Nome do job (forma antiga)
        query: Query usada (forma antiga)
        posts_count: Total de posts (forma antiga)
        diagnostic_report: Relatório diagnóstico opcional
        
    Returns:
        True se enviado com sucesso
    """
    now = datetime.now()
    date_str = now.strftime("%d/%m/%Y às %H:%M")
    
    # Extrair dados do result ou usar parâmetros diretos
    if result is not None:
        _posts_count = result.total_collected
        _query = query_or_url or result.query_or_url
        _job_name = job_name or "Coleta Manual"
        posts = result.posts
    else:
        _posts_count = posts_count or 0
        _query = query or query_or_url or ""
        _job_name = job_name or "Coleta"
        posts = []
    
    # Gerar relatório diagnóstico se não fornecido e temos posts
    report_text = ""
    report_html = ""
    
    if diagnostic_report:
        report_text = diagnostic_report.to_text()
        report_html = diagnostic_report.to_html()
    elif posts:
        try:
            from core.analyzer import generate_diagnostic_report
            diagnostic_report = await generate_diagnostic_report(posts, _query)
            report_text = diagnostic_report.to_text()
            report_html = diagnostic_report.to_html()
        except Exception as e:
            print(f"⚠️ Não foi possível gerar relatório diagnóstico: {e}")
    
    # Calcular métricas
    total_likes = sum(p.metrics.likes or 0 for p in posts) if posts else 0
    total_views = sum(p.metrics.views or 0 for p in posts) if posts else 0
    total_reposts = sum(p.metrics.reposts or 0 for p in posts) if posts else 0
    
    subject = f"[X Collector] {_job_name} - {_posts_count} posts coletados"
    
    body = f"""
Olá!

A coleta "{_job_name}" foi concluída com sucesso.

📊 RESUMO DA COLETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Data/Hora: {date_str}
• Pesquisa: {_query}
• Posts coletados: {_posts_count}
• Total de curtidas: {total_likes:,}
• Total de visualizações: {total_views:,}
• Total de reposts: {total_reposts:,}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{report_text}

Os arquivos com os dados completos estão anexados a este e-mail.

--
X Posts Collector
Gerado automaticamente
    """.strip()
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #1DA1F2, #0d8ecf); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="margin: 0;">🐦 X Posts Collector</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Relatório de Coleta Automática</p>
        </div>
        
        <p>A coleta <strong>"{_job_name}"</strong> foi concluída com sucesso.</p>
        
        <div style="background: #f5f8fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h3 style="margin-top: 0; color: #14171a;">📊 Resumo da Coleta</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #e1e8ed;">
                    <td style="padding: 8px 0;"><strong>Data/Hora:</strong></td>
                    <td style="padding: 8px 0;">{date_str}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e1e8ed;">
                    <td style="padding: 8px 0;"><strong>Pesquisa:</strong></td>
                    <td style="padding: 8px 0; word-break: break-all;">{_query}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e1e8ed;">
                    <td style="padding: 8px 0;"><strong>Posts coletados:</strong></td>
                    <td style="padding: 8px 0; font-size: 1.2em; color: #1DA1F2;"><strong>{_posts_count}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #e1e8ed;">
                    <td style="padding: 8px 0;"><strong>Total de curtidas:</strong></td>
                    <td style="padding: 8px 0;">❤️ {total_likes:,}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e1e8ed;">
                    <td style="padding: 8px 0;"><strong>Total de visualizações:</strong></td>
                    <td style="padding: 8px 0;">👁️ {total_views:,}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Total de reposts:</strong></td>
                    <td style="padding: 8px 0;">🔁 {total_reposts:,}</td>
                </tr>
            </table>
        </div>
        
        {report_html}
        
        <div style="background: #e8f5fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0;">📎 Os arquivos com os dados completos estão anexados a este e-mail.</p>
        </div>
        
        <hr style="border: none; border-top: 1px solid #e1e8ed; margin: 30px 0;">
        <p style="color: #657786; font-size: 12px; text-align: center;">
            X Posts Collector - Gerado automaticamente em {date_str}
        </p>
    </body>
    </html>
    """
    
    sender = EmailSender()
    return await sender.send(
        to=recipients,
        subject=subject,
        body=body,
        html_body=html_body,
        attachments=attachments,
    )


def send_collection_email_sync(
    recipients: List[str],
    job_name: str = "Coleta",
    query: str = "",
    posts_count: int = 0,
    attachments: List[str] = None,
    result = None,
) -> bool:
    """Versão síncrona do send_collection_email."""
    return asyncio.run(
        send_collection_email(
            recipients=recipients,
            job_name=job_name,
            query=query,
            posts_count=posts_count,
            attachments=attachments,
            result=result,
        )
    )


def test_email_config() -> tuple:
    """
    Testa a configuração de e-mail.
    
    Returns:
        (sucesso, mensagem)
    """
    config = EmailConfig.get_config()
    
    if not config["user"]:
        return False, "SMTP_USER não configurado"
    if not config["password"]:
        return False, "SMTP_PASS não configurado"
    if not config["from_email"]:
        return False, "FROM_EMAIL não configurado"
    
    return True, f"Configurado: {config['host']}:{config['port']} ({config['user']})"
