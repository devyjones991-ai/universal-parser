"""Модуль для AI-подсказок по аналитике."""
from __future__ import annotations

from typing import Dict, Optional

from config import settings

try:  # pragma: no cover - внешняя зависимость может отсутствовать на CI
    from openai import OpenAI
except Exception:  # noqa: BLE001 - важно поймать любые ошибки импортов
    OpenAI = None  # type: ignore


class AIAdvisor:
    """Генератор подсказок на базе LLM либо эвристик."""

    def __init__(self):
        self._client: Optional[OpenAI] = None
        if settings.OPENAI_API_KEY and OpenAI:
            try:
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception:  # pragma: no cover - чтобы не падать без сети/ключа
                self._client = None

    def build_prompt(self, report: Dict) -> str:
        price_stats = report.get("price_stats", {})
        inventory_stats = report.get("inventory_stats", {})
        anomalies = report.get("price_anomalies", [])
        stock_anomalies = report.get("inventory_anomalies", [])

        prompt = [
            "Ты — аналитик по продажам. Проанализируй данные и дай рекомендации.",
            f"Профиль: {report.get('profile_name')}",
            f"Товар: {report.get('item_id')}",
            f"Период: {report.get('start')} — {report.get('end')}",
            "Цена:",
            f"  Средняя: {price_stats.get('average')}",
            f"  Изменение: {price_stats.get('change_percent')}",
            f"Аномалии цен: {anomalies}",
            "Склад:",
            f"  Среднее наличие: {inventory_stats.get('average')}",
            f"Аномалии склада: {stock_anomalies}",
            "Дай три конкретные рекомендации по продажам или закупкам на русском языке.",
        ]
        return "\n".join(str(line) for line in prompt)

    def advise(self, report: Dict) -> str:
        prompt = self.build_prompt(report)
        if self._client:
            try:  # pragma: no cover - сложно эмулировать сетевые вызовы
                completion = self._client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=300,
                )
                return completion.choices[0].message.content.strip()
            except Exception:
                pass

        # Фолбэк: простые рекомендации без LLM
        advice = []
        price_stats = report.get("price_stats", {})
        inventory_stats = report.get("inventory_stats", {})
        change = price_stats.get("change_percent") or 0

        if change > 5:
            advice.append("Усилить продвижение, пока цена растёт и спрос подтверждён.")
        elif change < -5:
            advice.append("Рассмотреть скидки или акции для компенсации падения цены.")
        else:
            advice.append("Поддерживать текущую ценовую стратегию и мониторить тренд еженедельно.")

        average_stock = inventory_stats.get("average") or 0
        if average_stock < 5:
            advice.append("Запланировать пополнение склада: средний остаток ниже безопасного уровня.")
        else:
            advice.append("Запасы стабильные, можно оптимизировать складские расходы.")

        anomalies = report.get("price_anomalies") or []
        if anomalies:
            advice.append("Проверить дни с аномальными ценами: возможны ошибки загрузки или акции конкурентов.")
        else:
            advice.append("Аномалий не обнаружено, сохраняем текущую частоту мониторинга.")

        return "\n".join(advice)


advisor = AIAdvisor()
