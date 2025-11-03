"""Esquemas Pydantic para la API."""

from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import Role, WorkType


class MachineBase(BaseModel):
    id: str
    name: Optional[str] = None
    category: Optional[str] = None
    serial_number: Optional[str] = None
    status: Optional[str] = None
    last_update: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class FieldBase(BaseModel):
    id: str
    name: str
    boundary: Optional[dict] = None
    crop_type: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkPlanCreate(BaseModel):
    field_id: str
    type: WorkType
    start_date: date
    end_date: date
    status: Optional[str] = Field(default="pending")


class WorkPlanUpdate(BaseModel):
    status: str


class WorkPlanRead(BaseModel):
    id: int
    field_id: str
    type: WorkType
    start_date: date
    end_date: date
    status: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str
    role: Role


class UserCreate(BaseModel):
    username: str
    password: str
    role: Role = Role.OPERATOR


class UserRead(BaseModel):
    id: int
    username: str
    role: Role

    model_config = ConfigDict(from_attributes=True)


class SchedulerStatus(BaseModel):
    running: bool
    interval_seconds: int
    last_run: Optional[datetime] = None
    machines_synced: int = 0
    fields_synced: int = 0

