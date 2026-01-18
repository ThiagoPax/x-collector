"""Gerenciador de jobs agendados."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
import pytz
from core.models import Job, JobStatus, Schedule, ScheduleType, CollectionParams
from scheduler.persistence import get_db, DatabaseManager


def utc_now() -> datetime:
    """Retorna datetime atual em UTC."""
    return datetime.now(timezone.utc)


class JobManager:
    """Gerencia CRUD de jobs agendados."""
    
    def __init__(self, db: DatabaseManager = None):
        self.db = db or get_db()
    
    def create_job(
        self,
        name: str,
        query_or_url: str,
        is_url: bool = False,
        params: CollectionParams = None,
        schedule: Schedule = None,
        email_recipients: list[str] = None,
        export_formats: list[str] = None,
        dry_run: bool = False,
    ) -> Job:
        """
        Cria um novo job.
        
        Args:
            name: Nome do job
            query_or_url: Query ou URL de busca
            is_url: Se é URL
            params: Parâmetros de coleta
            schedule: Configuração de agendamento
            email_recipients: Lista de e-mails para envio
            export_formats: Formatos de exportação
            dry_run: Se True, não envia e-mail
            
        Returns:
            Job criado
        """
        job = Job(
            name=name,
            query_or_url=query_or_url,
            is_url=is_url,
            params=params or CollectionParams(),
            schedule=schedule or Schedule(),
            email_recipients=email_recipients or [],
            export_formats=export_formats or ["docx"],
            dry_run=dry_run,
        )
        
        self.db.save_job(job)
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Busca um job por ID."""
        return self.db.get_job(job_id)
    
    def list_jobs(self, active_only: bool = False) -> list[Job]:
        """Lista todos os jobs."""
        if active_only:
            return self.db.get_active_jobs()
        return self.db.get_all_jobs()
    
    def update_job(self, job: Job) -> None:
        """Atualiza um job existente."""
        self.db.save_job(job)
    
    def delete_job(self, job_id: str) -> bool:
        """Remove um job."""
        return self.db.delete_job(job_id)
    
    def pause_job(self, job_id: str) -> bool:
        """Pausa um job."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        self.db.update_job_status(job_id, JobStatus.PAUSED)
        return True
    
    def resume_job(self, job_id: str) -> bool:
        """Retoma um job pausado."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        self.db.update_job_status(job_id, JobStatus.ACTIVE)
        return True
    
    def mark_completed(self, job_id: str) -> None:
        """Marca job como concluído (para jobs únicos)."""
        self.db.update_job_status(job_id, JobStatus.COMPLETED)
    
    def update_last_run(self, job_id: str) -> None:
        """Atualiza timestamp da última execução."""
        self.db.update_job_last_run(job_id, utc_now())
    
    def get_due_jobs(self) -> list[Job]:
        """
        Retorna jobs que precisam ser executados.
        
        Verifica:
        - Jobs ativos
        - Hora de execução chegou
        """
        due_jobs = []
        now = utc_now()
        
        for job in self.db.get_active_jobs():
            if self._is_due(job, now):
                due_jobs.append(job)
        
        return due_jobs
    
    def _is_due(self, job: Job, now: datetime) -> bool:
        """Verifica se um job está devido para execução."""
        schedule = job.schedule
        
        # Converter para timezone do job
        tz = pytz.timezone(schedule.timezone)
        now_tz = pytz.utc.localize(now).astimezone(tz)
        
        if schedule.type == ScheduleType.ONCE:
            # Execução única
            if schedule.run_at:
                run_at_tz = schedule.run_at
                if run_at_tz.tzinfo is None:
                    run_at_tz = tz.localize(run_at_tz)
                
                # Devido se já passou a hora e nunca executou
                if now_tz >= run_at_tz and job.last_run is None:
                    return True
        
        elif schedule.type == ScheduleType.RECURRING:
            # Execução recorrente (cron)
            if schedule.cron:
                return self._check_cron(schedule.cron, now_tz, job.last_run, tz)
        
        return False
    
    def _check_cron(
        self,
        cron_expr: str,
        now: datetime,
        last_run: Optional[datetime],
        tz: pytz.BaseTzInfo,
    ) -> bool:
        """
        Verifica se o cron deve executar.
        
        Simplificação: suporta formatos básicos como:
        - "0 7 * * *" (diário às 7h)
        - "0 7 * * 1,3,5" (seg/qua/sex às 7h)
        - "*/2 * * * *" (a cada 2 minutos - para teste)
        """
        try:
            parts = cron_expr.split()
            if len(parts) != 5:
                return False
            
            minute, hour, day, month, weekday = parts
            
            # Verificar minuto
            if not self._matches_cron_field(minute, now.minute):
                return False
            
            # Verificar hora
            if not self._matches_cron_field(hour, now.hour):
                return False
            
            # Verificar dia do mês
            if not self._matches_cron_field(day, now.day):
                return False
            
            # Verificar mês
            if not self._matches_cron_field(month, now.month):
                return False
            
            # Verificar dia da semana (0=seg, 6=dom)
            # Python: weekday() = 0-6 (seg-dom)
            if not self._matches_cron_field(weekday, now.weekday()):
                return False
            
            # Verificar se já executou neste período
            if last_run:
                last_run_tz = last_run
                if last_run_tz.tzinfo is None:
                    last_run_tz = pytz.utc.localize(last_run_tz).astimezone(tz)
                
                # Se executou no mesmo minuto, não executa novamente
                if (
                    last_run_tz.year == now.year
                    and last_run_tz.month == now.month
                    and last_run_tz.day == now.day
                    and last_run_tz.hour == now.hour
                    and last_run_tz.minute == now.minute
                ):
                    return False
            
            return True
        
        except Exception:
            return False
    
    def _matches_cron_field(self, field: str, value: int) -> bool:
        """Verifica se um valor casa com um campo cron."""
        if field == "*":
            return True
        
        # Intervalo (*/N)
        if field.startswith("*/"):
            try:
                interval = int(field[2:])
                return value % interval == 0
            except ValueError:
                return False
        
        # Lista (1,3,5)
        if "," in field:
            try:
                values = [int(v) for v in field.split(",")]
                return value in values
            except ValueError:
                return False
        
        # Range (1-5)
        if "-" in field:
            try:
                start, end = map(int, field.split("-"))
                return start <= value <= end
            except ValueError:
                return False
        
        # Valor exato
        try:
            return value == int(field)
        except ValueError:
            return False


def validate_cron(cron_expr: str) -> tuple[bool, str]:
    """
    Valida uma expressão cron.
    
    Returns:
        (válido, mensagem)
    """
    parts = cron_expr.split()
    if len(parts) != 5:
        return False, "Expressão cron deve ter 5 campos: minuto hora dia mês dia_semana"
    
    fields = ["minuto (0-59)", "hora (0-23)", "dia (1-31)", "mês (1-12)", "dia_semana (0-6)"]
    
    for i, (part, field) in enumerate(zip(parts, fields)):
        if part == "*":
            continue
        
        if part.startswith("*/"):
            try:
                int(part[2:])
                continue
            except ValueError:
                return False, f"Campo {field}: intervalo inválido '{part}'"
        
        if "," in part:
            try:
                [int(v) for v in part.split(",")]
                continue
            except ValueError:
                return False, f"Campo {field}: lista inválida '{part}'"
        
        if "-" in part:
            try:
                parts_range = part.split("-")
                if len(parts_range) != 2:
                    return False, f"Campo {field}: range inválido '{part}'"
                int(parts_range[0])
                int(parts_range[1])
                continue
            except ValueError:
                return False, f"Campo {field}: range inválido '{part}'"
        
        try:
            int(part)
        except ValueError:
            return False, f"Campo {field}: valor inválido '{part}'"
    
    return True, "Válido"


def cron_examples() -> dict[str, str]:
    """Retorna exemplos de expressões cron."""
    return {
        "Diário às 7h": "0 7 * * *",
        "Diário às 19h": "0 19 * * *",
        "Seg/Qua/Sex às 8h": "0 8 * * 1,3,5",
        "A cada 2 horas": "0 */2 * * *",
        "A cada 30 min": "*/30 * * * *",
        "Sábados às 10h": "0 10 * * 6",
        "Primeira segunda do mês às 9h": "0 9 1-7 * 1",
    }
