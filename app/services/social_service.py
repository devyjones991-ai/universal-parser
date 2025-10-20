"""Сервис для социальных функций"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text

from app.models.social import (
    UserProfile, Group, Achievement, UserAchievement, SocialPost, 
    Comment, Like, Message, Leaderboard, LeaderboardEntry, Notification,
    friendship, follows, group_members
)
from app.schemas.social import (
    UserProfileCreate, UserProfileUpdate, GroupCreate, GroupUpdate,
    SocialPostCreate, SocialPostUpdate, CommentCreate, MessageCreate,
    LikeCreate, LeaderboardCreate, FriendshipRequest, FollowRequest,
    GroupJoinRequest
)


class SocialService:
    """Сервис для социальных функций"""

    def __init__(self, db: Session):
        self.db = db

    # === ПРОФИЛИ ПОЛЬЗОВАТЕЛЕЙ ===

    def create_user_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """Создать профиль пользователя"""
        profile = UserProfile(
            user_id=profile_data.user_id,
            display_name=profile_data.display_name,
            bio=profile_data.bio,
            avatar_url=profile_data.avatar_url,
            cover_url=profile_data.cover_url,
            location=profile_data.location,
            website=profile_data.website,
            is_public=profile_data.is_public,
            show_email=profile_data.show_email,
            show_phone=profile_data.show_phone,
            allow_friend_requests=profile_data.allow_friend_requests,
            allow_messages=profile_data.allow_messages
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Получить профиль пользователя"""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def update_user_profile(self, user_id: str, update_data: UserProfileUpdate) -> Optional[UserProfile]:
        """Обновить профиль пользователя"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return None

        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(profile, field, value)

        profile.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return {}

        # Подсчитываем статистику
        friends_count = self.db.query(friendship).filter(
            or_(
                friendship.c.user_id == user_id,
                friendship.c.friend_id == user_id
            ),
            friendship.c.status == 'accepted'
        ).count()

        followers_count = self.db.query(follows).filter(follows.c.following_id == user_id).count()
        following_count = self.db.query(follows).filter(follows.c.follower_id == user_id).count()
        
        posts_count = self.db.query(SocialPost).filter(SocialPost.author_id == profile.id).count()
        comments_count = self.db.query(Comment).filter(Comment.author_id == profile.id).count()
        likes_received = self.db.query(Like).join(SocialPost).filter(SocialPost.author_id == profile.id).count()
        achievements_count = self.db.query(UserAchievement).filter(
            UserAchievement.user_id == profile.id,
            UserAchievement.is_completed == True
        ).count()
        groups_count = self.db.query(group_members).filter(group_members.c.user_id == user_id).count()

        return {
            "user_id": user_id,
            "level": profile.level,
            "experience_points": profile.experience_points,
            "total_points": profile.total_points,
            "reputation": profile.reputation,
            "friends_count": friends_count,
            "followers_count": followers_count,
            "following_count": following_count,
            "posts_count": posts_count,
            "comments_count": comments_count,
            "likes_received": likes_received,
            "achievements_count": achievements_count,
            "groups_count": groups_count
        }

    # === ГРУППЫ ===

    def create_group(self, group_data: GroupCreate, owner_id: str) -> Group:
        """Создать группу"""
        group = Group(
            name=group_data.name,
            description=group_data.description,
            avatar_url=group_data.avatar_url,
            cover_url=group_data.cover_url,
            is_public=group_data.is_public,
            is_private=group_data.is_private,
            requires_approval=group_data.requires_approval,
            max_members=group_data.max_members,
            owner_id=owner_id
        )
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        
        # Добавляем владельца как участника
        self.join_group(group.id, owner_id, "admin")
        
        return group

    def get_group(self, group_id: str) -> Optional[Group]:
        """Получить группу"""
        return self.db.query(Group).filter(Group.id == group_id).first()

    def join_group(self, group_id: str, user_id: str, role: str = "member") -> bool:
        """Вступить в группу"""
        group = self.get_group(group_id)
        if not group:
            return False

        # Проверяем, не является ли пользователь уже участником
        existing = self.db.query(group_members).filter(
            group_members.c.group_id == group_id,
            group_members.c.user_id == user_id
        ).first()
        
        if existing:
            return False

        # Проверяем лимит участников
        if group.max_members:
            current_count = self.db.query(group_members).filter(group_members.c.group_id == group_id).count()
            if current_count >= group.max_members:
                return False

        # Добавляем участника
        self.db.execute(
            group_members.insert().values(
                group_id=group_id,
                user_id=user_id,
                role=role
            )
        )
        
        # Обновляем счетчик участников
        group.member_count += 1
        self.db.commit()
        
        return True

    def leave_group(self, group_id: str, user_id: str) -> bool:
        """Покинуть группу"""
        result = self.db.query(group_members).filter(
            group_members.c.group_id == group_id,
            group_members.c.user_id == user_id
        ).delete()
        
        if result:
            group = self.get_group(group_id)
            if group:
                group.member_count = max(0, group.member_count - 1)
                self.db.commit()
            return True
        
        return False

    # === ДОСТИЖЕНИЯ ===

    def check_achievements(self, user_id: str, action_type: str, action_data: Dict[str, Any]) -> List[UserAchievement]:
        """Проверить и разблокировать достижения"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return []

        # Получаем активные достижения для данного типа действия
        achievements = self.db.query(Achievement).filter(
            Achievement.is_active == True,
            Achievement.category == action_type
        ).all()

        unlocked_achievements = []
        
        for achievement in achievements:
            # Проверяем, не получено ли уже это достижение
            existing = self.db.query(UserAchievement).filter(
                UserAchievement.user_id == profile.id,
                UserAchievement.achievement_id == achievement.id
            ).first()

            if existing and existing.is_completed:
                continue

            # Проверяем условия достижения
            if self._check_achievement_condition(profile, achievement, action_data):
                if existing:
                    existing.is_completed = True
                    existing.completed_at = datetime.utcnow()
                    existing.progress = achievement.condition_value
                else:
                    user_achievement = UserAchievement(
                        user_id=profile.id,
                        achievement_id=achievement.id,
                        progress=achievement.condition_value,
                        is_completed=True,
                        completed_at=datetime.utcnow()
                    )
                    self.db.add(user_achievement)
                    unlocked_achievements.append(user_achievement)

                # Начисляем очки
                profile.experience_points += achievement.points_reward
                profile.total_points += achievement.points_reward
                
                # Проверяем повышение уровня
                self._check_level_up(profile)

        self.db.commit()
        return unlocked_achievements

    def _check_achievement_condition(self, profile: UserProfile, achievement: Achievement, action_data: Dict[str, Any]) -> bool:
        """Проверить условие достижения"""
        if achievement.condition_type == "count":
            # Подсчитываем количество действий
            count = 0
            if achievement.category == "parsing":
                count = action_data.get("parsing_count", 0)
            elif achievement.category == "social":
                count = action_data.get("posts_count", 0)
            elif achievement.category == "trading":
                count = action_data.get("trades_count", 0)
            
            return count >= achievement.condition_value
        
        elif achievement.condition_type == "streak":
            # Проверяем серию
            streak = action_data.get("streak", 0)
            return streak >= achievement.condition_value
        
        elif achievement.condition_type == "value":
            # Проверяем значение
            value = action_data.get("value", 0)
            return value >= achievement.condition_value
        
        return False

    def _check_level_up(self, profile: UserProfile):
        """Проверить повышение уровня"""
        # Формула для расчета необходимого опыта: level * 1000
        required_exp = profile.level * 1000
        
        if profile.experience_points >= required_exp:
            profile.level += 1
            profile.experience_points -= required_exp

    # === СОЦИАЛЬНЫЕ ПОСТЫ ===

    def create_post(self, post_data: SocialPostCreate, author_id: str) -> SocialPost:
        """Создать социальный пост"""
        profile = self.get_user_profile(author_id)
        if not profile:
            raise ValueError("User profile not found")

        post = SocialPost(
            author_id=profile.id,
            group_id=post_data.group_id,
            content=post_data.content,
            media_urls=post_data.media_urls,
            post_type=post_data.post_type,
            item_id=post_data.item_id,
            marketplace=post_data.marketplace,
            is_public=post_data.is_public,
            allow_comments=post_data.allow_comments
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        # Проверяем достижения
        self.check_achievements(author_id, "social", {"posts_count": 1})

        return post

    def get_social_feed(self, user_id: str, page: int = 1, limit: int = 20) -> List[SocialPost]:
        """Получить социальную ленту пользователя"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return []

        # Получаем ID друзей и подписок
        friends_ids = self.db.query(friendship.c.friend_id).filter(
            friendship.c.user_id == user_id,
            friendship.c.status == 'accepted'
        ).union(
            self.db.query(friendship.c.user_id).filter(
                friendship.c.friend_id == user_id,
                friendship.c.status == 'accepted'
            )
        ).all()
        
        following_ids = self.db.query(follows.c.following_id).filter(follows.c.follower_id == user_id).all()
        
        # Объединяем ID
        user_ids = [profile.id] + [f[0] for f in friends_ids] + [f[0] for f in following_ids]

        # Получаем посты
        posts = self.db.query(SocialPost).filter(
            SocialPost.author_id.in_(user_ids),
            SocialPost.is_public == True
        ).order_by(desc(SocialPost.created_at)).offset((page - 1) * limit).limit(limit).all()

        return posts

    # === КОММЕНТАРИИ ===

    def create_comment(self, comment_data: CommentCreate, author_id: str) -> Comment:
        """Создать комментарий"""
        profile = self.get_user_profile(author_id)
        if not profile:
            raise ValueError("User profile not found")

        comment = Comment(
            post_id=comment_data.post_id,
            author_id=profile.id,
            parent_id=comment_data.parent_id,
            content=comment_data.content,
            media_urls=comment_data.media_urls
        )
        self.db.add(comment)
        
        # Обновляем счетчик комментариев
        post = self.db.query(SocialPost).filter(SocialPost.id == comment_data.post_id).first()
        if post:
            post.comment_count += 1
            if comment_data.parent_id:
                parent_comment = self.db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
                if parent_comment:
                    parent_comment.reply_count += 1

        self.db.commit()
        self.db.refresh(comment)

        # Проверяем достижения
        self.check_achievements(author_id, "social", {"comments_count": 1})

        return comment

    # === ЛАЙКИ ===

    def toggle_like(self, like_data: LikeCreate, user_id: str) -> bool:
        """Переключить лайк"""
        profile = self.get_user_profile(user_id)
        if not profile:
            return False

        # Проверяем существующий лайк
        existing_like = None
        if like_data.post_id:
            existing_like = self.db.query(Like).filter(
                Like.user_id == profile.id,
                Like.post_id == like_data.post_id
            ).first()
        elif like_data.comment_id:
            existing_like = self.db.query(Like).filter(
                Like.user_id == profile.id,
                Like.comment_id == like_data.comment_id
            ).first()

        if existing_like:
            # Убираем лайк
            self.db.delete(existing_like)
            
            # Обновляем счетчики
            if like_data.post_id:
                post = self.db.query(SocialPost).filter(SocialPost.id == like_data.post_id).first()
                if post:
                    post.like_count = max(0, post.like_count - 1)
            elif like_data.comment_id:
                comment = self.db.query(Comment).filter(Comment.id == like_data.comment_id).first()
                if comment:
                    comment.like_count = max(0, comment.like_count - 1)
            
            self.db.commit()
            return False
        else:
            # Добавляем лайк
            like = Like(
                user_id=profile.id,
                post_id=like_data.post_id,
                comment_id=like_data.comment_id,
                like_type=like_data.like_type
            )
            self.db.add(like)
            
            # Обновляем счетчики
            if like_data.post_id:
                post = self.db.query(SocialPost).filter(SocialPost.id == like_data.post_id).first()
                if post:
                    post.like_count += 1
            elif like_data.comment_id:
                comment = self.db.query(Comment).filter(Comment.id == like_data.comment_id).first()
                if comment:
                    comment.like_count += 1
            
            self.db.commit()
            return True

    # === ЛИДЕРБОРДЫ ===

    def create_leaderboard(self, leaderboard_data: LeaderboardCreate) -> Leaderboard:
        """Создать лидерборд"""
        leaderboard = Leaderboard(
            name=leaderboard_data.name,
            description=leaderboard_data.description,
            category=leaderboard_data.category,
            period=leaderboard_data.period,
            max_entries=leaderboard_data.max_entries
        )
        self.db.add(leaderboard)
        self.db.commit()
        self.db.refresh(leaderboard)
        return leaderboard

    def update_leaderboard(self, leaderboard_id: str, user_id: str, score: float, metadata: Dict[str, Any] = None) -> bool:
        """Обновить лидерборд"""
        leaderboard = self.db.query(Leaderboard).filter(Leaderboard.id == leaderboard_id).first()
        if not leaderboard:
            return False

        # Проверяем существующую запись
        existing_entry = self.db.query(LeaderboardEntry).filter(
            LeaderboardEntry.leaderboard_id == leaderboard_id,
            LeaderboardEntry.user_id == user_id
        ).first()

        if existing_entry:
            existing_entry.score = score
            existing_entry.metadata = metadata
            existing_entry.updated_at = datetime.utcnow()
        else:
            entry = LeaderboardEntry(
                leaderboard_id=leaderboard_id,
                user_id=user_id,
                score=score,
                metadata=metadata
            )
            self.db.add(entry)

        self.db.commit()
        
        # Пересчитываем ранги
        self._recalculate_leaderboard_ranks(leaderboard_id)
        
        return True

    def _recalculate_leaderboard_ranks(self, leaderboard_id: str):
        """Пересчитать ранги в лидерборде"""
        entries = self.db.query(LeaderboardEntry).filter(
            LeaderboardEntry.leaderboard_id == leaderboard_id
        ).order_by(desc(LeaderboardEntry.score)).all()

        for rank, entry in enumerate(entries, 1):
            entry.rank = rank

        self.db.commit()

    def get_leaderboard(self, leaderboard_id: str, limit: int = 100) -> List[LeaderboardEntry]:
        """Получить лидерборд"""
        return self.db.query(LeaderboardEntry).filter(
            LeaderboardEntry.leaderboard_id == leaderboard_id
        ).order_by(LeaderboardEntry.rank).limit(limit).all()

    # === УВЕДОМЛЕНИЯ ===

    def create_notification(self, user_id: str, title: str, message: str, 
                          notification_type: str, related_id: str = None, 
                          related_type: str = None) -> Notification:
        """Создать уведомление"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_id=related_id,
            related_type=related_type
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Notification]:
        """Получить уведомления пользователя"""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(desc(Notification.created_at)).limit(limit).all()

    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Отметить уведомление как прочитанное"""
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False


