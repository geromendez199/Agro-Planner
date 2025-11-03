"""Punto de entrada del backend Agro Planner."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated, List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from prometheus_fastapi_instrumentator import PrometheusFastApiInstrumentator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import Settings, get_settings
from .crud import (
    create_user,
    create_work_plan,
    delete_work_plan,
    get_user_by_username,
    list_work_plans,
    update_work_plan_status,
)
from .database import get_session, get_sessionmaker, init_db
from .exceptions import AuthenticationError, ValidationError
from .john_deere_client import JohnDeereClient
from .logger_config import configure_logging
from .models import Field, Machine, Role, User
from .scheduler import get_status as scheduler_status
from .scheduler import start_scheduler, stop_scheduler, update_interval
from .schemas import (
    FieldBase,
    MachineBase,
    SchedulerStatus,
    Token,
    TokenData,
    UserCreate,
    UserRead,
    WorkPlanCreate,
    WorkPlanRead,
    WorkPlanUpdate,
)

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def create_access_token(data: dict, settings: Settings) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> tuple[bool, Role]:
    user = await get_user_by_username(session, username)
    if not user:
        return False, Role.OPERATOR
    if not pwd_context.verify(password, user.hashed_password):
        return False, Role.OPERATOR
    return True, user.role


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        role_value: str = payload.get("role")
        if username is None or role_value is None:
            raise AuthenticationError()
    except JWTError as exc:
        raise AuthenticationError() from exc
    user = await get_user_by_username(session, username)
    if user is None:
        raise AuthenticationError()
    return TokenData(username=username, role=user.role)


def require_role(required: Role):
    async def _dependency(current: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        if current.role != required and current.role != Role.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
        return current

    return _dependency


async def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme_optional)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenData | None:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    user = await get_user_by_username(session, username)
    if user is None:
        return None
    return TokenData(username=username, role=user.role)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    session_factory = get_sessionmaker()
    if settings.scheduler_interval_seconds > 0:
        start_scheduler(session_factory)
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(title="Agro Planner API", version="0.2.0", lifespan=lifespan)

settings = get_settings()

if not settings.secret_key:
    logger.warning("SECRET_KEY no configurado: los tokens JWT no serán seguros")

origins = [origin.strip() for origin in settings.backend_cors_origins.split(",") if origin.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

PrometheusFastApiInstrumentator().instrument(app).expose(app)


async def get_client(settings: Settings = Depends(get_settings)) -> JohnDeereClient:
    return JohnDeereClient(settings)


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[TokenData | None, Depends(get_optional_user)] = None,
) -> UserRead:
    total_users = await session.scalar(select(func.count()).select_from(User))
    if total_users and (current_user is None or current_user.role != Role.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado")
    existing = await get_user_by_username(session, payload.username)
    if existing:
        raise ValidationError("El usuario ya existe")
    hashed_password = pwd_context.hash(payload.password)
    user = await create_user(
        session, username=payload.username, hashed_password=hashed_password, role=payload.role
    )
    await session.commit()
    await session.refresh(user)
    return UserRead.model_validate(user)


@app.post("/auth/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    valid, role = await authenticate_user(session, form_data.username, form_data.password)
    if not valid:
        raise AuthenticationError()
    access_token = create_access_token({"sub": form_data.username, "role": role.value}, settings)
    return Token(access_token=access_token)


@app.get("/machines", response_model=List[MachineBase])
async def get_machines(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[TokenData, Depends(get_current_user)],
) -> List[MachineBase]:
    result = await session.execute(select(Machine))
    machines = result.scalars().all()
    return [MachineBase.model_validate(machine) for machine in machines]


@app.get("/fields", response_model=List[FieldBase])
async def get_fields(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[TokenData, Depends(get_current_user)],
) -> List[FieldBase]:
    result = await session.execute(select(Field))
    fields = result.scalars().all()
    return [FieldBase.model_validate(field) for field in fields]


@app.get("/work-plans", response_model=List[WorkPlanRead])
async def list_plans(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[TokenData, Depends(get_current_user)],
) -> List[WorkPlanRead]:
    plans = await list_work_plans(session)
    return [WorkPlanRead.model_validate(plan) for plan in plans]


@app.post("/work-plans", response_model=WorkPlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: WorkPlanCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[JohnDeereClient, Depends(get_client)],
    _: Annotated[TokenData, Depends(require_role(Role.OPERATOR))],
) -> WorkPlanRead:
    if payload.start_date > payload.end_date:
        raise ValidationError("La fecha de inicio debe ser anterior o igual a la de fin")
    plan = await create_work_plan(
        session,
        field_id=payload.field_id,
        work_type=payload.type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status or "pending",
    )
    await session.commit()
    try:
        await client.create_work_plan(
            {
                "fieldId": payload.field_id,
                "jobType": payload.type.value,
                "startDate": payload.start_date.isoformat(),
                "endDate": payload.end_date.isoformat(),
                "status": payload.status,
            }
        )
    except Exception as exc:
        logger.warning("No se pudo sincronizar plan de trabajo con John Deere: %s", exc)
    return WorkPlanRead.model_validate(plan)


@app.put("/work-plans/{plan_id}", response_model=WorkPlanRead)
async def update_plan(
    plan_id: int,
    payload: WorkPlanUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[JohnDeereClient, Depends(get_client)],
    _: Annotated[TokenData, Depends(require_role(Role.OPERATOR))],
) -> WorkPlanRead:
    plan = await update_work_plan_status(session, plan_id, status=payload.status)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado")
    await session.commit()
    try:
        await client.update_work_plan(str(plan_id), {"status": payload.status})
    except Exception as exc:
        logger.warning("No se pudo actualizar plan en John Deere: %s", exc)
    return WorkPlanRead.model_validate(plan)


@app.delete("/work-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_plan(
    plan_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[JohnDeereClient, Depends(get_client)],
    _: Annotated[TokenData, Depends(require_role(Role.OPERATOR))],
) -> None:
    await delete_work_plan(session, plan_id)
    await session.commit()
    try:
        await client.delete_work_plan(str(plan_id))
    except Exception as exc:
        logger.warning("No se pudo eliminar plan en John Deere: %s", exc)


@app.post("/scheduler/start", response_model=SchedulerStatus)
async def scheduler_start(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> SchedulerStatus:
    start_scheduler(get_sessionmaker())
    status_data = await scheduler_status(session)
    return SchedulerStatus(**status_data)


@app.post("/scheduler/stop", response_model=SchedulerStatus)
async def scheduler_stop(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> SchedulerStatus:
    stop_scheduler()
    status_data = await scheduler_status(session)
    return SchedulerStatus(**status_data)


@app.post("/scheduler/interval", response_model=SchedulerStatus)
async def scheduler_interval(
    seconds: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[TokenData, Depends(require_role(Role.ADMIN))],
) -> SchedulerStatus:
    update_interval(seconds)
    status_data = await scheduler_status(session)
    return SchedulerStatus(**status_data)


@app.get("/scheduler/status", response_model=SchedulerStatus)
async def scheduler_status_endpoint(
    session: Annotated[AsyncSession, Depends(get_session)],
    _: Annotated[TokenData, Depends(get_current_user)],
) -> SchedulerStatus:
    status_data = await scheduler_status(session)
    return SchedulerStatus(**status_data)


@app.get("/john-deere/field-operations")
async def field_operations(
    client: Annotated[JohnDeereClient, Depends(get_client)],
    _: Annotated[TokenData, Depends(get_current_user)],
) -> dict:
    return await client.list_field_operations()


@app.get("/john-deere/field-operations/{operation_id}/measurements")
async def field_operation_measurements(
    operation_id: str,
    measurement_type: str | None = None,
    client: Annotated[JohnDeereClient, Depends(get_client)],
    _: Annotated[TokenData, Depends(get_current_user)],
) -> dict:
    return await client.get_measurements(operation_id, measurement_type)

