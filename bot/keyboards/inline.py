from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import SpecialistRole


def get_role_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🏛️ Architect (Arxitektor)",
                callback_data=f"role:{SpecialistRole.ARCHITECT.value}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏗️ Structural Engineer (Konstruktor)",
                callback_data=f"role:{SpecialistRole.STRUCTURAL_ENGINEER.value}",
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Cost Estimator (Smetchik)",
                callback_data=f"role:{SpecialistRole.COST_ESTIMATOR.value}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Interior & Facade Designer",
                callback_data=f"role:{SpecialistRole.INTERIOR_DESIGNER.value}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tier_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🇺🇿 Local Uzbekistan Standard (Default)",
                callback_data="tier:local",
            )
        ],
        [
            InlineKeyboardButton(
                text="🌍 Include Global / European Benchmark",
                callback_data="tier:global",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_start_task_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Submit Tomorrow's Project Task",
                callback_data="action:submit_task",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
