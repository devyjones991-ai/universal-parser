from __future__ import annotations

import io
from typing import Iterable, List, Sequence

import pandas as pd

from .monitoring import UserTrackedItem


EXPORT_COLUMNS = ["user_id", "profile", "query", "sku", "title", "sources"]


def _items_to_frame(items: Iterable[UserTrackedItem]) -> pd.DataFrame:
    rows = []
    for item in items:
        rows.append(
            {
                "user_id": item.user_id,
                "profile": item.profile,
                "query": item.query,
                "sku": item.sku or "",
                "title": item.title or "",
                "sources": ",".join(item.sources),
            }
        )
    return pd.DataFrame(rows, columns=EXPORT_COLUMNS)


def export_items(items: Iterable[UserTrackedItem], fmt: str = "xlsx") -> tuple[str, bytes]:
    fmt = fmt.lower()
    df = _items_to_frame(items)
    if df.empty:
        df = pd.DataFrame(columns=EXPORT_COLUMNS)
    if fmt == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Monitoring")
        buffer.seek(0)
        return "monitoring.xlsx", buffer.read()
    if fmt == "csv":
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return "monitoring.csv", csv_buffer.getvalue().encode("utf-8")
    raise ValueError("Поддерживаются форматы csv и xlsx")


def export_items_to_clipboard(items: Iterable[UserTrackedItem], fmt: str = "csv") -> str:
    fmt = fmt.lower()
    df = _items_to_frame(items)
    if df.empty:
        df = pd.DataFrame(columns=EXPORT_COLUMNS)
    if fmt == "csv":
        return df.to_csv(index=False)
    if fmt == "json":
        return df.to_json(orient="records", force_ascii=False)
    raise ValueError("Поддерживаются форматы csv и json для буфера обмена")


def _ensure_sequence(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        if not value.strip():
            return []
        return [s.strip() for s in value.split(",") if s.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(v).strip() for v in value if str(v).strip()]
    if pd.isna(value):  # type: ignore[arg-type]
        return []
    text = str(value).strip()
    return [text] if text else []


def _frame_to_items(df: pd.DataFrame, default_user_id: int | None = None) -> List[UserTrackedItem]:
    items: List[UserTrackedItem] = []
    for _, row in df.iterrows():
        raw_user = row.get("user_id")
        if pd.isna(raw_user) or raw_user in ("", None):
            if default_user_id is None:
                raise ValueError("Не указан user_id для одной из строк")
            user_id = int(default_user_id)
        else:
            user_id = int(raw_user)

        profile = str(row.get("profile", "")).strip()
        query = str(row.get("query", "")).strip()
        if not profile or not query:
            continue

        raw_sku = row.get("sku")
        raw_title = row.get("title")
        sku = None if pd.isna(raw_sku) or raw_sku in (None, "") else str(raw_sku).strip()
        title = None if pd.isna(raw_title) or raw_title in (None, "") else str(raw_title).strip()

        item = UserTrackedItem(
            user_id=user_id,
            profile=profile,
            query=query,
            sku=sku if sku else None,
            title=title if title else None,
            sources=_ensure_sequence(row.get("sources")),
        )
        items.append(item)
    return items


def import_items_from_file(
    file_bytes: bytes, filename: str, default_user_id: int | None = None
) -> List[UserTrackedItem]:
    name = filename.lower()
    if name.endswith(".csv"):
        buffer = io.StringIO(file_bytes.decode("utf-8"))
        df = pd.read_csv(buffer)
    elif name.endswith(".xlsx") or name.endswith(".xls"):
        buffer = io.BytesIO(file_bytes)
        df = pd.read_excel(buffer)
    else:
        raise ValueError("Поддерживаются только CSV и Excel файлы")
    return _frame_to_items(df, default_user_id=default_user_id)


def import_items_from_clipboard(text: str, fmt: str = "csv", default_user_id: int | None = None) -> List[UserTrackedItem]:
    fmt = fmt.lower()
    if fmt == "csv":
        df = pd.read_csv(io.StringIO(text))
    elif fmt == "json":
        df = pd.read_json(io.StringIO(text))
    else:
        raise ValueError("Поддерживаются форматы csv и json для буфера обмена")
    return _frame_to_items(df, default_user_id=default_user_id)


def import_items_from_rows(rows: Sequence[dict], default_user_id: int | None = None) -> List[UserTrackedItem]:
    df = pd.DataFrame(rows, columns=EXPORT_COLUMNS)
    return _frame_to_items(df, default_user_id=default_user_id)
