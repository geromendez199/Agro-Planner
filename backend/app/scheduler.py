"""Planificador de tareas recurrentes para Agro Planner."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Optional

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import get_settings
from . import crud
from .john_deere_client import JohnDeereClient

logger = logging.getLogger(__name__)

settings = get_settings()
_scheduler: Optional[AsyncIOScheduler] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None
_interval_seconds: int = settings.scheduler_interval_seconds
_last_run_summary: dict[str, Optional[datetime | int]] = {
    "last_run": None,
    "machines_synced": 0,
    "fields_synced": 0,
}


def configure(session_factory: async_sessionmaker[AsyncSession]) -> None:
    global _session_factory
    _session_factory = session_factory


def is_running() -> bool:
    return _scheduler is not None and _scheduler.running


async def _fetch_weather_summary() -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.get("https://api.open-meteo.com/v1/forecast", params={"latitude": 0, "longitude": 0, "hourly": "relativehumidity_2m"})
        logger.info("Consulta diaria de clima completada")
    except httpx.HTTPError as exc:
        logger.warning("No se pudo obtener información meteorológica: %s", exc)


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _sync_entities() -> None:
    if _session_factory is None:
        logger.warning("No hay sesión configurada para el planificador")
        return
    client = JohnDeereClient(settings)
    try:
        machines_data, fields_data = await asyncio.gather(
            client.list_equipment(), client.list_fields(), return_exceptions=False
        )
    except httpx.HTTPError as exc:
        logger.error("Error al sincronizar datos de John Deere: %s", exc)
        return

    machine_values = []
    for item in machines_data.get("values", []):
        machine_values.append(
            {
                "id": item.get("id"),
                "name": item.get("displayName"),
                "category": item.get("category"),
                "serial_number": item.get("serialNumber"),
                "status": item.get("status"),
                "last_update": _parse_datetime(item.get("lastUpdated")),
                "latitude": (item.get("location") or {}).get("latitude"),
                "longitude": (item.get("location") or {}).get("longitude"),
            }
        )

    field_values = []
    for item in fields_data.get("values", []):
        field_values.append(
            {
                "id": item.get("id"),
                "name": item.get("name", ""),
                "boundary": item.get("boundary"),
                "crop_type": item.get("cropType"),
                "updated_at": _parse_datetime(item.get("modifiedTime")),
            }
        )

    async with _session_factory() as session:
        machines_synced = await crud.upsert_machines(session, machine_values)
        fields_synced = await crud.upsert_fields(session, field_values)
        await crud.create_scheduler_run(
            session, machines_synced=machines_synced, fields_synced=fields_synced
        )
        await session.commit()
        _last_run_summary["last_run"] = datetime.utcnow()
        _last_run_summary["machines_synced"] = machines_synced
        _last_run_summary["fields_synced"] = fields_synced
        logger.info(
            "Sincronización completada: %s máquinas, %s campos",
            machines_synced,
            fields_synced,
        )


def start_scheduler(session_factory: Optional[async_sessionmaker[AsyncSession]] = None) -> None:
    global _scheduler
    if session_factory is not None:
        configure(session_factory)
    if _scheduler is not None and _scheduler.running:
        return
    if _session_factory is None:
        raise RuntimeError("No se configuró una sesión para el planificador")
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_sync_entities, IntervalTrigger(seconds=_interval_seconds), id="sync_job")
    _scheduler.add_job(_fetch_weather_summary, CronTrigger(hour=6, minute=0), id="weather_job")
    _scheduler.start()
    asyncio.create_task(_sync_entities())
    logger.info("Planificador iniciado con intervalo %s segundos", _interval_seconds)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Planificador detenido")
    _scheduler = None


def update_interval(seconds: int) -> None:
    global _interval_seconds
    _interval_seconds = seconds
    if _scheduler:
        job = _scheduler.get_job("sync_job")
        if job:
            job.reschedule(trigger=IntervalTrigger(seconds=seconds))
            logger.info("Intervalo del planificador actualizado a %s segundos", seconds)


async def get_status(session: AsyncSession) -> dict[str, Optional[datetime | int]]:
    runs = await crud.get_scheduler_runs(session)
    if runs:
        latest = runs[0]
        _last_run_summary["last_run"] = latest.last_run
        _last_run_summary["machines_synced"] = latest.machines_synced
        _last_run_summary["fields_synced"] = latest.fields_synced
    return {
        "running": is_running(),
        "interval_seconds": _interval_seconds,
        "last_run": _last_run_summary.get("last_run"),
        "machines_synced": _last_run_summary.get("machines_synced", 0),
        "fields_synced": _last_run_summary.get("fields_synced", 0),
    }

