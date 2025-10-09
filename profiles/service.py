"""Сервисный слой для работы с профилями пользователей Telegram."""

from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from .models import UserHistory, UserProfile, UserSetting, UserTrackedItem


class ProfileService:
    """Предоставляет операции CRUD для профилей, настроек и истории."""

    def __init__(self, session: Session):
        self.session = session

    # --- Работа с профилем ---
    def get_profile(self, telegram_id: int) -> Optional[UserProfile]:
        return (
            self.session.query(UserProfile)
            .filter(UserProfile.telegram_id == telegram_id)
            .one_or_none()
        )

    def create_profile(
        self,
        telegram_id: int,
        *,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> UserProfile:
        profile = UserProfile(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            language_code=language_code,
        )
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def get_or_create_profile(
        self,
        telegram_id: int,
        *,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> UserProfile:
        profile = self.get_profile(telegram_id)
        if profile:
            update_data = {
                "username": username,
                "full_name": full_name,
                "language_code": language_code,
            }
            # Обновляем только непустые значения
            update_data = {k: v for k, v in update_data.items() if v is not None}
            if update_data:
                for key, value in update_data.items():
                    setattr(profile, key, value)
                self.session.commit()
                self.session.refresh(profile)
            return profile

        return self.create_profile(
            telegram_id,
            username=username,
            full_name=full_name,
            language_code=language_code,
        )

    def update_profile(
        self,
        profile: UserProfile,
        **kwargs,
    ) -> UserProfile:
        allowed_fields = {"username", "full_name", "language_code"}
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(profile, field, value)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def delete_profile(self, profile: UserProfile) -> None:
        self.session.delete(profile)
        self.session.commit()

    # --- Настройки ---
    def set_setting(self, profile: UserProfile, key: str, value: str) -> UserSetting:
        setting = (
            self.session.query(UserSetting)
            .filter(UserSetting.profile_id == profile.id, UserSetting.key == key)
            .one_or_none()
        )
        if setting:
            setting.value = value
        else:
            setting = UserSetting(profile=profile, key=key, value=value)
            self.session.add(setting)
        self.session.commit()
        self.session.refresh(setting)
        return setting

    def get_setting(self, profile: UserProfile, key: str) -> Optional[UserSetting]:
        return (
            self.session.query(UserSetting)
            .filter(UserSetting.profile_id == profile.id, UserSetting.key == key)
            .one_or_none()
        )

    def list_settings(self, profile: UserProfile) -> Iterable[UserSetting]:
        return (
            self.session.query(UserSetting)
            .filter(UserSetting.profile_id == profile.id)
            .order_by(UserSetting.key.asc())
            .all()
        )

    def delete_setting(self, profile: UserProfile, key: str) -> bool:
        setting = self.get_setting(profile, key)
        if not setting:
            return False
        self.session.delete(setting)
        self.session.commit()
        return True

    # --- История ---
    def add_history(
        self,
        profile: UserProfile,
        action: str,
        payload: Optional[str] = None,
    ) -> UserHistory:
        history_entry = UserHistory(profile=profile, action=action, payload=payload)
        self.session.add(history_entry)
        self.session.commit()
        self.session.refresh(history_entry)
        return history_entry

    def list_history(
        self,
        profile: UserProfile,
        limit: Optional[int] = None,
    ) -> Iterable[UserHistory]:
        query = (
            self.session.query(UserHistory)
            .filter(UserHistory.profile_id == profile.id)
            .order_by(UserHistory.created_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def clear_history(self, profile: UserProfile) -> int:
        entries = (
            self.session.query(UserHistory)
            .filter(UserHistory.profile_id == profile.id)
            .all()
        )
        deleted = len(entries)
        for entry in entries:
            self.session.delete(entry)
        self.session.commit()
        return deleted

    # --- Отслеживаемые элементы ---
    def add_tracked_item(
        self,
        profile: UserProfile,
        name: str,
        data: Optional[str] = None,
    ) -> UserTrackedItem:
        item = UserTrackedItem(profile=profile, name=name, data=data)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def list_tracked_items(self, profile: UserProfile) -> Iterable[UserTrackedItem]:
        return (
            self.session.query(UserTrackedItem)
            .filter(UserTrackedItem.profile_id == profile.id)
            .order_by(UserTrackedItem.created_at.desc())
            .all()
        )

    def delete_tracked_item(self, item: UserTrackedItem) -> None:
        self.session.delete(item)
        self.session.commit()

