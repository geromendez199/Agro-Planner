"""Modelos ORM del proyecto."""

from __future__ import annotations

import enum
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"


class WorkType(str, enum.Enum):
    COSECHA = "COSECHA"
    SIEMBRA = "SIEMBRA"
    FERTILIZACION = "FERTILIZACION"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Machine(Base, TimestampMixin):
    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_update: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class Field(Base, TimestampMixin):
    __tablename__ = "fields"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    boundary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    crop_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    work_plans: Mapped[list["WorkPlan"]] = relationship(back_populates="field")


class WorkPlan(Base, TimestampMixin):
    __tablename__ = "work_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    field_id: Mapped[str] = mapped_column(ForeignKey("fields.id"))
    type: Mapped[WorkType] = mapped_column(Enum(WorkType))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="pending")

    field: Mapped[Field] = relationship(back_populates="work_plans")


class SchedulerRun(Base):
    __tablename__ = "scheduler_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    last_run: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    machines_synced: Mapped[int] = mapped_column(Integer, default=0)
    fields_synced: Mapped[int] = mapped_column(Integer, default=0)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.OPERATOR)

