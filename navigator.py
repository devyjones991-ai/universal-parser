"""Справочные данные и FAQ для бота."""
from __future__ import annotations

from textwrap import dedent
from typing import Iterable, List, Tuple

FAQ_ITEMS: List[Tuple[str, str]] = [
    (
        "Как добавить алерт?",
        "Используйте кнопку \"➕ Добавить алерт\" и следуйте пошаговым подсказкам.",
    ),
    (
        "Как импортировать список ссылок?",
        "Выберите действие \"📥 Импорт списка\", вставьте ссылки и подтвердите импорт.",
    ),
    (
        "Можно ли повторно запустить профиль?",
        "Да, откройте раздел результатов и воспользуйтесь инлайн-кнопкой \"🔁 Повторить\".",
    ),
    (
        "Как экспортировать данные?",
        "Используйте команду /export или инлайн-кнопку \"📤 Экспортировать\" в результатах.",
    ),
]


def build_help_section(commands: Iterable[str]) -> str:
    commands_block = "\n".join(f"• {command}" for command in commands)
    faq_block = "\n\n".join(f"<b>{question}</b>\n{answer}" for question, answer in FAQ_ITEMS)
    return dedent(
        f"""
        <b>Доступные команды:</b>
        {commands_block}
        \n
        <b>FAQ:</b>
        {faq_block}
        """
    ).strip()


__all__ = ("FAQ_ITEMS", "build_help_section")
