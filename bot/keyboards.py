"""Наборы клавиатур для бота."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить алерт"),
            KeyboardButton(text="📥 Импорт списка"),
        ],
        [
            KeyboardButton(text="📊 Последние результаты"),
            KeyboardButton(text="ℹ️ Помощь"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие",
)


def build_results_actions(profile_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔁 Повторить",
                    callback_data=f"results:rerun:{profile_name}",
                ),
                InlineKeyboardButton(
                    text="📤 Экспортировать",
                    callback_data=f"results:export:{profile_name}",
                ),
            ]
        ]
    )


def build_import_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Сохранить", callback_data="import:confirm"),
                InlineKeyboardButton(text="↩️ Отменить", callback_data="import:cancel"),
            ]
        ]
    )


__all__ = ("MAIN_MENU", "build_results_actions", "build_import_confirmation_keyboard")
