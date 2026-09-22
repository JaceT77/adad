from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import SpecialistRole


def get_role_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🏛️ Arxitektor",
                callback_data=f"role:{SpecialistRole.ARCHITECT.value}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🏗️ Konstruktor (Muhandis)",
                callback_data=f"role:{SpecialistRole.STRUCTURAL_ENGINEER.value}",
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Smetachi (Smetchik)",
                callback_data=f"role:{SpecialistRole.COST_ESTIMATOR.value}",
            )
        ],
        [
            InlineKeyboardButton(
                text="🎨 Interyer va Fasad Dizayneri",
                callback_data=f"role:{SpecialistRole.INTERIOR_DESIGNER.value}",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tier_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="🇺🇿 O'zbekiston standarti (Asosiy / Tejamkor)",
                callback_data="tier:local",
            )
        ],
        [
            InlineKeyboardButton(
                text="🌍 Jahon / Yevropa standarti bilan birga",
                callback_data="tier:global",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_start_task_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Ertangi loyiha vazifasini kiritish",
                callback_data="action:submit_task",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
