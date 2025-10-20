"""API эндпоинты для социальных функций и геймификации"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.social_service import SocialService
from app.schemas.social import (
    UserProfileResponse, UserProfileCreate, UserProfileUpdate,
    GroupResponse, GroupCreate, GroupUpdate, GroupJoinRequest,
    SocialPostResponse, SocialPostCreate, SocialPostUpdate,
    CommentResponse, CommentCreate, MessageResponse, MessageCreate,
    LikeCreate, LikeResponse, LeaderboardResponse, LeaderboardCreate,
    LeaderboardEntryResponse, NotificationResponse, SocialFeedResponse,
    UserStatsResponse, GamificationPointsResponse, FriendshipRequest,
    FollowRequest, AchievementResponse, UserAchievementResponse
)

router = APIRouter()

# === ПРОФИЛИ ПОЛЬЗОВАТЕЛЕЙ ===

@router.post("/profiles", response_model=UserProfileResponse)
async def create_user_profile(
    profile_data: UserProfileCreate,
    db: Session = Depends(get_db)
):
    """Создать профиль пользователя"""
    service = SocialService(db)
    profile = service.create_user_profile(profile_data)
    return profile

@router.get("/profiles/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str, db: Session = Depends(get_db)):
    """Получить профиль пользователя"""
    service = SocialService(db)
    profile = service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile

@router.put("/profiles/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: str,
    update_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """Обновить профиль пользователя"""
    service = SocialService(db)
    profile = service.update_user_profile(user_id, update_data)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile

@router.get("/profiles/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(user_id: str, db: Session = Depends(get_db)):
    """Получить статистику пользователя"""
    service = SocialService(db)
    stats = service.get_user_stats(user_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return stats

# === ГРУППЫ ===

@router.post("/groups", response_model=GroupResponse)
async def create_group(
    group_data: GroupCreate,
    owner_id: str = Query(..., description="ID владельца группы"),
    db: Session = Depends(get_db)
):
    """Создать группу"""
    service = SocialService(db)
    group = service.create_group(group_data, owner_id)
    return group

@router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str, db: Session = Depends(get_db)):
    """Получить группу"""
    service = SocialService(db)
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    return group

@router.post("/groups/{group_id}/join")
async def join_group(
    group_id: str,
    join_request: GroupJoinRequest,
    db: Session = Depends(get_db)
):
    """Вступить в группу"""
    service = SocialService(db)
    success = service.join_group(group_id, join_request.group_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to join group"
        )
    return {"message": "Successfully joined group"}

@router.delete("/groups/{group_id}/leave")
async def leave_group(
    group_id: str,
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Покинуть группу"""
    service = SocialService(db)
    success = service.leave_group(group_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to leave group"
        )
    return {"message": "Successfully left group"}

# === СОЦИАЛЬНЫЕ ПОСТЫ ===

@router.post("/posts", response_model=SocialPostResponse)
async def create_post(
    post_data: SocialPostCreate,
    author_id: str = Query(..., description="ID автора поста"),
    db: Session = Depends(get_db)
):
    """Создать социальный пост"""
    service = SocialService(db)
    try:
        post = service.create_post(post_data, author_id)
        return post
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/feed", response_model=SocialFeedResponse)
async def get_social_feed(
    user_id: str = Query(..., description="ID пользователя"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(20, ge=1, le=100, description="Количество постов"),
    db: Session = Depends(get_db)
):
    """Получить социальную ленту пользователя"""
    service = SocialService(db)
    posts = service.get_social_feed(user_id, page, limit)

    return SocialFeedResponse(
        posts=posts,
        total=len(posts),
        page=page,
        has_more=len(posts) == limit
    )

@router.get("/posts/{post_id}", response_model=SocialPostResponse)
async def get_post(post_id: str, db: Session = Depends(get_db)):
    """Получить пост по ID"""
    service = SocialService(db)
    post = service.db.query(service.db.query(SocialPost).filter(SocialPost.id == post_id).first())
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

@router.put("/posts/{post_id}", response_model=SocialPostResponse)
async def update_post(
    post_id: str,
    update_data: SocialPostUpdate,
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Обновить пост"""
    service = SocialService(db)
    post = service.db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Проверяем права доступа
    if post.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(post, field, value)

    post.updated_at = datetime.utcnow()
    service.db.commit()
    service.db.refresh(post)
    return post

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Удалить пост"""
    service = SocialService(db)
    post = service.db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )

    # Проверяем права доступа
    if post.author_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )

    service.db.delete(post)
    service.db.commit()
    return {"message": "Post deleted successfully"}

# === КОММЕНТАРИИ ===

@router.post("/comments", response_model=CommentResponse)
async def create_comment(
    comment_data: CommentCreate,
    author_id: str = Query(..., description="ID автора комментария"),
    db: Session = Depends(get_db)
):
    """Создать комментарий"""
    service = SocialService(db)
    try:
        comment = service.create_comment(comment_data, author_id)
        return comment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: str,
    page: int = Query(1, ge=1, description="Номер страницы"),
    limit: int = Query(50, ge=1, le=100, description="Количество комментариев"),
    db: Session = Depends(get_db)
):
    """Получить комментарии к посту"""
    service = SocialService(db)
    comments = service.db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_id.is_(None)  # Только корневые комментарии
    ).order_by(Comment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return comments

# === ЛАЙКИ ===

@router.post("/likes", response_model=LikeResponse)
async def toggle_like(
    like_data: LikeCreate,
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Переключить лайк"""
    service = SocialService(db)
    success = service.toggle_like(like_data, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to toggle like"
        )

    # Возвращаем информацию о лайке
    if like_data.post_id:
        like = service.db.query(Like).filter(
            Like.user_id == user_id,
            Like.post_id == like_data.post_id
        ).first()
    else:
        like = service.db.query(Like).filter(
            Like.user_id == user_id,
            Like.comment_id == like_data.comment_id
        ).first()

    return like

# === ЛИДЕРБОРДЫ ===

@router.post("/leaderboards", response_model=LeaderboardResponse)
async def create_leaderboard(
    leaderboard_data: LeaderboardCreate,
    db: Session = Depends(get_db)
):
    """Создать лидерборд"""
    service = SocialService(db)
    leaderboard = service.create_leaderboard(leaderboard_data)
    return leaderboard

@router.get("/leaderboards/{leaderboard_id}", response_model=List[LeaderboardEntryResponse])
async def get_leaderboard(
    leaderboard_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Количество записей"),
    db: Session = Depends(get_db)
):
    """Получить лидерборд"""
    service = SocialService(db)
    entries = service.get_leaderboard(leaderboard_id, limit)
    return entries

@router.post("/leaderboards/{leaderboard_id}/update")
async def update_leaderboard_score(
    leaderboard_id: str,
    user_id: str = Query(..., description="ID пользователя"),
    score: float = Query(..., description="Очки"),
    metadata: dict = Query(None, description="Дополнительные данные"),
    db: Session = Depends(get_db)
):
    """Обновить очки в лидерборде"""
    service = SocialService(db)
    success = service.update_leaderboard(leaderboard_id, user_id, score, metadata)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update leaderboard"
        )
    return {"message": "Leaderboard updated successfully"}

# === УВЕДОМЛЕНИЯ ===

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str = Query(..., description="ID пользователя"),
    limit: int = Query(50, ge=1, le=100, description="Количество уведомлений"),
    db: Session = Depends(get_db)
):
    """Получить уведомления пользователя"""
    service = SocialService(db)
    notifications = service.get_user_notifications(user_id, limit)
    return notifications

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Отметить уведомление как прочитанное"""
    service = SocialService(db)
    success = service.mark_notification_read(notification_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return {"message": "Notification marked as read"}

# === ДРУЗЬЯ И ПОДПИСКИ ===

@router.post("/friends/request")
async def send_friend_request(
    request_data: FriendshipRequest,
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Отправить запрос в друзья"""
    service = SocialService(db)
    # Здесь должна быть логика отправки запроса в друзья
    return {"message": "Friend request sent"}

@router.post("/follow")
async def follow_user(
    request_data: FollowRequest,
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Подписаться на пользователя"""
    service = SocialService(db)
    # Здесь должна быть логика подписки на пользователя
    return {"message": "Successfully followed user"}

# === ГЕЙМИФИКАЦИЯ ===

@router.get("/gamification/points", response_model=GamificationPointsResponse)
async def get_gamification_points(
    user_id: str = Query(..., description="ID пользователя"),
    db: Session = Depends(get_db)
):
    """Получить очки геймификации пользователя"""
    service = SocialService(db)
    profile = service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    # Рассчитываем очки до следующего уровня
    required_exp = profile.level * 1000
    points_to_next_level = max(0, required_exp - profile.experience_points)

    # Получаем недавние достижения
    recent_achievements = service.db.query(UserAchievement).filter(
        UserAchievement.user_id == profile.id,
        UserAchievement.is_completed == True
    ).order_by(UserAchievement.completed_at.desc()).limit(5).all()

    return GamificationPointsResponse(
        user_id=user_id,
        total_points=profile.total_points,
        level=profile.level,
        experience_points=profile.experience_points,
        points_to_next_level=points_to_next_level,
        recent_earnings=[],  # Заглушка
        achievements_unlocked=recent_achievements
    )

@router.get("/achievements", response_model=List[AchievementResponse])
async def get_achievements(
    category: Optional[str] = Query(None, description="Категория достижений"),
    db: Session = Depends(get_db)
):
    """Получить список достижений"""
    service = SocialService(db)
    query = service.db.query(Achievement).filter(Achievement.is_active == True)

    if category:
        query = query.filter(Achievement.category == category)

    achievements = query.all()
    return achievements

@router.get("/users/{user_id}/achievements", response_model=List[UserAchievementResponse])
async def get_user_achievements(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Получить достижения пользователя"""
    service = SocialService(db)
    profile = service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    achievements = service.db.query(UserAchievement).filter(
        UserAchievement.user_id == profile.id
    ).all()

    return achievements
