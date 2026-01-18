"""Executor de jobs agendados."""
from __future__ import annotations
import asyncio
import threading
from datetime import datetime, timezone
from typing import Callable, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from core.models import Job, RunHistory, RunStatus, ScheduleType
from core.collector import XCollector
from scheduler.job_manager import JobManager
from scheduler.persistence import get_db
from exporters import export_to_docx, export_to_json, export_to_csv


def utc_now() -> datetime:
    """Retorna datetime atual em UTC."""
    return datetime.now(timezone.utc)


class JobRunner:
    """Executa jobs agendados."""
    
    def __init__(
        self,
        job_manager: JobManager = None,
        on_job_complete: Optional[Callable[[RunHistory], None]] = None,
        on_job_error: Optional[Callable[[str, str], None]] = None,
    ):
        self.job_manager = job_manager or JobManager()
        self.on_job_complete = on_job_complete
        self.on_job_error = on_job_error
        
        self.scheduler = BackgroundScheduler(
            timezone=pytz.timezone("America/Sao_Paulo")
        )
        self._running = False
        self._current_run: Optional[RunHistory] = None
    
    def start(self):
        """Inicia o scheduler em background."""
        if self._running:
            return
        
        # Verificar jobs a cada minuto
        self.scheduler.add_job(
            self._check_and_run_jobs,
            trigger=IntervalTrigger(minutes=1),
            id="job_checker",
            replace_existing=True,
        )
        
        self.scheduler.start()
        self._running = True
        print("🚀 Scheduler iniciado")
    
    def stop(self):
        """Para o scheduler."""
        if not self._running:
            return
        
        self.scheduler.shutdown(wait=False)
        self._running = False
        print("🛑 Scheduler parado")
    
    def _check_and_run_jobs(self):
        """Verifica e executa jobs devidos."""
        due_jobs = self.job_manager.get_due_jobs()
        
        for job in due_jobs:
            print(f"⏰ Job devido: {job.name} ({job.job_id})")
            
            # Executar em thread separada para não bloquear
            thread = threading.Thread(
                target=self._run_job_sync,
                args=(job,),
                daemon=True,
            )
            thread.start()
    
    def _run_job_sync(self, job: Job):
        """Wrapper síncrono para executar job assíncrono."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_job(job))
        finally:
            loop.close()
    
    async def run_job(self, job: Job) -> RunHistory:
        """
        Executa um job.
        
        Args:
            job: Job a executar
            
        Returns:
            Histórico da execução
        """
        run = RunHistory(
            job_id=job.job_id,
            job_name=job.name,
            started_at=utc_now(),
        )
        self._current_run = run
        
        def log(msg: str):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {msg}"
            run.logs.append(log_entry)
            print(f"  {log_entry}")
        
        try:
            log(f"Iniciando job: {job.name}")
            log(f"Query/URL: {job.query_or_url}")
            
            # Coletar posts (headless para jobs automáticos)
            async with XCollector(headless=True) as collector:
                # Verificar se está logado
                is_logged = await collector.is_logged_in()
                if not is_logged:
                    raise Exception("Sessão expirada. Faça login novamente.")
                
                def progress_callback(count: int, msg: str):
                    log(msg)
                
                result = await collector.collect(
                    query_or_url=job.query_or_url,
                    params=job.params,
                    is_url=job.is_url,
                    progress_callback=progress_callback,
                )
            
            run.posts_collected = result.total_collected
            log(f"Coletados: {run.posts_collected} posts")
            
            if result.errors:
                for error in result.errors:
                    log(f"⚠️ {error}")
            
            # Exportar arquivos
            export_files = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{job.name.replace(' ', '_')}_{timestamp}"
            
            if "docx" in job.export_formats:
                filepath = export_to_docx(result, filename=f"{base_name}.docx")
                export_files.append(filepath)
                log(f"📄 DOCX: {filepath}")
            
            if "json" in job.export_formats:
                filepath = export_to_json(result, filename=f"{base_name}.json")
                export_files.append(filepath)
                log(f"📋 JSON: {filepath}")
            
            if "csv" in job.export_formats:
                filepath = export_to_csv(result, filename=f"{base_name}.csv")
                export_files.append(filepath)
                log(f"📊 CSV: {filepath}")
            
            run.export_files = export_files
            
            # Enviar e-mail (se não for dry run)
            if job.email_recipients and not job.dry_run:
                try:
                    from email_service.sender import send_collection_email
                    
                    success = await send_collection_email(
                        recipients=job.email_recipients,
                        job_name=job.name,
                        query=job.query_or_url,
                        posts_count=run.posts_collected,
                        attachments=export_files,
                    )
                    
                    run.email_sent = success
                    if success:
                        log(f"📧 E-mail enviado para: {', '.join(job.email_recipients)}")
                    else:
                        log("⚠️ Falha ao enviar e-mail")
                except Exception as e:
                    log(f"⚠️ Erro no envio de e-mail: {e}")
                    run.email_sent = False
            elif job.dry_run:
                log("🔄 Dry run - e-mail não enviado")
            
            # Atualizar status
            run.status = RunStatus.SUCCESS if not result.errors else RunStatus.PARTIAL
            run.finished_at = utc_now()
            
            # Marcar job como executado
            self.job_manager.update_last_run(job.job_id)
            
            # Se for job único, marcar como concluído
            if job.schedule.type == ScheduleType.ONCE:
                self.job_manager.mark_completed(job.job_id)
            
            log(f"✅ Job concluído: {run.status.value}")
            
        except Exception as e:
            run.status = RunStatus.FAILED
            run.error_message = str(e)
            run.finished_at = utc_now()
            log(f"❌ Erro: {e}")
            
            if self.on_job_error:
                self.on_job_error(job.job_id, str(e))
        
        finally:
            # Salvar histórico
            get_db().save_run(run)
            self._current_run = None
            
            if self.on_job_complete:
                self.on_job_complete(run)
        
        return run
    
    async def run_job_now(self, job_id: str) -> Optional[RunHistory]:
        """Executa um job imediatamente."""
        job = self.job_manager.get_job(job_id)
        if not job:
            return None
        
        return await self.run_job(job)
    
    def get_current_run(self) -> Optional[RunHistory]:
        """Retorna a execução atual (se houver)."""
        return self._current_run


# Singleton do runner
_runner: Optional[JobRunner] = None


def get_runner() -> JobRunner:
    """Retorna instância singleton do runner."""
    global _runner
    if _runner is None:
        _runner = JobRunner()
    return _runner


def start_scheduler():
    """Inicia o scheduler global."""
    get_runner().start()


def stop_scheduler():
    """Para o scheduler global."""
    get_runner().stop()
