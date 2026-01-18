"""Persistência de jobs e histórico usando SQLite."""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from core.models import Job, JobStatus, RunHistory, RunStatus

Base = declarative_base()


class JobModel(Base):
    """Modelo SQLAlchemy para Job."""
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    query_or_url = Column(String, nullable=False)
    is_url = Column(Boolean, default=False)
    params_json = Column(Text)
    schedule_json = Column(Text)
    email_recipients_json = Column(Text)
    export_formats_json = Column(Text)
    status = Column(String, default="active")
    created_at = Column(DateTime)
    last_run = Column(DateTime, nullable=True)
    dry_run = Column(Boolean, default=False)


class RunHistoryModel(Base):
    """Modelo SQLAlchemy para RunHistory."""
    __tablename__ = "run_history"
    
    run_id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    job_name = Column(String)
    started_at = Column(DateTime)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String)
    posts_collected = Column(String, default="0")
    export_files_json = Column(Text)
    email_sent = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    logs_json = Column(Text)


class DatabaseManager:
    """Gerenciador de banco de dados SQLite."""
    
    def __init__(self, db_path: str = None):
        if not db_path:
            db_path = os.getenv("DB_PATH", "./data/scheduler.db")
        
        # Garantir que o diretório existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f"sqlite:///{db_path}")
        # checkfirst=True evita erro se tabelas já existem
        Base.metadata.create_all(self.engine, checkfirst=True)
        self.Session = sessionmaker(bind=self.engine)
    
    # === JOBS ===
    
    def save_job(self, job: Job) -> None:
        """Salva ou atualiza um job."""
        session = self.Session()
        try:
            job_model = JobModel(
                job_id=job.job_id,
                name=job.name,
                query_or_url=job.query_or_url,
                is_url=job.is_url,
                params_json=job.params.model_dump_json(),
                schedule_json=job.schedule.model_dump_json(),
                email_recipients_json=json.dumps(job.email_recipients),
                export_formats_json=json.dumps(job.export_formats),
                status=job.status.value,
                created_at=job.created_at,
                last_run=job.last_run,
                dry_run=job.dry_run,
            )
            session.merge(job_model)
            session.commit()
        finally:
            session.close()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Busca um job por ID."""
        session = self.Session()
        try:
            job_model = session.query(JobModel).filter_by(job_id=job_id).first()
            if not job_model:
                return None
            return self._job_from_model(job_model)
        finally:
            session.close()
    
    def get_all_jobs(self) -> list[Job]:
        """Retorna todos os jobs."""
        session = self.Session()
        try:
            job_models = session.query(JobModel).all()
            return [self._job_from_model(jm) for jm in job_models]
        finally:
            session.close()
    
    def get_active_jobs(self) -> list[Job]:
        """Retorna jobs ativos."""
        session = self.Session()
        try:
            job_models = session.query(JobModel).filter_by(status="active").all()
            return [self._job_from_model(jm) for jm in job_models]
        finally:
            session.close()
    
    def delete_job(self, job_id: str) -> bool:
        """Remove um job."""
        session = self.Session()
        try:
            result = session.query(JobModel).filter_by(job_id=job_id).delete()
            session.commit()
            return result > 0
        finally:
            session.close()
    
    def update_job_status(self, job_id: str, status: JobStatus) -> None:
        """Atualiza o status de um job."""
        session = self.Session()
        try:
            session.query(JobModel).filter_by(job_id=job_id).update({"status": status.value})
            session.commit()
        finally:
            session.close()
    
    def update_job_last_run(self, job_id: str, last_run: datetime) -> None:
        """Atualiza a última execução de um job."""
        session = self.Session()
        try:
            session.query(JobModel).filter_by(job_id=job_id).update({"last_run": last_run})
            session.commit()
        finally:
            session.close()
    
    def _job_from_model(self, model: JobModel) -> Job:
        """Converte modelo SQLAlchemy para Pydantic."""
        from core.models import CollectionParams, Schedule
        
        return Job(
            job_id=model.job_id,
            name=model.name,
            query_or_url=model.query_or_url,
            is_url=model.is_url,
            params=CollectionParams.model_validate_json(model.params_json) if model.params_json else CollectionParams(),
            schedule=Schedule.model_validate_json(model.schedule_json) if model.schedule_json else Schedule(),
            email_recipients=json.loads(model.email_recipients_json) if model.email_recipients_json else [],
            export_formats=json.loads(model.export_formats_json) if model.export_formats_json else ["docx"],
            status=JobStatus(model.status),
            created_at=model.created_at,
            last_run=model.last_run,
            dry_run=model.dry_run,
        )
    
    # === RUN HISTORY ===
    
    def save_run(self, run: RunHistory) -> None:
        """Salva ou atualiza uma execução."""
        session = self.Session()
        try:
            run_model = RunHistoryModel(
                run_id=run.run_id,
                job_id=run.job_id,
                job_name=run.job_name,
                started_at=run.started_at,
                finished_at=run.finished_at,
                status=run.status.value,
                posts_collected=str(run.posts_collected),
                export_files_json=json.dumps(run.export_files),
                email_sent=run.email_sent,
                error_message=run.error_message,
                logs_json=json.dumps(run.logs),
            )
            session.merge(run_model)
            session.commit()
        finally:
            session.close()
    
    def get_run(self, run_id: str) -> Optional[RunHistory]:
        """Busca uma execução por ID."""
        session = self.Session()
        try:
            run_model = session.query(RunHistoryModel).filter_by(run_id=run_id).first()
            if not run_model:
                return None
            return self._run_from_model(run_model)
        finally:
            session.close()
    
    def get_runs_by_job(self, job_id: str, limit: int = 10) -> list[RunHistory]:
        """Retorna últimas execuções de um job."""
        session = self.Session()
        try:
            run_models = (
                session.query(RunHistoryModel)
                .filter_by(job_id=job_id)
                .order_by(RunHistoryModel.started_at.desc())
                .limit(limit)
                .all()
            )
            return [self._run_from_model(rm) for rm in run_models]
        finally:
            session.close()
    
    def get_all_runs(self, limit: int = 50) -> list[RunHistory]:
        """Retorna últimas execuções de todos os jobs."""
        session = self.Session()
        try:
            run_models = (
                session.query(RunHistoryModel)
                .order_by(RunHistoryModel.started_at.desc())
                .limit(limit)
                .all()
            )
            return [self._run_from_model(rm) for rm in run_models]
        finally:
            session.close()
    
    def _run_from_model(self, model: RunHistoryModel) -> RunHistory:
        """Converte modelo SQLAlchemy para Pydantic."""
        return RunHistory(
            run_id=model.run_id,
            job_id=model.job_id,
            job_name=model.job_name,
            started_at=model.started_at,
            finished_at=model.finished_at,
            status=RunStatus(model.status),
            posts_collected=int(model.posts_collected),
            export_files=json.loads(model.export_files_json) if model.export_files_json else [],
            email_sent=model.email_sent,
            error_message=model.error_message,
            logs=json.loads(model.logs_json) if model.logs_json else [],
        )


# Singleton para uso global
_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Retorna instância singleton do gerenciador de banco."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
