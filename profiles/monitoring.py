from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional


MONITORING_STORAGE_PATH = Path("profiles/user_monitoring.json")


@dataclass
class UserTrackedItem:
    """Описание элемента мониторинга пользователя."""

    user_id: int
    profile: str
    query: str
    sku: Optional[str] = None
    title: Optional[str] = None
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["sources"] = list(self.sources)
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "UserTrackedItem":
        return cls(
            user_id=int(data["user_id"]),
            profile=data["profile"],
            query=data["query"],
            sku=data.get("sku") or None,
            title=data.get("title") or None,
            sources=[s for s in data.get("sources", []) if s],
        )

    def as_kwargs(self) -> Dict[str, object]:
        payload: Dict[str, object] = {"query": self.query}
        if self.sku:
            payload["sku"] = self.sku
        if self.title:
            payload["title"] = self.title
        if self.sources:
            payload["sources"] = self.sources
        return payload


class MonitoringStorage:
    """Хранилище пользовательских мониторингов."""

    def __init__(self, path: Path | str = MONITORING_STORAGE_PATH):
        self.path = Path(path)

    def _load_raw(self) -> Dict[str, List[Dict]]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _save_raw(self, data: Dict[str, List[Dict]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)

    def list_items(
        self, user_id: Optional[int] = None, profile: Optional[str] = None
    ) -> List[UserTrackedItem]:
        data = self._load_raw()
        items: List[UserTrackedItem] = []
        for uid, entries in data.items():
            if user_id is not None and int(uid) != int(user_id):
                continue
            for entry in entries:
                item = UserTrackedItem.from_dict({"user_id": uid, **entry})
                if profile and item.profile != profile:
                    continue
                items.append(item)
        return items

    def list_user_items(self, user_id: int, profile: Optional[str] = None) -> List[UserTrackedItem]:
        return self.list_items(user_id=user_id, profile=profile)

    def add_item(self, item: UserTrackedItem) -> bool:
        data = self._load_raw()
        user_key = str(item.user_id)
        entries = data.setdefault(user_key, [])
        for entry in entries:
            if entry["profile"] == item.profile and entry["query"] == item.query:
                return False
        entries.append(
            {
                "profile": item.profile,
                "query": item.query,
                "sku": item.sku,
                "title": item.title,
                "sources": list(item.sources),
            }
        )
        self._save_raw(data)
        return True

    def remove_item(
        self,
        user_id: int,
        profile: str,
        query: Optional[str] = None,
    ) -> bool:
        data = self._load_raw()
        user_key = str(user_id)
        if user_key not in data:
            return False
        entries = data[user_key]
        before = len(entries)
        entries = [
            entry
            for entry in entries
            if not (
                entry["profile"] == profile
                and (query is None or entry["query"] == query)
            )
        ]
        if len(entries) == before:
            return False
        if entries:
            data[user_key] = entries
        else:
            data.pop(user_key)
        self._save_raw(data)
        return True

    def replace_user_items(self, user_id: int, items: Iterable[UserTrackedItem]) -> None:
        data = self._load_raw()
        data[str(user_id)] = [
            {
                "profile": item.profile,
                "query": item.query,
                "sku": item.sku,
                "title": item.title,
                "sources": list(item.sources),
            }
            for item in items
        ]
        self._save_raw(data)

    def extend_user_items(self, user_id: int, items: Iterable[UserTrackedItem]) -> int:
        added = 0
        for item in items:
            if item.user_id != user_id:
                item.user_id = user_id
            if self.add_item(item):
                added += 1
        return added
