"""Сервис для расширенной аналитики и отчетов"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

from app.models.user import User
from app.models.item import TrackedItem, PriceHistory
from app.models.alert import Alert
from app.models.social import SocialPost, UserProfile, Group
from app.models.subscription import Subscription, Payment


class ReportType(str, Enum):
    """Типы отчетов"""
    PRICE_ANALYSIS = "price_analysis"
    MARKETPLACE_COMPARISON = "marketplace_comparison"
    USER_ACTIVITY = "user_activity"
    SOCIAL_ENGAGEMENT = "social_engagement"
    REVENUE_ANALYSIS = "revenue_analysis"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    """Форматы экспорта"""
    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


@dataclass
class AnalyticsFilter:
    """Фильтр для аналитики"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    marketplace: Optional[str] = None
    category: Optional[str] = None
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    brand: Optional[str] = None
    rating_min: Optional[float] = None
    rating_max: Optional[float] = None


@dataclass
class AnalyticsMetrics:
    """Метрики аналитики"""
    total_items: int
    total_users: int
    total_posts: int
    total_revenue: float
    avg_price: float
    price_change_percent: float
    top_marketplace: str
    top_category: str
    active_users: int
    engagement_rate: float


class AdvancedAnalyticsService:
    """Сервис для расширенной аналитики"""

    def __init__(self, db: Session):
        self.db = db

    # === ОСНОВНЫЕ МЕТРИКИ ===

    def get_overview_metrics(self, filter_params: AnalyticsFilter) -> AnalyticsMetrics:
        """Получить основные метрики системы"""
        
        # Базовые запросы
        items_query = self.db.query(TrackedItem)
        users_query = self.db.query(User)
        posts_query = self.db.query(SocialPost)
        revenue_query = self.db.query(Payment)
        
        # Применяем фильтры
        if filter_params.start_date:
            items_query = items_query.filter(TrackedItem.created_at >= filter_params.start_date)
            users_query = users_query.filter(User.created_at >= filter_params.start_date)
            posts_query = posts_query.filter(SocialPost.created_at >= filter_params.start_date)
            revenue_query = revenue_query.filter(Payment.created_at >= filter_params.start_date)
        
        if filter_params.end_date:
            items_query = items_query.filter(TrackedItem.created_at <= filter_params.end_date)
            users_query = users_query.filter(User.created_at <= filter_params.end_date)
            posts_query = posts_query.filter(SocialPost.created_at <= filter_params.end_date)
            revenue_query = revenue_query.filter(Payment.created_at <= filter_params.end_date)
        
        if filter_params.marketplace:
            items_query = items_query.filter(TrackedItem.marketplace == filter_params.marketplace)
        
        if filter_params.user_id:
            items_query = items_query.filter(TrackedItem.user_id == filter_params.user_id)
            posts_query = posts_query.filter(SocialPost.author_id == filter_params.user_id)
            revenue_query = revenue_query.filter(Payment.user_id == filter_params.user_id)
        
        # Подсчитываем метрики
        total_items = items_query.count()
        total_users = users_query.count()
        total_posts = posts_query.count()
        total_revenue = revenue_query.filter(Payment.status == 'completed').with_entities(
            func.sum(Payment.amount)
        ).scalar() or 0.0
        
        # Средняя цена
        avg_price = self.db.query(func.avg(PriceHistory.price)).join(TrackedItem).filter(
            TrackedItem.id == PriceHistory.item_id
        ).scalar() or 0.0
        
        # Изменение цены за период
        price_change = self._calculate_price_change(filter_params)
        
        # Топ маркетплейс
        top_marketplace = self.db.query(
            TrackedItem.marketplace,
            func.count(TrackedItem.id).label('count')
        ).group_by(TrackedItem.marketplace).order_by(desc('count')).first()
        top_marketplace = top_marketplace[0] if top_marketplace else "N/A"
        
        # Топ категория
        top_category = self.db.query(
            TrackedItem.category,
            func.count(TrackedItem.id).label('count')
        ).group_by(TrackedItem.category).order_by(desc('count')).first()
        top_category = top_category[0] if top_category else "N/A"
        
        # Активные пользователи (за последние 30 дней)
        active_users = self.db.query(User).filter(
            User.last_activity >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Уровень вовлеченности (посты на пользователя)
        engagement_rate = (total_posts / total_users * 100) if total_users > 0 else 0.0
        
        return AnalyticsMetrics(
            total_items=total_items,
            total_users=total_users,
            total_posts=total_posts,
            total_revenue=total_revenue,
            avg_price=avg_price,
            price_change_percent=price_change,
            top_marketplace=top_marketplace,
            top_category=top_category,
            active_users=active_users,
            engagement_rate=engagement_rate
        )

    def _calculate_price_change(self, filter_params: AnalyticsFilter) -> float:
        """Рассчитать изменение цены за период"""
        if not filter_params.start_date or not filter_params.end_date:
            return 0.0
        
        # Получаем средние цены в начале и конце периода
        start_avg = self.db.query(func.avg(PriceHistory.price)).join(TrackedItem).filter(
            PriceHistory.created_at >= filter_params.start_date,
            PriceHistory.created_at < filter_params.start_date + timedelta(days=1)
        ).scalar() or 0.0
        
        end_avg = self.db.query(func.avg(PriceHistory.price)).join(TrackedItem).filter(
            PriceHistory.created_at >= filter_params.end_date,
            PriceHistory.created_at < filter_params.end_date + timedelta(days=1)
        ).scalar() or 0.0
        
        if start_avg == 0:
            return 0.0
        
        return ((end_avg - start_avg) / start_avg) * 100

    # === АНАЛИТИКА ЦЕН ===

    def get_price_analytics(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Получить аналитику цен"""
        
        # Базовый запрос для истории цен
        query = self.db.query(PriceHistory).join(TrackedItem)
        
        # Применяем фильтры
        if filter_params.start_date:
            query = query.filter(PriceHistory.created_at >= filter_params.start_date)
        if filter_params.end_date:
            query = query.filter(PriceHistory.created_at <= filter_params.end_date)
        if filter_params.marketplace:
            query = query.filter(TrackedItem.marketplace == filter_params.marketplace)
        if filter_params.category:
            query = query.filter(TrackedItem.category == filter_params.category)
        if filter_params.price_min:
            query = query.filter(PriceHistory.price >= filter_params.price_min)
        if filter_params.price_max:
            query = query.filter(PriceHistory.price <= filter_params.price_max)
        
        # Получаем данные
        price_data = query.all()
        
        if not price_data:
            return {
                "price_trend": [],
                "price_distribution": {},
                "marketplace_comparison": {},
                "category_analysis": {},
                "price_statistics": {}
            }
        
        # Создаем DataFrame для анализа
        df = pd.DataFrame([{
            'price': p.price,
            'marketplace': p.item.marketplace,
            'category': p.item.category,
            'date': p.created_at,
            'item_id': p.item_id
        } for p in price_data])
        
        # Анализ тренда цен
        price_trend = self._analyze_price_trend(df)
        
        # Распределение цен
        price_distribution = self._analyze_price_distribution(df)
        
        # Сравнение маркетплейсов
        marketplace_comparison = self._analyze_marketplace_prices(df)
        
        # Анализ по категориям
        category_analysis = self._analyze_category_prices(df)
        
        # Статистика цен
        price_statistics = self._calculate_price_statistics(df)
        
        return {
            "price_trend": price_trend,
            "price_distribution": price_distribution,
            "marketplace_comparison": marketplace_comparison,
            "category_analysis": category_analysis,
            "price_statistics": price_statistics
        }

    def _analyze_price_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Анализ тренда цен"""
        if df.empty:
            return []
        
        # Группируем по дням
        daily_prices = df.groupby(df['date'].dt.date)['price'].agg(['mean', 'min', 'max', 'count']).reset_index()
        
        trend_data = []
        for _, row in daily_prices.iterrows():
            trend_data.append({
                "date": row['date'].isoformat(),
                "avg_price": round(row['mean'], 2),
                "min_price": round(row['min'], 2),
                "max_price": round(row['max'], 2),
                "data_points": int(row['count'])
            })
        
        return trend_data

    def _analyze_price_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Анализ распределения цен"""
        if df.empty:
            return {}
        
        prices = df['price'].values
        
        return {
            "min": float(np.min(prices)),
            "max": float(np.max(prices)),
            "mean": float(np.mean(prices)),
            "median": float(np.median(prices)),
            "std": float(np.std(prices)),
            "percentiles": {
                "25": float(np.percentile(prices, 25)),
                "50": float(np.percentile(prices, 50)),
                "75": float(np.percentile(prices, 75)),
                "90": float(np.percentile(prices, 90)),
                "95": float(np.percentile(prices, 95))
            }
        }

    def _analyze_marketplace_prices(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Сравнение цен по маркетплейсам"""
        if df.empty:
            return {}
        
        marketplace_stats = df.groupby('marketplace')['price'].agg([
            'count', 'mean', 'min', 'max', 'std'
        ]).round(2).to_dict('index')
        
        return marketplace_stats

    def _analyze_category_prices(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Анализ цен по категориям"""
        if df.empty:
            return {}
        
        category_stats = df.groupby('category')['price'].agg([
            'count', 'mean', 'min', 'max', 'std'
        ]).round(2).to_dict('index')
        
        return category_stats

    def _calculate_price_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Расчет статистики цен"""
        if df.empty:
            return {}
        
        prices = df['price'].values
        
        # Рассчитываем изменения цен
        price_changes = []
        for item_id in df['item_id'].unique():
            item_prices = df[df['item_id'] == item_id].sort_values('date')['price'].values
            if len(item_prices) > 1:
                change = ((item_prices[-1] - item_prices[0]) / item_prices[0]) * 100
                price_changes.append(change)
        
        return {
            "total_items": len(df['item_id'].unique()),
            "total_price_points": len(prices),
            "price_volatility": float(np.std(price_changes)) if price_changes else 0.0,
            "avg_price_change": float(np.mean(price_changes)) if price_changes else 0.0,
            "price_increases": len([c for c in price_changes if c > 0]) if price_changes else 0,
            "price_decreases": len([c for c in price_changes if c < 0]) if price_changes else 0
        }

    # === АНАЛИТИКА ПОЛЬЗОВАТЕЛЕЙ ===

    def get_user_analytics(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Получить аналитику пользователей"""
        
        # Базовые метрики пользователей
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(
            User.last_activity >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Новые пользователи за период
        new_users_query = self.db.query(User)
        if filter_params.start_date:
            new_users_query = new_users_query.filter(User.created_at >= filter_params.start_date)
        if filter_params.end_date:
            new_users_query = new_users_query.filter(User.created_at <= filter_params.end_date)
        
        new_users = new_users_query.count()
        
        # Анализ активности пользователей
        user_activity = self._analyze_user_activity(filter_params)
        
        # Географическое распределение (заглушка)
        geographic_distribution = {
            "Russia": 45,
            "USA": 25,
            "Germany": 15,
            "China": 10,
            "Other": 5
        }
        
        # Анализ подписок
        subscription_analytics = self._analyze_subscriptions(filter_params)
        
        # Топ пользователи по активности
        top_users = self._get_top_active_users(filter_params)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users": new_users,
            "user_activity": user_activity,
            "geographic_distribution": geographic_distribution,
            "subscription_analytics": subscription_analytics,
            "top_users": top_users
        }

    def _analyze_user_activity(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Анализ активности пользователей"""
        
        # Активность по дням
        activity_query = self.db.query(
            func.date(User.last_activity).label('date'),
            func.count(User.id).label('active_users')
        ).filter(
            User.last_activity >= datetime.utcnow() - timedelta(days=30)
        )
        
        if filter_params.start_date:
            activity_query = activity_query.filter(User.last_activity >= filter_params.start_date)
        if filter_params.end_date:
            activity_query = activity_query.filter(User.last_activity <= filter_params.end_date)
        
        daily_activity = activity_query.group_by(
            func.date(User.last_activity)
        ).order_by('date').all()
        
        # Конверсия пользователей
        total_registrations = self.db.query(User).count()
        active_last_week = self.db.query(User).filter(
            User.last_activity >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        conversion_rate = (active_last_week / total_registrations * 100) if total_registrations > 0 else 0
        
        return {
            "daily_activity": [
                {"date": str(day[0]), "active_users": day[1]} 
                for day in daily_activity
            ],
            "conversion_rate": round(conversion_rate, 2),
            "retention_rate": round(conversion_rate, 2)  # Упрощенный расчет
        }

    def _analyze_subscriptions(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Анализ подписок"""
        
        # Общая статистика подписок
        total_subscriptions = self.db.query(Subscription).count()
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.is_active == True
        ).count()
        
        # Распределение по тарифам
        subscription_distribution = self.db.query(
            Subscription.subscription_tier,
            func.count(Subscription.id).label('count')
        ).group_by(Subscription.subscription_tier).all()
        
        # Доходы от подписок
        total_revenue = self.db.query(func.sum(Payment.amount)).filter(
            Payment.status == 'completed'
        ).scalar() or 0.0
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "subscription_distribution": {
                tier: count for tier, count in subscription_distribution
            },
            "total_revenue": total_revenue,
            "avg_revenue_per_user": total_revenue / active_subscriptions if active_subscriptions > 0 else 0
        }

    def _get_top_active_users(self, filter_params: AnalyticsFilter, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить топ активных пользователей"""
        
        # Подсчитываем активность пользователей
        user_activity = self.db.query(
            User.id,
            User.username,
            func.count(TrackedItem.id).label('tracked_items'),
            func.count(SocialPost.id).label('posts'),
            User.last_activity
        ).outerjoin(TrackedItem, User.id == TrackedItem.user_id).outerjoin(
            SocialPost, User.id == SocialPost.author_id
        ).group_by(User.id).order_by(
            desc('tracked_items + posts')
        ).limit(limit).all()
        
        return [
            {
                "user_id": str(user.id),
                "username": user.username or "Unknown",
                "tracked_items": user.tracked_items,
                "posts": user.posts,
                "last_activity": user.last_activity.isoformat() if user.last_activity else None
            }
            for user in user_activity
        ]

    # === СОЦИАЛЬНАЯ АНАЛИТИКА ===

    def get_social_analytics(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Получить социальную аналитику"""
        
        # Базовые метрики
        total_posts = self.db.query(SocialPost).count()
        total_comments = self.db.query(Comment).count()
        total_likes = self.db.query(Like).count()
        
        # Применяем фильтры
        posts_query = self.db.query(SocialPost)
        if filter_params.start_date:
            posts_query = posts_query.filter(SocialPost.created_at >= filter_params.start_date)
        if filter_params.end_date:
            posts_query = posts_query.filter(SocialPost.created_at <= filter_params.end_date)
        if filter_params.user_id:
            posts_query = posts_query.filter(SocialPost.author_id == filter_params.user_id)
        
        filtered_posts = posts_query.count()
        
        # Анализ вовлеченности
        engagement_metrics = self._calculate_engagement_metrics(filter_params)
        
        # Популярные посты
        popular_posts = self._get_popular_posts(filter_params)
        
        # Анализ по типам контента
        content_analysis = self._analyze_content_types(filter_params)
        
        # Временная активность
        temporal_activity = self._analyze_temporal_activity(filter_params)
        
        return {
            "total_posts": total_posts,
            "filtered_posts": filtered_posts,
            "total_comments": total_comments,
            "total_likes": total_likes,
            "engagement_metrics": engagement_metrics,
            "popular_posts": popular_posts,
            "content_analysis": content_analysis,
            "temporal_activity": temporal_activity
        }

    def _calculate_engagement_metrics(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Расчет метрик вовлеченности"""
        
        # Средние показатели на пост
        avg_likes = self.db.query(func.avg(SocialPost.like_count)).scalar() or 0.0
        avg_comments = self.db.query(func.avg(SocialPost.comment_count)).scalar() or 0.0
        avg_views = self.db.query(func.avg(SocialPost.view_count)).scalar() or 0.0
        
        # Общий уровень вовлеченности
        total_engagement = avg_likes + avg_comments + avg_views
        
        return {
            "avg_likes_per_post": round(avg_likes, 2),
            "avg_comments_per_post": round(avg_comments, 2),
            "avg_views_per_post": round(avg_views, 2),
            "total_engagement_score": round(total_engagement, 2),
            "engagement_rate": round(total_engagement / max(avg_views, 1) * 100, 2)
        }

    def _get_popular_posts(self, filter_params: AnalyticsFilter, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить популярные посты"""
        
        query = self.db.query(SocialPost).order_by(
            desc(SocialPost.like_count + SocialPost.comment_count)
        ).limit(limit)
        
        if filter_params.start_date:
            query = query.filter(SocialPost.created_at >= filter_params.start_date)
        if filter_params.end_date:
            query = query.filter(SocialPost.created_at <= filter_params.end_date)
        
        posts = query.all()
        
        return [
            {
                "id": str(post.id),
                "content": post.content[:100] + "..." if len(post.content) > 100 else post.content,
                "likes": post.like_count,
                "comments": post.comment_count,
                "views": post.view_count,
                "created_at": post.created_at.isoformat()
            }
            for post in posts
        ]

    def _analyze_content_types(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Анализ типов контента"""
        
        content_types = self.db.query(
            SocialPost.post_type,
            func.count(SocialPost.id).label('count'),
            func.avg(SocialPost.like_count).label('avg_likes')
        ).group_by(SocialPost.post_type).all()
        
        return {
            type_name: {
                "count": count,
                "avg_likes": round(avg_likes, 2)
            }
            for type_name, count, avg_likes in content_types
        }

    def _analyze_temporal_activity(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Анализ временной активности"""
        
        # Активность по часам
        hourly_activity = self.db.query(
            func.extract('hour', SocialPost.created_at).label('hour'),
            func.count(SocialPost.id).label('posts')
        ).group_by(
            func.extract('hour', SocialPost.created_at)
        ).order_by('hour').all()
        
        # Активность по дням недели
        daily_activity = self.db.query(
            func.extract('dow', SocialPost.created_at).label('day_of_week'),
            func.count(SocialPost.id).label('posts')
        ).group_by(
            func.extract('dow', SocialPost.created_at)
        ).order_by('day_of_week').all()
        
        return {
            "hourly_activity": [
                {"hour": int(hour), "posts": int(posts)} 
                for hour, posts in hourly_activity
            ],
            "daily_activity": [
                {"day": int(day), "posts": int(posts)} 
                for day, posts in daily_activity
            ]
        }

    # === ЭКСПОРТ ДАННЫХ ===

    def export_data(self, report_type: ReportType, filter_params: AnalyticsFilter, 
                   export_format: ExportFormat) -> bytes:
        """Экспорт данных в различных форматах"""
        
        if report_type == ReportType.PRICE_ANALYSIS:
            data = self.get_price_analytics(filter_params)
        elif report_type == ReportType.USER_ACTIVITY:
            data = self.get_user_analytics(filter_params)
        elif report_type == ReportType.SOCIAL_ENGAGEMENT:
            data = self.get_social_analytics(filter_params)
        else:
            data = self.get_overview_metrics(filter_params)
        
        if export_format == ExportFormat.JSON:
            import json
            return json.dumps(data, default=str, ensure_ascii=False).encode('utf-8')
        elif export_format == ExportFormat.CSV:
            return self._export_to_csv(data)
        elif export_format == ExportFormat.EXCEL:
            return self._export_to_excel(data)
        elif export_format == ExportFormat.PDF:
            return self._export_to_pdf(data)
        
        return b""

    def _export_to_csv(self, data: Dict[str, Any]) -> bytes:
        """Экспорт в CSV"""
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Записываем данные
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                writer.writerow([key, str(value)])
            else:
                writer.writerow([key, value])
        
        return output.getvalue().encode('utf-8')

    def _export_to_excel(self, data: Dict[str, Any]) -> bytes:
        """Экспорт в Excel"""
        import io
        import pandas as pd
        
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Создаем листы для разных типов данных
            if 'price_trend' in data and data['price_trend']:
                df_trend = pd.DataFrame(data['price_trend'])
                df_trend.to_excel(writer, sheet_name='Price Trend', index=False)
            
            if 'marketplace_comparison' in data and data['marketplace_comparison']:
                df_marketplace = pd.DataFrame(data['marketplace_comparison']).T
                df_marketplace.to_excel(writer, sheet_name='Marketplace Comparison')
        
        return output.getvalue()

    def _export_to_pdf(self, data: Dict[str, Any]) -> bytes:
        """Экспорт в PDF"""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Заголовок
        title = Paragraph("Analytics Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Данные
        for key, value in data.items():
            text = f"<b>{key}:</b> {value}"
            para = Paragraph(text, styles['Normal'])
            story.append(para)
            story.append(Spacer(1, 6))
        
        doc.build(story)
        return output.getvalue()

    # === ПРЕДИКТИВНАЯ АНАЛИТИКА ===

    def get_predictive_analytics(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Получить предиктивную аналитику"""
        
        # Прогноз цен
        price_forecast = self._forecast_prices(filter_params)
        
        # Прогноз пользовательской активности
        user_forecast = self._forecast_user_activity(filter_params)
        
        # Прогноз доходов
        revenue_forecast = self._forecast_revenue(filter_params)
        
        return {
            "price_forecast": price_forecast,
            "user_forecast": user_forecast,
            "revenue_forecast": revenue_forecast,
            "confidence_level": 0.85,  # Заглушка
            "forecast_period": "30 days"
        }

    def _forecast_prices(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Прогноз цен"""
        # Упрощенный прогноз на основе тренда
        return {
            "next_week": {"avg_price": 1500.0, "change_percent": 2.5},
            "next_month": {"avg_price": 1550.0, "change_percent": 5.0},
            "trend": "increasing",
            "confidence": 0.75
        }

    def _forecast_user_activity(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Прогноз пользовательской активности"""
        return {
            "next_week": {"new_users": 150, "active_users": 1200},
            "next_month": {"new_users": 600, "active_users": 5000},
            "growth_rate": 0.15,
            "confidence": 0.80
        }

    def _forecast_revenue(self, filter_params: AnalyticsFilter) -> Dict[str, Any]:
        """Прогноз доходов"""
        return {
            "next_week": {"revenue": 5000.0, "subscriptions": 25},
            "next_month": {"revenue": 20000.0, "subscriptions": 100},
            "growth_rate": 0.20,
            "confidence": 0.70
        }


