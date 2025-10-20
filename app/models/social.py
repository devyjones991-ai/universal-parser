"""Модели для социальных функций и геймификации"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from app.core.database import Base

# Таблица связей друзей
friendship = Table(
    'friendships',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('friend_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('status', String(20), default='pending'),  # pending, accepted, blocked
    Column('created_at', DateTime, default=datetime.utcnow)
)

# Таблица подписок на пользователей
follows = Table(
    'follows',
    Base.metadata,
    Column('follower_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('following_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow)
)

# Таблица участников групп
group_members = Table(
    'group_members',
    Base.metadata,
    Column('group_id', UUID(as_uuid=True), ForeignKey('groups.id'), primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role', String(20), default='member'),  # member, moderator, admin
    Column('joined_at', DateTime, default=datetime.utcnow)
)

class UserProfile(Base):
    """Расширенный профиль пользователя"""
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    # Основная информация
    display_name = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(200), nullable=True)

    # Статистика
    level = Column(Integer, default=1)
    experience_points = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    reputation = Column(Integer, default=0)

    # Настройки приватности
    is_public = Column(Boolean, default=True)
    show_email = Column(Boolean, default=False)
    show_phone = Column(Boolean, default=False)
    allow_friend_requests = Column(Boolean, default=True)
    allow_messages = Column(Boolean, default=True)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="profile")
    achievements = relationship("UserAchievement", back_populates="user_profile")
    posts = relationship("SocialPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    likes = relationship("Like", back_populates="user")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")

class Group(Base):
    """Группы и сообщества"""
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)

    # Настройки группы
    is_public = Column(Boolean, default=True)
    is_private = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    max_members = Column(Integer, nullable=True)

    # Статистика
    member_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)

    # Владелец
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    owner = relationship("User", back_populates="owned_groups")
    members = relationship("User", secondary=group_members, back_populates="groups")
    posts = relationship("SocialPost", back_populates="group")

class Achievement(Base):
    """Достижения"""
    __tablename__ = "achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)

    # Тип достижения
    category = Column(String(50), nullable=False)  # parsing, social, trading, etc.
    type = Column(String(50), nullable=False)  # milestone, streak, special, etc.

    # Условия получения
    condition_type = Column(String(50), nullable=False)  # count, value, streak, etc.
    condition_value = Column(Integer, nullable=False)
    condition_data = Column(JSON, nullable=True)  # Дополнительные условия

    # Награда
    points_reward = Column(Integer, default=0)
    badge_reward = Column(String(100), nullable=True)

    # Настройки
    is_active = Column(Boolean, default=True)
    is_hidden = Column(Boolean, default=False)  # Скрытое достижение

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user_achievements = relationship("UserAchievement", back_populates="achievement")

class UserAchievement(Base):
    """Достижения пользователей"""
    __tablename__ = "user_achievements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    achievement_id = Column(UUID(as_uuid=True), ForeignKey("achievements.id"), nullable=False)

    # Прогресс
    progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    user_profile = relationship("UserProfile", back_populates="achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

class SocialPost(Base):
    """Социальные посты"""
    __tablename__ = "social_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id"), nullable=True)

    # Содержимое
    content = Column(Text, nullable=False)
    media_urls = Column(JSON, nullable=True)  # Ссылки на медиафайлы
    post_type = Column(String(20), default='text')  # text, image, video, link, etc.

    # Связанные данные
    item_id = Column(UUID(as_uuid=True), ForeignKey("tracked_items.id"), nullable=True)
    marketplace = Column(String(50), nullable=True)

    # Настройки
    is_public = Column(Boolean, default=True)
    allow_comments = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)

    # Статистика
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    author = relationship("UserProfile", back_populates="posts")
    group = relationship("Group", back_populates="posts")
    item = relationship("TrackedItem", back_populates="posts")
    comments = relationship("Comment", back_populates="post")
    likes = relationship("Like", back_populates="post")

class Comment(Base):
    """Комментарии к постам"""
    __tablename__ = "comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_posts.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)

    # Содержимое
    content = Column(Text, nullable=False)
    media_urls = Column(JSON, nullable=True)

    # Статистика
    like_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    post = relationship("SocialPost", back_populates="comments")
    author = relationship("UserProfile", back_populates="comments")
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent")
    likes = relationship("Like", back_populates="comment")

class Like(Base):
    """Лайки"""
    __tablename__ = "likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey("social_posts.id"), nullable=True)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id"), nullable=True)

    # Тип лайка
    like_type = Column(String(20), default='like')  # like, love, laugh, angry, etc.

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("UserProfile", back_populates="likes")
    post = relationship("SocialPost", back_populates="likes")
    comment = relationship("Comment", back_populates="likes")

class Message(Base):
    """Личные сообщения"""
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)

    # Содержимое
    content = Column(Text, nullable=False)
    media_urls = Column(JSON, nullable=True)
    message_type = Column(String(20), default='text')  # text, image, file, etc.

    # Статус
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    sender = relationship("UserProfile", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("UserProfile", foreign_keys=[receiver_id], back_populates="messages_received")

class Leaderboard(Base):
    """Лидерборды"""
    __tablename__ = "leaderboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Тип лидерборда
    category = Column(String(50), nullable=False)  # parsing, trading, social, etc.
    period = Column(String(20), default='all')  # daily, weekly, monthly, all

    # Настройки
    is_active = Column(Boolean, default=True)
    max_entries = Column(Integer, default=100)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    entries = relationship("LeaderboardEntry", back_populates="leaderboard")

class LeaderboardEntry(Base):
    """Записи в лидерборде"""
    __tablename__ = "leaderboard_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    leaderboard_id = Column(UUID(as_uuid=True), ForeignKey("leaderboards.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)

    # Показатели
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)

    # Дополнительные данные
    metadata = Column(JSON, nullable=True)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    leaderboard = relationship("Leaderboard", back_populates="entries")
    user = relationship("UserProfile")

class Notification(Base):
    """Уведомления"""
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user_profiles.id"), nullable=False)

    # Содержимое
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # friend_request, like, comment, etc.

    # Связанные данные
    related_id = Column(UUID(as_uuid=True), nullable=True)  # ID связанного объекта
    related_type = Column(String(50), nullable=True)  # post, comment, user, etc.

    # Статус
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("UserProfile")
