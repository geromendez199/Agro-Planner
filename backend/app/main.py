"""
Punto de entrada del backend Agro Planner.

Define la aplicación FastAPI, registra los endpoints y configura CORS y
dependencias.  Cuando la aplicación se inicia, arranca el planificador de
tareas para actualizar la información de las máquinas de forma periódica.
"""

from typing import Any, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import get_settings, Settings
from .john_deere_client import JohnDeereClient
from .scheduler import start_scheduler

import httpx


app = FastAPI(title="Agro Planner API", version="0.1.0")


def get_client(settings: Settings = Depends(get_settings)) -> JohnDeereClient:
    """Dependencia que proporciona una instancia de JohnDeereClient."""
    return JohnDeereClient(settings)


class WorkPlanRequest(BaseModel):
    """Modelo de entrada para crear un plan de trabajo."""

    field_id: str = Field(..., description="Identificador del campo/lote")
    job_type: str = Field(..., description="Tipo de tarea, p.ej. cosecha, siembra")
    start_date: str = Field(..., description="Fecha de inicio ISO 8601 (YYYY-MM-DD)")
    end_date: str = Field(..., description="Fecha de finalización ISO 8601 (YYYY-MM-DD)")
    product_mix: Optional[dict] = Field(None, description="Configuración de la mezcla de tanque y productos")
    notes: Optional[str] = Field(None, description="Observaciones adicionales")


class MachineOut(BaseModel):
    """Modelo de salida para una máquina."""

    id: str
    name: Optional[str]
    category: Optional[str]
    serial_number: Optional[str]
    status: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


@app.on_event("startup")
async def on_startup() -> None:
    """Inicia el planificador al arrancar la aplicación."""
    start_scheduler()


@app.get("/machines", response_model=List[MachineOut])
async def get_machines(client: JohnDeereClient = Depends(get_client)) -> List[MachineOut]:
    """Devuelve la lista de máquinas de la organización.

    Esta ruta utiliza la nueva Equipment API y solo devuelve los campos
    necesarios para la interfaz.  Si ocurre un error al llamar a la API
    externa, se genera una excepción HTTP 502.
    """
    try:
        data = await client.list_equipment()
        machines: List[MachineOut] = []
        for item in data.get("values", []):
            machines.append(MachineOut(
                id=item.get("id"),
                name=item.get("displayName"),
                category=item.get("category"),
                serial_number=item.get("serialNumber"),
                status=item.get("status"),
                latitude=item.get("location", {}).get("latitude"),
                longitude=item.get("location", {}).get("longitude"),
            ))
        return machines
    except httpx.HTTPError as exc:  # type: ignore[name-defined]
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Error al obtener máquinas: {exc}") from exc


@app.get("/fields")
async def get_fields(client: JohnDeereClient = Depends(get_client)) -> Any:
    """Lista todos los campos de la organización con sus límites."""
    try:
        return await client.list_fields()
    except httpx.HTTPError as exc:  # type: ignore[name-defined]
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Error al obtener campos: {exc}") from exc


@app.post("/work-plans")
async def create_work_plan(request: WorkPlanRequest, client: JohnDeereClient = Depends(get_client)) -> Any:
    """Crea un plan de trabajo y lo envía a Operations Center.

    El cuerpo de la solicitud debe contener el identificador del lote, el tipo
    de tarea, las fechas y cualquier mezcla de productos.  Devuelve la
    respuesta de la API externa.  Si algo falla se devuelve un error 502.
    """
    try:
        payload = {
            "fieldId": request.field_id,
            "jobType": request.job_type,
            "startDate": request.start_date,
            "endDate": request.end_date,
            "productMix": request.product_mix,
            "notes": request.notes,
        }
        return await client.create_work_plan(payload)
    except httpx.HTTPError as exc:  # type: ignore[name-defined]
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"Error al crear el plan de trabajo: {exc}") from exc


# Configuración de CORS
settings = get_settings()
origins = [origin.strip() for origin in settings.backend_cors_origins.split(",") if origin.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )