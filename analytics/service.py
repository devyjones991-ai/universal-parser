"""Сервис аналитики: расчёт трендов, средних значений, поиск аномалий."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from config import settings
from db import InventoryHistory, PriceHistory, SessionLocal, init_db

try:  # pragma: no cover - matplotlib может отсутствовать на CI
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: E402  # pylint: disable=wrong-import-position
except ImportError:  # pragma: no cover - gracefully degrade
    matplotlib = None  # type: ignore
    plt = None  # type: ignore


@dataclass
class TimeSeriesPoint:
    timestamp: datetime
    value: Optional[float]
    extra: Dict[str, Optional[float]]


def _ensure_datetime(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def resolve_period(
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[datetime, datetime]:
    """Возвращает интервал времени на основе периода или явных дат."""

    now = datetime.utcnow()
    end = _ensure_datetime(end_date) or now

    if start_date:
        start = _ensure_datetime(start_date)
        if start:
            return start, end

    period = (period or settings.ANALYTICS_DEFAULT_PERIOD or "7d").lower()
    delta = timedelta(days=7)
    if period.endswith("d") and period[:-1].isdigit():
        delta = timedelta(days=int(period[:-1]))
    elif period.endswith("w") and period[:-1].isdigit():
        delta = timedelta(weeks=int(period[:-1]))
    elif period.endswith("m") and period[:-1].isdigit():
        delta = timedelta(days=int(period[:-1]) * 30)

    start = end - delta
    return start, end


def _fetch_history(
    model,
    profile_name: Optional[str],
    item_id: Optional[str],
    start: datetime,
    end: datetime,
) -> List:
    init_db()
    with SessionLocal() as session:
        query = session.query(model).filter(model.created_at.between(start, end))
        if profile_name:
            query = query.filter(model.profile_name == profile_name)
        if item_id:
            query = query.filter(model.item_id == item_id)
        return list(query.order_by(model.created_at.asc()))


def _to_series(points: Iterable, value_attr: str, extras: Optional[List[str]] = None) -> List[TimeSeriesPoint]:
    series: List[TimeSeriesPoint] = []
    for point in points:
        value = getattr(point, value_attr, None)
        extra_data = {}
        if extras:
            for attr in extras:
                extra_data[attr] = getattr(point, attr, None)
        series.append(TimeSeriesPoint(timestamp=point.created_at, value=value, extra=extra_data))
    return series


def _calculate_linear_trend(series: List[TimeSeriesPoint]) -> float:
    values = [p.value for p in series if p.value is not None]
    if len(values) < 2:
        return 0.0

    indexed_values = [(index, value) for index, value in enumerate(values)]
    n = len(indexed_values)
    mean_x = sum(idx for idx, _ in indexed_values) / n
    mean_y = sum(val for _, val in indexed_values) / n

    numerator = sum((idx - mean_x) * (val - mean_y) for idx, val in indexed_values)
    denominator = sum((idx - mean_x) ** 2 for idx, _ in indexed_values)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _calculate_basic_stats(series: List[TimeSeriesPoint]) -> Dict[str, Optional[float]]:
    values = [p.value for p in series if p.value is not None]
    if not values:
        return {
            "average": None,
            "minimum": None,
            "maximum": None,
            "trend": 0.0,
            "change_percent": None,
            "last": None,
            "first": None,
        }

    first = values[0]
    last = values[-1]
    change_percent = ((last - first) / first * 100) if first else None

    return {
        "average": sum(values) / len(values),
        "minimum": min(values),
        "maximum": max(values),
        "trend": _calculate_linear_trend(series),
        "change_percent": change_percent,
        "last": last,
        "first": first,
    }


def _detect_anomalies(series: List[TimeSeriesPoint], threshold: float = 2.5) -> List[TimeSeriesPoint]:
    values = [p.value for p in series if p.value is not None]
    if len(values) < 3:
        return []
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    std = math.sqrt(variance)
    if std == 0:
        return []

    anomalies: List[TimeSeriesPoint] = []
    for point in series:
        if point.value is None:
            continue
        z_score = abs(point.value - mean) / std
        if z_score >= threshold:
            anomalies.append(point)
    return anomalies


def build_analytics_report(
    profile_name: Optional[str] = None,
    item_id: Optional[str] = None,
    period: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict:
    start, end = resolve_period(period, start_date, end_date)

    price_history_records = _fetch_history(PriceHistory, profile_name, item_id, start, end)
    inventory_history_records = _fetch_history(InventoryHistory, profile_name, item_id, start, end)

    price_series = _to_series(price_history_records, "price", ["currency", "price_change", "change_percent"])
    inventory_series = _to_series(inventory_history_records, "stock_level", ["availability"])

    report = {
        "profile_name": profile_name,
        "item_id": item_id,
        "start": start,
        "end": end,
        "price_history": [
            {
                "timestamp": point.timestamp.isoformat(),
                "price": point.value,
                "currency": point.extra.get("currency"),
                "price_change": point.extra.get("price_change"),
                "change_percent": point.extra.get("change_percent"),
            }
            for point in price_series
        ],
        "inventory_history": [
            {
                "timestamp": point.timestamp.isoformat(),
                "stock_level": point.value,
                "availability": point.extra.get("availability"),
            }
            for point in inventory_series
        ],
        "price_stats": _calculate_basic_stats(price_series),
        "inventory_stats": _calculate_basic_stats(inventory_series),
        "price_anomalies": [
            {
                "timestamp": point.timestamp.isoformat(),
                "price": point.value,
            }
            for point in _detect_anomalies(price_series)
        ],
        "inventory_anomalies": [
            {
                "timestamp": point.timestamp.isoformat(),
                "stock_level": point.value,
            }
            for point in _detect_anomalies(inventory_series)
        ],
    }

    return report


def format_report_text(report: Dict) -> str:
    """Форматирует отчёт в текстовом виде для отправки в Telegram."""

    price_stats = report.get("price_stats", {})
    inventory_stats = report.get("inventory_stats", {})
    lines = ["📈 Аналитика"]
    if report.get("profile_name"):
        lines.append(f"Профиль: {report['profile_name']}")
    if report.get("item_id"):
        lines.append(f"Товар: {report['item_id']}")
    lines.append(
        "Период: {:%Y-%m-%d} — {:%Y-%m-%d}".format(report["start"], report["end"])
    )

    def _fmt(value: Optional[float]) -> str:
        return "—" if value is None else f"{value:,.2f}".replace(",", " ")

    lines.append("")
    lines.append("💵 Цена:")
    lines.append(f"  Средняя: {_fmt(price_stats.get('average'))}")
    lines.append(f"  Мин: {_fmt(price_stats.get('minimum'))}")
    lines.append(f"  Макс: {_fmt(price_stats.get('maximum'))}")
    change = price_stats.get("change_percent")
    change_str = "—" if change is None else f"{change:+.2f}%"
    lines.append(f"  Изменение: {change_str}")
    lines.append("")
    lines.append("📦 Склад:")
    lines.append(f"  Среднее наличие: {_fmt(inventory_stats.get('average'))}")
    lines.append(f"  Мин: {_fmt(inventory_stats.get('minimum'))}")
    lines.append(f"  Макс: {_fmt(inventory_stats.get('maximum'))}")

    anomalies = report.get("price_anomalies") or []
    if anomalies:
        lines.append("")
        lines.append("⚠️ Ценовые аномалии:")
        for point in anomalies[:5]:
            lines.append(f"  {point['timestamp']}: {point['price']}")

    stock_anomalies = report.get("inventory_anomalies") or []
    if stock_anomalies:
        lines.append("")
        lines.append("⚠️ Аномалии запаса:")
        for point in stock_anomalies[:5]:
            lines.append(f"  {point['timestamp']}: {point['stock_level']}")

    if not anomalies and not stock_anomalies:
        lines.append("")
        lines.append("✅ Аномалии не выявлены")

    return "\n".join(lines)


def _merge_history_rows(report: Dict) -> List[Dict]:
    combined: Dict[str, Dict[str, Optional[float]]] = {}
    for entry in report.get("price_history", []):
        combined.setdefault(entry["timestamp"], {}).update(
            {
                "timestamp": entry["timestamp"],
                "price": entry.get("price"),
                "currency": entry.get("currency"),
                "price_change": entry.get("price_change"),
                "change_percent": entry.get("change_percent"),
            }
        )
    for entry in report.get("inventory_history", []):
        combined.setdefault(entry["timestamp"], {}).update(
            {
                "timestamp": entry["timestamp"],
                "stock_level": entry.get("stock_level"),
                "availability": entry.get("availability"),
            }
        )

    rows = list(combined.values())
    rows.sort(key=lambda row: row.get("timestamp", ""))
    return rows


def export_report(report: Dict, export_format: str = "csv") -> Tuple[BytesIO, str, str]:
    """Экспортирует отчёт в CSV или JSON и возвращает буфер, имя файла и MIME."""

    rows = _merge_history_rows(report)
    if not rows:
        raise ValueError("Нет данных для экспорта")

    df = pd.DataFrame(rows)
    buffer = BytesIO()
    filename = f"analytics_{report.get('profile_name') or 'all'}_{report.get('item_id') or 'summary'}"

    if export_format.lower() == "csv":
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return buffer, f"{filename}.csv", "text/csv"

    if export_format.lower() == "json":
        buffer.write(df.to_json(orient="records", force_ascii=False).encode("utf-8"))
        buffer.seek(0)
        return buffer, f"{filename}.json", "application/json"

    raise ValueError("Неподдерживаемый формат экспорта")


def generate_price_chart(report: Dict) -> Optional[BytesIO]:
    if plt is None:
        return None

    history = report.get("price_history") or []
    if not history:
        return None

    timestamps = [datetime.fromisoformat(item["timestamp"]) for item in history]
    prices = [item.get("price") for item in history]
    currency = history[-1].get("currency") or ""

    plt.figure(figsize=(8, 4))
    plt.plot(timestamps, prices, marker="o", linestyle="-")
    plt.title("Динамика цены")
    plt.xlabel("Дата")
    plt.ylabel(f"Цена {currency}".strip())
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    plt.close()
    buffer.seek(0)
    return buffer
