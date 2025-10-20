"""Pydantic схемы для социальных функций и геймификации"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class PostType(str, Enum):
    """Типы постов"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    LINK = "link"
    ITEM = "item"


class LikeType(str, Enum):
    """Типы лайков"""
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    ANGRY = "angry"
    SAD = "sad"


class MessageType(str, Enum):
    """Типы сообщений"""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    STICKER = "sticker"


class NotificationType(str, Enum):
    """Типы уведомлений"""
    FRIEND_REQUEST = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"
    LIKE = "like"
    COMMENT = "comment"
    MESSAGE = "message"
    ACHIEVEMENT = "achievement"
    GROUP_INVITE = "group_invite"
    MENTION = "mention"


class UserProfileBase(BaseModel):
    """Базовая схема профиля пользователя"""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    is_public: bool = True
    show_email: bool = False
    show_phone: bool = False
    allow_friend_requests: bool = True
    allow_messages: bool = True


class UserProfileCreate(UserProfileBase):
    """Схема создания профиля пользователя"""
    user_id: str


class UserProfileUpdate(BaseModel):
    """Схема обновления профиля пользователя"""
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    is_public: Optional[bool] = None
    show_email: Optional[bool] = None
    show_phone: Optional[bool] = None
    allow_friend_requests: Optional[bool] = None
    allow_messages: Optional[bool] = None


class UserProfileResponse(UserProfileBase):
    """Схема ответа профиля пользователя"""
    id: str
    user_id: str
    level: int
    experience_points: int
    total_points: int
    reputation: int
    created_at: datetime
    updated_at: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class GroupBase(BaseModel):
    """Базовая схема группы"""
    name: str
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    is_public: bool = True
    is_private: bool = False
    requires_approval: bool = False
    max_members: Optional[int] = None


class GroupCreate(GroupBase):
    """Схема создания группы"""
    pass


class GroupUpdate(BaseModel):
    """Схема обновления группы"""
    name: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    is_public: Optional[bool] = None
    is_private: Optional[bool] = None
    requires_approval: Optional[bool] = None
    max_members: Optional[int] = None


class GroupResponse(GroupBase):
    """Схема ответа группы"""
    id: str
    owner_id: str
    member_count: int
    post_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AchievementBase(BaseModel):
    """Базовая схема достижения"""
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    category: str
    type: str
    condition_type: str
    condition_value: int
    condition_data: Optional[Dict[str, Any]] = None
    points_reward: int = 0
    badge_reward: Optional[str] = None
    is_hidden: bool = False


class AchievementCreate(AchievementBase):
    """Схема создания достижения"""
    pass


class AchievementResponse(AchievementBase):
    """Схема ответа достижения"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserAchievementResponse(BaseModel):
    """Схема ответа достижения пользователя"""
    id: str
    user_id: str
    achievement_id: str
    progress: int
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    achievement: AchievementResponse

    class Config:
        from_attributes = True


class SocialPostBase(BaseModel):
    """Базовая схема социального поста"""
    content: str
    media_urls: Optional[List[str]] = None
    post_type: PostType = PostType.TEXT
    is_public: bool = True
    allow_comments: bool = True


class SocialPostCreate(SocialPostBase):
    """Схема создания социального поста"""
    group_id: Optional[str] = None
    item_id: Optional[str] = None
    marketplace: Optional[str] = None


class SocialPostUpdate(BaseModel):
    """Схема обновления социального поста"""
    content: Optional[str] = None
    media_urls: Optional[List[str]] = None
    is_public: Optional[bool] = None
    allow_comments: Optional[bool] = None
    is_pinned: Optional[bool] = None


class SocialPostResponse(SocialPostBase):
    """Схема ответа социального поста"""
    id: str
    author_id: str
    group_id: Optional[str]
    item_id: Optional[str]
    marketplace: Optional[str]
    is_pinned: bool
    like_count: int
    comment_count: int
    share_count: int
    view_count: int
    created_at: datetime
    updated_at: datetime
    author: UserProfileResponse

    class Config:
        from_attributes = True


class CommentBase(BaseModel):
    """Базовая схема комментария"""
    content: str
    media_urls: Optional[List[str]] = None


class CommentCreate(CommentBase):
    """Схема создания комментария"""
    post_id: str
    parent_id: Optional[str] = None


class CommentResponse(CommentBase):
    """Схема ответа комментария"""
    id: str
    post_id: str
    author_id: str
    parent_id: Optional[str]
    like_count: int
    reply_count: int
    created_at: datetime
    updated_at: datetime
    author: UserProfileResponse

    class Config:
        from_attributes = True


class LikeCreate(BaseModel):
    """Схема создания лайка"""
    post_id: Optional[str] = None
    comment_id: Optional[str] = None
    like_type: LikeType = LikeType.LIKE


class LikeResponse(BaseModel):
    """Схема ответа лайка"""
    id: str
    user_id: str
    post_id: Optional[str]
    comment_id: Optional[str]
    like_type: LikeType
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """Базовая схема сообщения"""
    content: str
    media_urls: Optional[List[str]] = None
    message_type: MessageType = MessageType.TEXT


class MessageCreate(MessageBase):
    """Схема создания сообщения"""
    receiver_id: str


class MessageResponse(MessageBase):
    """Схема ответа сообщения"""
    id: str
    sender_id: str
    receiver_id: str
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    sender: UserProfileResponse

    class Config:
        from_attributes = True


class LeaderboardBase(BaseModel):
    """Базовая схема лидерборда"""
    name: str
    description: Optional[str] = None
    category: str
    period: str = "all"
    max_entries: int = 100


class LeaderboardCreate(LeaderboardBase):
    """Схема создания лидерборда"""
    pass


class LeaderboardResponse(LeaderboardBase):
    """Схема ответа лидерборда"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeaderboardEntryResponse(BaseModel):
    """Схема ответа записи лидерборда"""
    id: str
    leaderboard_id: str
    user_id: str
    score: float
    rank: int
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    user: UserProfileResponse

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Схема ответа уведомления"""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: NotificationType
    related_id: Optional[str]
    related_type: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class FriendshipRequest(BaseModel):
    """Схема запроса дружбы"""
    friend_id: str


class FollowRequest(BaseModel):
    """Схема подписки"""
    following_id: str


class GroupJoinRequest(BaseModel):
    """Схема вступления в группу"""
    group_id: str


class SocialFeedResponse(BaseModel):
    """Схема ответа социальной ленты"""
    posts: List[SocialPostResponse]
    total: int
    page: int
    has_more: bool


class UserStatsResponse(BaseModel):
    """Схема статистики пользователя"""
    user_id: str
    level: int
    experience_points: int
    total_points: int
    reputation: int
    friends_count: int
    followers_count: int
    following_count: int
    posts_count: int
    comments_count: int
    likes_received: int
    achievements_count: int
    groups_count: int


class GamificationPointsResponse(BaseModel):
    """Схема ответа очков геймификации"""
    user_id: str
    total_points: int
    level: int
    experience_points: int
    points_to_next_level: int
    recent_earnings: List[Dict[str, Any]]
    achievements_unlocked: List[UserAchievementResponse]


