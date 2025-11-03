"""
Planificador de tareas recurrentes para Agro Planner.

Este módulo utiliza APScheduler para ejecutar funciones en intervalos
regulares.  Se definen tareas como la actualización periódica de la lista de
máquinas y la comprobación de alertas agronómicas.  Para iniciar el
planificador desde el módulo principal, importa y ejecuta `start_scheduler()`.
"""

import asyncio
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import get_settings
from .john_deere_client import JohnDeereClient


settings = get_settings()
_scheduler: AsyncIOScheduler | None = None


async def update_machines_task() -> None:
    """Sincroniza el listado de máquinas y sus ubicaciones.

    Obtiene la lista de equipos desde la Equipment API y procesa la información.
    En una implementación real, aquí se podría actualizar la base de datos,
    enviar notificaciones o calcular métricas de disponibilidad.
    """
    client = JohnDeereClient(settings)
    try:
        machines = await client.list_equipment()
        # TODO: persistir en base de datos y generar alertas si es necesario
        print(f"[Scheduler] Se han sincronizado {len(machines.get('values', []))} máquinas.")
    except Exception as exc:
        print(f"[Scheduler] Error al sincronizar máquinas: {exc}")


def start_scheduler() -> None:
    """Inicializa y arranca el planificador de APScheduler."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = AsyncIOScheduler()
    # Tarea que se ejecuta cada `scheduler_interval_seconds`
    trigger = IntervalTrigger(seconds=settings.scheduler_interval_seconds)
    _scheduler.add_job(update_machines_task, trigger)
    _scheduler.start()


def stop_scheduler() -> None:
    """Detiene el planificador si está en ejecución."""
    if _scheduler:
        _scheduler.shutdown(wait=False)