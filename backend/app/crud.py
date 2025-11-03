"""Operaciones CRUD para los modelos del proyecto."""

from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Field, Machine, Role, SchedulerRun, User, WorkPlan, WorkType


async def upsert_machines(session: AsyncSession, machines: Sequence[dict]) -> int:
    count = 0
    for item in machines:
        db_machine = await session.get(Machine, item["id"])
        if db_machine:
            db_machine.name = item.get("name")
            db_machine.category = item.get("category")
            db_machine.serial_number = item.get("serial_number")
            db_machine.status = item.get("status")
            db_machine.latitude = item.get("latitude")
            db_machine.longitude = item.get("longitude")
            db_machine.last_update = item.get("last_update")
        else:
            session.add(Machine(**item))
        count += 1
    return count


async def upsert_fields(session: AsyncSession, fields: Sequence[dict]) -> int:
    count = 0
    for item in fields:
        db_field = await session.get(Field, item["id"])
        if db_field:
            db_field.name = item.get("name", db_field.name)
            db_field.boundary = item.get("boundary")
            db_field.crop_type = item.get("crop_type")
            db_field.updated_at = item.get("updated_at")
        else:
            session.add(Field(**item))
        count += 1
    return count


async def create_work_plan(
    session: AsyncSession,
    *,
    field_id: str,
    work_type: WorkType,
    start_date: date,
    end_date: date,
    status: str = "pending",
) -> WorkPlan:
    work_plan = WorkPlan(
        field_id=field_id,
        type=work_type,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )
    session.add(work_plan)
    await session.flush()
    await session.refresh(work_plan)
    return work_plan


async def list_work_plans(session: AsyncSession) -> Sequence[WorkPlan]:
    result = await session.execute(select(WorkPlan).order_by(WorkPlan.start_date))
    return result.scalars().all()


async def update_work_plan_status(
    session: AsyncSession, plan_id: int, *, status: str
) -> Optional[WorkPlan]:
    result = await session.execute(
        update(WorkPlan).where(WorkPlan.id == plan_id).values(status=status).returning(WorkPlan)
    )
    plan = result.scalars().first()
    return plan


async def delete_work_plan(session: AsyncSession, plan_id: int) -> None:
    await session.execute(delete(WorkPlan).where(WorkPlan.id == plan_id))


async def get_scheduler_runs(session: AsyncSession) -> Sequence[SchedulerRun]:
    result = await session.execute(select(SchedulerRun).order_by(SchedulerRun.last_run.desc()))
    return result.scalars().all()


async def create_scheduler_run(
    session: AsyncSession, *, machines_synced: int, fields_synced: int
) -> SchedulerRun:
    run = SchedulerRun(machines_synced=machines_synced, fields_synced=fields_synced)
    session.add(run)
    await session.flush()
    await session.refresh(run)
    return run


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def create_user(
    session: AsyncSession, *, username: str, hashed_password: str, role: Role
) -> User:
    user = User(username=username, hashed_password=hashed_password, role=role)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user

