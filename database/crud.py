import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import DailyTask, Dossier, SpecialistRole, TaskStatus, User


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: str | None = None,
    role: SpecialistRole = SpecialistRole.ARCHITECT,
) -> User:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # Check if this is the very first user in the system
        total_users = await session.scalar(select(func.count(User.id)))
        is_first_user = total_users == 0 or total_users is None

        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            role=role,
            is_active=True,
            is_admin=is_first_user,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_non_admin_users(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.is_admin == False, User.is_active == True)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def set_user_admin(session: AsyncSession, user_id: int, is_admin: bool = True) -> User | None:
    user = await get_user_by_id(session, user_id)
    if user:
        user.is_admin = is_admin
        await session.commit()
        await session.refresh(user)
    return user


async def update_user_role(
    session: AsyncSession,
    telegram_id: int,
    role: SpecialistRole,
) -> User | None:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.role = role
        await session.commit()
        await session.refresh(user)
    return user


async def get_active_users(session: AsyncSession) -> list[User]:
    stmt = select(User).where(User.is_active == True)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_daily_task(
    session: AsyncSession,
    user_id: int,
    project_title: str,
    building_type: str,
    raw_notes: str,
    request_global_tier: bool = False,
    target_date: date | None = None,
) -> DailyTask:
    if target_date is None:
        target_date = date.today()

    task = DailyTask(
        user_id=user_id,
        target_date=target_date,
        project_title=project_title,
        building_type=building_type,
        raw_notes=raw_notes,
        request_global_tier=request_global_tier,
        status=TaskStatus.PENDING,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_pending_tasks_for_research(session: AsyncSession) -> list[DailyTask]:
    stmt = select(DailyTask).options(selectinload(DailyTask.user)).where(DailyTask.status == TaskStatus.PENDING)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_dossier(
    session: AsyncSession,
    task_id: uuid.UUID,
    norms_summary: str,
    materials_summary: str,
    eco_solutions: str,
    full_content: str,
    global_benchmarks: str | None = None,
    cad_dwg_notes: str | None = None,
) -> Dossier:
    dossier = Dossier(
        task_id=task_id,
        norms_summary=norms_summary,
        materials_summary=materials_summary,
        eco_solutions=eco_solutions,
        global_benchmarks=global_benchmarks,
        cad_dwg_notes=cad_dwg_notes,
        full_content=full_content,
    )
    session.add(dossier)

    # Update task status to READY
    stmt = select(DailyTask).where(DailyTask.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    if task:
        task.status = TaskStatus.READY

    await session.commit()
    await session.refresh(dossier)
    return dossier


async def get_ready_dossiers_for_delivery(
    session: AsyncSession,
    target_date: date | None = None,
) -> list[DailyTask]:
    stmt = (
        select(DailyTask)
        .options(selectinload(DailyTask.user), selectinload(DailyTask.dossier))
        .where(DailyTask.status == TaskStatus.READY)
    )
    if target_date:
        stmt = stmt.where(DailyTask.target_date == target_date)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def mark_task_delivered(session: AsyncSession, task_id: uuid.UUID) -> None:
    stmt = select(DailyTask).where(DailyTask.id == task_id)
    result = await session.execute(stmt)
    task = result.scalar_one_or_none()
    if task:
        task.status = TaskStatus.DELIVERED
        await session.commit()
