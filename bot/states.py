"""FSM состояния для сценариев бота."""
from aiogram.fsm.state import State, StatesGroup


class AlertScenario(StatesGroup):
    waiting_for_name = State()
    waiting_for_url = State()
    waiting_for_conditions = State()


class ImportListScenario(StatesGroup):
    waiting_for_payload = State()
    waiting_for_confirmation = State()


__all__ = ("AlertScenario", "ImportListScenario")
