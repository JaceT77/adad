from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import get_tier_keyboard
from core.orchestrator import orchestrator
from database import crud
from database.connection import async_session

router = Router(name="evening_task_router")


class TaskSubmissionState(StatesGroup):
    waiting_for_project_title = State()
    waiting_for_building_type = State()
    waiting_for_notes = State()
    waiting_for_tier = State()


@router.callback_query(F.data == "action:submit_task")
async def callback_start_task(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(
        "🏗️ *Submit Tomorrow's Project Task*\n\n"
        "Please enter the *Project Title*:\n"
        "_(e.g., 'Navoi Street Commercial Center' or '3-Story Office Building in Yunusabad')_"
    )
    await state.set_state(TaskSubmissionState.waiting_for_project_title)
    await callback.answer()


@router.message(Command("task"))
async def cmd_task(message: Message, state: FSMContext) -> None:
    await message.answer(
        "🏗️ *Submit Tomorrow's Project Task*\n\n"
        "Please enter the *Project Title*:\n"
        "_(e.g., 'Navoi Street Commercial Center' or '3-Story Office Building in Yunusabad')_"
    )
    await state.set_state(TaskSubmissionState.waiting_for_project_title)


@router.message(TaskSubmissionState.waiting_for_project_title)
async def process_project_title(message: Message, state: FSMContext) -> None:
    await state.update_data(project_title=message.text.strip())
    await message.answer(
        "🏢 What is the *Building Typology*?\n\n"
        "_(e.g., 'Commercial Office', 'Residential Cottage', 'Retail Store', 'Automobile Showroom')_"
    )
    await state.set_state(TaskSubmissionState.waiting_for_building_type)


@router.message(TaskSubmissionState.waiting_for_building_type)
async def process_building_type(message: Message, state: FSMContext) -> None:
    await state.update_data(building_type=message.text.strip())
    await message.answer(
        "📝 Please enter any *Specific Instructions or Focus Areas*:\n\n"
        "_(e.g., 'Need cost-effective local wall materials, greywater recycling concept, and check Tashkent design codes for facade')_"
    )
    await state.set_state(TaskSubmissionState.waiting_for_notes)


@router.message(TaskSubmissionState.waiting_for_notes)
async def process_notes(message: Message, state: FSMContext) -> None:
    await state.update_data(raw_notes=message.text.strip())
    await message.answer(
        "🌍 *Design Standards Preference:*\n"
        "Would you like standard Uzbekistan norms only, or should we include a high-spec Global / European benchmark as well?",
        reply_markup=get_tier_keyboard(),
    )
    await state.set_state(TaskSubmissionState.waiting_for_tier)


@router.callback_query(TaskSubmissionState.waiting_for_tier, F.data.startswith("tier:"))
async def process_tier_selection(callback: CallbackQuery, state: FSMContext) -> None:
    tier_choice = callback.data.split(":")[1]
    request_global_tier = tier_choice == "global"

    data = await state.get_data()
    project_title = data["project_title"]
    building_type = data["building_type"]
    raw_notes = data["raw_notes"]

    target_date = date.today() + timedelta(days=1)

    async with async_session() as session:
        user = await crud.get_or_create_user(
            session=session,
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username,
        )

        task = await crud.create_daily_task(
            session=session,
            user_id=user.id,
            project_title=project_title,
            building_type=building_type,
            raw_notes=raw_notes,
            request_global_tier=request_global_tier,
            target_date=target_date,
        )

        # Trigger overnight research orchestrator
        await orchestrator.process_task(session=session, task=task)

    await state.clear()
    confirmation_text = (
        "✅ *Task Registered for Overnight AI Preparation!*\n\n"
        f"• *Project:* `{project_title}`\n"
        f"• *Typology:* `{building_type}`\n"
        f"• *Target Date:* `{target_date}`\n"
        f"• *Tier:* `{'Uzbek Standard + Global Benchmark' if request_global_tier else 'Uzbekistan Standard'}`\n\n"
        "🤖 *The AI has pre-compiled your technical research dossier.*\n"
        "🕘 It will be delivered to you tomorrow morning at *09:00* before you start working!"
    )
    await callback.message.edit_text(confirmation_text)
    await callback.answer("Task saved successfully!")
