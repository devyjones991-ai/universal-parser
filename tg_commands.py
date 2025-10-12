"""Основные обработчики Telegram-бота."""
from __future__ import annotations

import asyncio
import io
import json
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)
from urllib.parse import quote_plus, unquote_plus

from alerts.checker import AlertChecker
from alerts.service import AlertNotFoundError, AlertService, AlertServiceError
from bot import bot, dp
from bot.keyboards import (
    MAIN_MENU,
    build_import_confirmation_keyboard,
    build_results_actions,
)
from bot.services import Alert, ImportBatch, add_alert, register_import
from bot.states import AlertScenario, ImportListScenario
from config import parsing_profiles, settings
from db import get_recent_results, save_results
from navigator import build_help_section
from navigator.guides import get_section, get_paginated_faq
from navigator.logistics import Carrier, find_carriers, initialise_storage
from navigator.suppliers import search_suppliers, OPEN_CATALOGS
from parser import UniversalParser
from profiles.monitoring import MonitoringStorage

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
alert_service = AlertService()
alert_checker = AlertChecker(bot=bot, service=alert_service)
monitoring_storage = MonitoringStorage()

router = Router(name="main")


SUPPLIERS_PAGE_SIZE = 5
LOGISTICS_PAGE_SIZE = 5
FAQ_PAGE_SIZE = 2


# Проверка доступа