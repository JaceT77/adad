import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SpecialistRole(str, enum.Enum):
    ARCHITECT = "architect"  # Floor plans, finishes, aesthetics
    STRUCTURAL_ENGINEER = "structural_engineer"  # Konstruktor: framing, load-bearing
    COST_ESTIMATOR = "cost_estimator"  # Smetchik: material cost & quantities
    INTERIOR_DESIGNER = "interior_designer"  # Interior & Facade styling


class TaskStatus(str, enum.Enum):
    PENDING = "pending"  # Registered in evening, awaiting overnight research
    RESEARCHING = "researching"  # AI actively synthesizing
    READY = "ready"  # Dossier generated, ready for 09:00 delivery
    DELIVERED = "delivered"  # Pushed to specialist on Telegram


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[SpecialistRole] = mapped_column(
        Enum(SpecialistRole, name="specialist_role_enum"),
        default=SpecialistRole.ARCHITECT,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    tasks: Mapped[list["DailyTask"]] = relationship("DailyTask", back_populates="user", cascade="all, delete-orphan")


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    project_title: Mapped[str] = mapped_column(String(255), nullable=False)
    building_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., office, dom, showroom
    raw_notes: Mapped[str] = mapped_column(Text, nullable=False)
    request_global_tier: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum"),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tasks")
    dossier: Mapped["Dossier | None"] = relationship(
        "Dossier", back_populates="task", uselist=False, cascade="all, delete-orphan"
    )


class Dossier(Base):
    __tablename__ = "dossiers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_tasks.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    norms_summary: Mapped[str] = mapped_column(Text, nullable=False)
    materials_summary: Mapped[str] = mapped_column(Text, nullable=False)
    eco_solutions: Mapped[str] = mapped_column(Text, nullable=False)
    global_benchmarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    cad_dwg_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    task: Mapped["DailyTask"] = relationship("DailyTask", back_populates="dossier")
