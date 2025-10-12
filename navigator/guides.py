"""Справочные материалы для пользователей парсера."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Tuple

__all__ = [
    "GuideSection",
    "GUIDES",
    "get_section",
    "update_section",
    "list_sections",
    "get_paginated_faq",
]


@dataclass(slots=True)
class GuideSection:
    """Отдельная секция справочной информации."""

    title: str
    content: List[str]
    updated_at: datetime
    editable: bool = False

    def as_text(self) -> str:
        return "\n".join(self.content)


GUIDES: Dict[str, GuideSection] = {
    "quickstart": GuideSection(
        title="Быстрый старт",
        content=[
            "1. Выберите профиль парсинга или подготовьте URL.",
            "2. Запустите команду /parse или /run в боте.",
            "3. Просмотрите результаты и экспортируйте при необходимости.",
        ],
        updated_at=datetime.now(timezone.utc),
        editable=False,
    ),
    "roadmap": GuideSection(
        title="Дорожная карта",
        content=[
            "✔️ Поддержка новых форматов экспорта.",
            "🔄 Интеграция с CRM для поставщиков.",
            "🧠 Автоопределение качества данных.",
        ],
        updated_at=datetime.now(timezone.utc),
        editable=True,
    ),
    "faq": GuideSection(
        title="FAQ",
        content=[
            "Q: Как добавить новый профиль?",
            "A: Используйте JSON-файл в каталоге profiles.",
            "Q: Можно ли запускать парсер по расписанию?",
            "A: Да, через cron или внешние планировщики.",
            "Q: Где хранится история результатов?",
            "A: В SQLite базе, управляемой модулем db.py.",
        ],
        updated_at=datetime.now(timezone.utc),
        editable=True,
    ),
}


def list_sections() -> List[Tuple[str, GuideSection]]:
    """Возвращает список секций с ключами."""

    return sorted(GUIDES.items(), key=lambda item: item[0])


def get_section(key: str) -> GuideSection:
    if key not in GUIDES:
        raise KeyError(f"Секция '{key}' не найдена")
    return GUIDES[key]


def update_section(key: str, content: List[str]) -> GuideSection:
    section = get_section(key)
    if not section.editable:
        raise PermissionError("Секция защищена от редактирования")
    section.content = content
    section.updated_at = datetime.now(timezone.utc)
    return section


def get_paginated_faq(page: int = 1, per_page: int = 2) -> Tuple[List[str], int]:
    """Возвращает FAQ постранично."""

    faq = get_section("faq")
    total_items = len(faq.content) // 2  # В FAQ пары вопросов/ответов
    start = (page - 1) * per_page * 2
    end = start + per_page * 2
    items = faq.content[start:end]
    pages = max(1, (total_items + per_page - 1) // per_page)
    return items, pages
