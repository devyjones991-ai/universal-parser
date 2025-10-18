"""
Intelligent notification engine for smart alerts and user engagement
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib

from app.core.cache import cache_service, cached
from app.services.trend_detector import TrendDetectorService, TrendAlert
from app.services.dynamic_pricing import DynamicPricingService

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    PRICE_DROP = "price_drop"
    PRICE_SPIKE = "price_spike"
    STOCK_ALERT = "stock_alert"
    NICHE_OPPORTUNITY = "niche_opportunity"
    TREND_ALERT = "trend_alert"
    COMPETITOR_UPDATE = "competitor_update"
    ACHIEVEMENT = "achievement"
    SYSTEM_UPDATE = "system_update"


class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"
    TELEGRAM = "telegram"


@dataclass
class NotificationTemplate:
    """Template for generating notifications"""
    template_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title_template: str
    body_template: str
    action_template: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


@dataclass
class SmartNotification:
    """Intelligent notification with ML-based prioritization"""
    notification_id: str
    user_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    body: str
    action_url: Optional[str] = None
    channels: List[NotificationChannel] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    importance_score: float = 0.5
    engagement_prediction: float = 0.5
    created_at: datetime = None
    data: Dict[str, Any] = None


@dataclass
class UserPreferences:
    """User notification preferences"""
    user_id: str
    enabled_types: List[NotificationType]
    enabled_channels: List[NotificationChannel]
    quiet_hours_start: int = 22  # 10 PM
    quiet_hours_end: int = 8     # 8 AM
    max_notifications_per_day: int = 10
    priority_threshold: float = 0.5
    batch_notifications: bool = True
    digest_frequency: str = "daily"  # daily, weekly, never


class NotificationEngineService:
    """Service for intelligent notification management"""
    
    def __init__(self):
        self.trend_service = TrendDetectorService()
        self.pricing_service = DynamicPricingService()
        
        # ML models
        self.importance_classifier = None
        self.engagement_predictor = None
        self.scaler = StandardScaler()
        
        # Notification templates
        self.templates = self._initialize_templates()
        
        # User preferences cache
        self.user_preferences = {}
        
        # Notification queue
        self.notification_queue = []
        
        # Engagement tracking
        self.engagement_history = {}
        
    def _initialize_templates(self) -> Dict[str, NotificationTemplate]:
        """Initialize notification templates"""
        templates = {}
        
        # Price drop template
        templates["price_drop"] = NotificationTemplate(
            template_id="price_drop",
            notification_type=NotificationType.PRICE_DROP,
            priority=NotificationPriority.HIGH,
            title_template="💰 Price Drop Alert: {item_name}",
            body_template="The price of {item_name} dropped by {price_change}% to {new_price} {currency}",
            action_template="View Details",
            icon="💰",
            color="#4CAF50"
        )
        
        # Price spike template
        templates["price_spike"] = NotificationTemplate(
            template_id="price_spike",
            notification_type=NotificationType.PRICE_SPIKE,
            priority=NotificationPriority.MEDIUM,
            title_template="📈 Price Spike: {item_name}",
            body_template="The price of {item_name} increased by {price_change}% to {new_price} {currency}",
            action_template="Check Competitors",
            icon="📈",
            color="#FF9800"
        )
        
        # Stock alert template
        templates["stock_alert"] = NotificationTemplate(
            template_id="stock_alert",
            notification_type=NotificationType.STOCK_ALERT,
            priority=NotificationPriority.HIGH,
            title_template="⚠️ Stock Alert: {item_name}",
            body_template="Only {stock_count} units left of {item_name} at {marketplace}",
            action_template="Buy Now",
            icon="⚠️",
            color="#F44336"
        )
        
        # Niche opportunity template
        templates["niche_opportunity"] = NotificationTemplate(
            template_id="niche_opportunity",
            notification_type=NotificationType.NICHE_OPPORTUNITY,
            priority=NotificationPriority.MEDIUM,
            title_template="🎯 New Opportunity: {niche_name}",
            body_template="High-potential niche discovered with {opportunity_score}% opportunity score",
            action_template="Explore Niche",
            icon="🎯",
            color="#9C27B0"
        )
        
        # Trend alert template
        templates["trend_alert"] = NotificationTemplate(
            template_id="trend_alert",
            notification_type=NotificationType.TREND_ALERT,
            priority=NotificationPriority.MEDIUM,
            title_template="📊 Trend Alert: {trend_type}",
            body_template="{trend_description} affecting {affected_items} items",
            action_template="View Analysis",
            icon="📊",
            color="#2196F3"
        )
        
        # Achievement template
        templates["achievement"] = NotificationTemplate(
            template_id="achievement",
            notification_type=NotificationType.ACHIEVEMENT,
            priority=NotificationPriority.LOW,
            title_template="🏆 Achievement Unlocked: {achievement_name}",
            body_template="Congratulations! You've earned the {achievement_name} badge",
            action_template="View Profile",
            icon="🏆",
            color="#FFD700"
        )
        
        return templates
    
    async def send_smart_notification(self, 
                                    user_id: str,
                                    notification_type: str,
                                    data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a smart notification to a user"""
        try:
            logger.info(f"Sending smart notification to user {user_id}: {notification_type}")
            
            # Get user preferences
            preferences = await self.get_user_preferences(user_id)
            
            # Check if notification type is enabled
            if NotificationType(notification_type) not in preferences.enabled_types:
                return {"sent": False, "message": "Notification type disabled by user"}
            
            # Generate notification content
            notification = await self._generate_smart_notification(
                user_id, notification_type, data or {}
            )
            
            if not notification:
                return {"sent": False, "message": "Failed to generate notification"}
            
            # Apply smart prioritization
            notification = await self._apply_smart_prioritization(notification, user_id)
            
            # Check if notification should be sent based on preferences
            if not await self._should_send_notification(notification, preferences):
                return {"sent": False, "message": "Notification filtered by preferences"}
            
            # Schedule notification
            await self._schedule_notification(notification, preferences)
            
            return {"sent": True, "message": "Notification scheduled successfully"}
            
        except Exception as e:
            logger.error(f"Error sending smart notification: {e}")
            return {"sent": False, "message": f"Error: {str(e)}"}
    
    async def _generate_smart_notification(self, 
                                         user_id: str,
                                         notification_type: str,
                                         data: Dict[str, Any]) -> Optional[SmartNotification]:
        """Generate a smart notification with personalized content"""
        try:
            notification_type_enum = NotificationType(notification_type)
            template = self.templates.get(notification_type_enum.value)
            
            if not template:
                logger.warning(f"No template found for notification type: {notification_type}")
                return None
            
            # Generate personalized content
            title, body, action_url = await self._generate_personalized_content(
                template, data, user_id
            )
            
            # Determine priority
            priority = await self._calculate_notification_priority(
                notification_type_enum, data, user_id
            )
            
            # Determine channels
            channels = await self._determine_notification_channels(
                notification_type_enum, priority, user_id
            )
            
            # Calculate importance and engagement scores
            importance_score = await self._calculate_importance_score(
                notification_type_enum, data, user_id
            )
            engagement_prediction = await self._predict_engagement(
                notification_type_enum, data, user_id
            )
            
            # Create notification
            notification = SmartNotification(
                notification_id=f"{user_id}_{notification_type}_{datetime.now().timestamp()}",
                user_id=user_id,
                notification_type=notification_type_enum,
                priority=priority,
                title=title,
                body=body,
                action_url=action_url,
                channels=channels,
                importance_score=importance_score,
                engagement_prediction=engagement_prediction,
                created_at=datetime.now(),
                data=data
            )
            
            return notification
            
        except Exception as e:
            logger.error(f"Error generating smart notification: {e}")
            return None
    
    async def _generate_personalized_content(self, 
                                           template: NotificationTemplate,
                                           data: Dict[str, Any],
                                           user_id: str) -> Tuple[str, str, Optional[str]]:
        """Generate personalized notification content"""
        try:
            # Get user context for personalization
            user_context = await self._get_user_context(user_id)
            
            # Merge data with user context
            content_data = {**data, **user_context}
            
            # Format templates
            title = template.title_template.format(**content_data)
            body = template.body_template.format(**content_data)
            action_url = template.action_template.format(**content_data) if template.action_template else None
            
            return title, body, action_url
            
        except Exception as e:
            logger.error(f"Error generating personalized content: {e}")
            # Fallback to basic formatting
            title = template.title_template.format(**data)
            body = template.body_template.format(**data)
            action_url = template.action_template.format(**data) if template.action_template else None
            return title, body, action_url
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context for personalization"""
        try:
            # In a real implementation, this would query user data
            # For now, return mock context
            return {
                "user_name": f"User_{user_id}",
                "currency": "RUB",
                "timezone": "Europe/Moscow",
                "language": "ru"
            }
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {}
    
    async def _calculate_notification_priority(self, 
                                             notification_type: NotificationType,
                                             data: Dict[str, Any],
                                             user_id: str) -> NotificationPriority:
        """Calculate notification priority using ML"""
        try:
            # Extract features for priority calculation
            features = self._extract_priority_features(notification_type, data, user_id)
            
            # If we have a trained model, use it
            if self.importance_classifier:
                features_scaled = self.scaler.transform([features])
                priority_proba = self.importance_classifier.predict_proba(features_scaled)[0]
                
                # Map probabilities to priority levels
                if priority_proba[3] > 0.7:  # Critical
                    return NotificationPriority.CRITICAL
                elif priority_proba[2] > 0.6:  # High
                    return NotificationPriority.HIGH
                elif priority_proba[1] > 0.5:  # Medium
                    return NotificationPriority.MEDIUM
                else:
                    return NotificationPriority.LOW
            
            # Fallback to rule-based priority
            return self._rule_based_priority(notification_type, data)
            
        except Exception as e:
            logger.error(f"Error calculating notification priority: {e}")
            return NotificationPriority.MEDIUM
    
    def _extract_priority_features(self, 
                                 notification_type: NotificationType,
                                 data: Dict[str, Any],
                                 user_id: str) -> List[float]:
        """Extract features for priority calculation"""
        features = []
        
        # Notification type features
        type_features = [0] * len(NotificationType)
        type_features[list(NotificationType).index(notification_type)] = 1
        features.extend(type_features)
        
        # Data-based features
        features.extend([
            data.get("price_change_percent", 0),
            data.get("opportunity_score", 0),
            data.get("impact_score", 0),
            data.get("confidence", 0),
            data.get("urgency", 0)
        ])
        
        # User engagement features
        user_engagement = self.engagement_history.get(user_id, {})
        features.extend([
            user_engagement.get("avg_click_rate", 0.5),
            user_engagement.get("avg_open_rate", 0.5),
            user_engagement.get("recent_activity", 0.5)
        ])
        
        # Time-based features
        now = datetime.now()
        features.extend([
            now.hour / 24,  # Hour of day (0-1)
            now.weekday() / 7,  # Day of week (0-1)
            1 if 9 <= now.hour <= 17 else 0,  # Business hours
        ])
        
        return features
    
    def _rule_based_priority(self, 
                           notification_type: NotificationType,
                           data: Dict[str, Any]) -> NotificationPriority:
        """Calculate priority using rules"""
        # Base priority by type
        type_priorities = {
            NotificationType.PRICE_DROP: NotificationPriority.HIGH,
            NotificationType.STOCK_ALERT: NotificationPriority.HIGH,
            NotificationType.PRICE_SPIKE: NotificationPriority.MEDIUM,
            NotificationType.NICHE_OPPORTUNITY: NotificationPriority.MEDIUM,
            NotificationType.TREND_ALERT: NotificationPriority.MEDIUM,
            NotificationType.COMPETITOR_UPDATE: NotificationPriority.LOW,
            NotificationType.ACHIEVEMENT: NotificationPriority.LOW,
            NotificationType.SYSTEM_UPDATE: NotificationPriority.LOW
        }
        
        base_priority = type_priorities.get(notification_type, NotificationPriority.MEDIUM)
        
        # Adjust based on data
        if notification_type == NotificationType.PRICE_DROP:
            price_change = abs(data.get("price_change_percent", 0))
            if price_change > 20:
                return NotificationPriority.CRITICAL
            elif price_change > 10:
                return NotificationPriority.HIGH
        
        elif notification_type == NotificationType.STOCK_ALERT:
            stock_count = data.get("stock_count", 0)
            if stock_count < 5:
                return NotificationPriority.CRITICAL
            elif stock_count < 10:
                return NotificationPriority.HIGH
        
        elif notification_type == NotificationType.NICHE_OPPORTUNITY:
            opportunity_score = data.get("opportunity_score", 0)
            if opportunity_score > 0.8:
                return NotificationPriority.HIGH
            elif opportunity_score > 0.6:
                return NotificationPriority.MEDIUM
        
        return base_priority
    
    async def _determine_notification_channels(self, 
                                             notification_type: NotificationType,
                                             priority: NotificationPriority,
                                             user_id: str) -> List[NotificationChannel]:
        """Determine which channels to use for notification"""
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(user_id)
            enabled_channels = preferences.enabled_channels
            
            # Filter by priority
            channels = []
            
            if priority == NotificationPriority.CRITICAL:
                # Use all available channels for critical notifications
                channels = enabled_channels
            elif priority == NotificationPriority.HIGH:
                # Use push and in-app for high priority
                channels = [ch for ch in enabled_channels if ch in [NotificationChannel.PUSH, NotificationChannel.IN_APP]]
            else:
                # Use in-app only for medium/low priority
                channels = [ch for ch in enabled_channels if ch == NotificationChannel.IN_APP]
            
            # Add email for certain types
            if notification_type in [NotificationType.SYSTEM_UPDATE, NotificationType.ACHIEVEMENT]:
                if NotificationChannel.EMAIL in enabled_channels:
                    channels.append(NotificationChannel.EMAIL)
            
            return channels if channels else [NotificationChannel.IN_APP]
            
        except Exception as e:
            logger.error(f"Error determining notification channels: {e}")
            return [NotificationChannel.IN_APP]
    
    async def _calculate_importance_score(self, 
                                        notification_type: NotificationType,
                                        data: Dict[str, Any],
                                        user_id: str) -> float:
        """Calculate importance score for notification"""
        try:
            # Base importance by type
            type_importance = {
                NotificationType.PRICE_DROP: 0.8,
                NotificationType.STOCK_ALERT: 0.9,
                NotificationType.PRICE_SPIKE: 0.6,
                NotificationType.NICHE_OPPORTUNITY: 0.7,
                NotificationType.TREND_ALERT: 0.5,
                NotificationType.COMPETITOR_UPDATE: 0.4,
                NotificationType.ACHIEVEMENT: 0.3,
                NotificationType.SYSTEM_UPDATE: 0.2
            }
            
            base_importance = type_importance.get(notification_type, 0.5)
            
            # Adjust based on data
            if "price_change_percent" in data:
                price_change = abs(data["price_change_percent"])
                base_importance += min(price_change / 100, 0.3)
            
            if "opportunity_score" in data:
                opportunity_score = data["opportunity_score"]
                base_importance += opportunity_score * 0.2
            
            if "impact_score" in data:
                impact_score = data["impact_score"]
                base_importance += impact_score * 0.2
            
            return max(0, min(1, base_importance))
            
        except Exception as e:
            logger.error(f"Error calculating importance score: {e}")
            return 0.5
    
    async def _predict_engagement(self, 
                                notification_type: NotificationType,
                                data: Dict[str, Any],
                                user_id: str) -> float:
        """Predict user engagement with notification"""
        try:
            # Get user engagement history
            user_engagement = self.engagement_history.get(user_id, {})
            
            # Base engagement by type
            type_engagement = {
                NotificationType.PRICE_DROP: 0.7,
                NotificationType.STOCK_ALERT: 0.8,
                NotificationType.PRICE_SPIKE: 0.5,
                NotificationType.NICHE_OPPORTUNITY: 0.6,
                NotificationType.TREND_ALERT: 0.4,
                NotificationType.COMPETITOR_UPDATE: 0.3,
                NotificationType.ACHIEVEMENT: 0.9,
                NotificationType.SYSTEM_UPDATE: 0.2
            }
            
            base_engagement = type_engagement.get(notification_type, 0.5)
            
            # Adjust based on user history
            if user_engagement:
                avg_engagement = user_engagement.get("avg_engagement", 0.5)
                base_engagement = (base_engagement + avg_engagement) / 2
            
            # Adjust based on data quality
            if "confidence" in data:
                confidence = data["confidence"]
                base_engagement *= confidence
            
            return max(0, min(1, base_engagement))
            
        except Exception as e:
            logger.error(f"Error predicting engagement: {e}")
            return 0.5
    
    async def _apply_smart_prioritization(self, 
                                        notification: SmartNotification,
                                        user_id: str) -> SmartNotification:
        """Apply smart prioritization to notification"""
        try:
            # Check if notification should be batched
            if await self._should_batch_notification(notification, user_id):
                notification.scheduled_for = datetime.now() + timedelta(minutes=30)
            
            # Check if notification should be delayed
            if await self._should_delay_notification(notification, user_id):
                notification.scheduled_for = datetime.now() + timedelta(hours=1)
            
            # Set expiration
            notification.expires_at = datetime.now() + timedelta(days=7)
            
            return notification
            
        except Exception as e:
            logger.error(f"Error applying smart prioritization: {e}")
            return notification
    
    async def _should_batch_notification(self, 
                                       notification: SmartNotification,
                                       user_id: str) -> bool:
        """Check if notification should be batched"""
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(user_id)
            
            # Check if batching is enabled
            if not preferences.batch_notifications:
                return False
            
            # Check notification type
            batchable_types = [
                NotificationType.PRICE_SPIKE,
                NotificationType.COMPETITOR_UPDATE,
                NotificationType.TREND_ALERT
            ]
            
            return notification.notification_type in batchable_types
            
        except Exception as e:
            logger.error(f"Error checking if notification should be batched: {e}")
            return False
    
    async def _should_delay_notification(self, 
                                       notification: SmartNotification,
                                       user_id: str) -> bool:
        """Check if notification should be delayed"""
        try:
            # Get user preferences
            preferences = await self.get_user_preferences(user_id)
            
            # Check if it's during quiet hours
            now = datetime.now()
            current_hour = now.hour
            
            if preferences.quiet_hours_start <= preferences.quiet_hours_end:
                # Same day quiet hours
                if preferences.quiet_hours_start <= current_hour < preferences.quiet_hours_end:
                    return True
            else:
                # Overnight quiet hours
                if current_hour >= preferences.quiet_hours_start or current_hour < preferences.quiet_hours_end:
                    return True
            
            # Check if user has reached daily limit
            daily_count = await self._get_daily_notification_count(user_id)
            if daily_count >= preferences.max_notifications_per_day:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if notification should be delayed: {e}")
            return False
    
    async def _should_send_notification(self, 
                                      notification: SmartNotification,
                                      preferences: UserPreferences) -> bool:
        """Check if notification should be sent based on preferences"""
        try:
            # Check if notification type is enabled
            if notification.notification_type not in preferences.enabled_types:
                return False
            
            # Check priority threshold
            if notification.importance_score < preferences.priority_threshold:
                return False
            
            # Check daily limit
            daily_count = await self._get_daily_notification_count(notification.user_id)
            if daily_count >= preferences.max_notifications_per_day:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if notification should be sent: {e}")
            return True
    
    async def _schedule_notification(self, 
                                   notification: SmartNotification,
                                   preferences: UserPreferences):
        """Schedule notification for delivery"""
        try:
            # Add to queue
            self.notification_queue.append(notification)
            
            # In a real implementation, this would:
            # 1. Store in database
            # 2. Schedule with a task queue (Celery, RQ, etc.)
            # 3. Send to appropriate channels
            
            logger.info(f"Notification scheduled for user {notification.user_id}")
            
        except Exception as e:
            logger.error(f"Error scheduling notification: {e}")
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user notification preferences"""
        try:
            # Check cache first
            if user_id in self.user_preferences:
                return self.user_preferences[user_id]
            
            # In a real implementation, this would query the database
            # For now, return default preferences
            preferences = UserPreferences(
                user_id=user_id,
                enabled_types=list(NotificationType),
                enabled_channels=[
                    NotificationChannel.PUSH,
                    NotificationChannel.IN_APP,
                    NotificationChannel.EMAIL
                ],
                quiet_hours_start=22,
                quiet_hours_end=8,
                max_notifications_per_day=10,
                priority_threshold=0.5,
                batch_notifications=True,
                digest_frequency="daily"
            )
            
            # Cache preferences
            self.user_preferences[user_id] = preferences
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            # Return default preferences
            return UserPreferences(
                user_id=user_id,
                enabled_types=list(NotificationType),
                enabled_channels=[NotificationChannel.IN_APP],
                quiet_hours_start=22,
                quiet_hours_end=8,
                max_notifications_per_day=5,
                priority_threshold=0.7,
                batch_notifications=False,
                digest_frequency="never"
            )
    
    async def update_user_preferences(self, 
                                    user_id: str,
                                    preferences: UserPreferences):
        """Update user notification preferences"""
        try:
            # Update cache
            self.user_preferences[user_id] = preferences
            
            # In a real implementation, this would update the database
            logger.info(f"Updated preferences for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
    
    async def _get_daily_notification_count(self, user_id: str) -> int:
        """Get daily notification count for user"""
        try:
            # In a real implementation, this would query the database
            # For now, return mock count
            return len([n for n in self.notification_queue if n.user_id == user_id])
            
        except Exception as e:
            logger.error(f"Error getting daily notification count: {e}")
            return 0
    
    async def track_engagement(self, 
                             notification_id: str,
                             action: str,
                             user_id: str):
        """Track user engagement with notification"""
        try:
            # Update engagement history
            if user_id not in self.engagement_history:
                self.engagement_history[user_id] = {
                    "total_notifications": 0,
                    "total_opens": 0,
                    "total_clicks": 0,
                    "avg_engagement": 0.5
                }
            
            user_engagement = self.engagement_history[user_id]
            user_engagement["total_notifications"] += 1
            
            if action == "open":
                user_engagement["total_opens"] += 1
            elif action == "click":
                user_engagement["total_clicks"] += 1
            
            # Calculate average engagement
            total_actions = user_engagement["total_opens"] + user_engagement["total_clicks"]
            user_engagement["avg_engagement"] = total_actions / user_engagement["total_notifications"]
            
            logger.info(f"Tracked engagement for notification {notification_id}: {action}")
            
        except Exception as e:
            logger.error(f"Error tracking engagement: {e}")
    
    async def get_notification_history(self, 
                                     user_id: str,
                                     limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history for user"""
        try:
            # Filter notifications for user
            user_notifications = [
                n for n in self.notification_queue 
                if n.user_id == user_id
            ]
            
            # Sort by creation date
            user_notifications.sort(key=lambda x: x.created_at, reverse=True)
            
            # Convert to dict format
            history = []
            for notification in user_notifications[:limit]:
                history.append({
                    "notification_id": notification.notification_id,
                    "type": notification.notification_type.value,
                    "priority": notification.priority.value,
                    "title": notification.title,
                    "body": notification.body,
                    "created_at": notification.created_at.isoformat(),
                    "importance_score": notification.importance_score,
                    "engagement_prediction": notification.engagement_prediction
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return []
    
    async def train_models(self, training_data: Optional[List[Dict[str, Any]]] = None):
        """Train ML models for notification optimization"""
        try:
            logger.info("Training notification models...")
            
            if not training_data:
                training_data = await self._generate_training_data()
            
            # Prepare features and targets
            X = []
            y_importance = []
            y_engagement = []
            
            for data in training_data:
                features = self._extract_priority_features(
                    NotificationType(data["notification_type"]),
                    data["data"],
                    data["user_id"]
                )
                X.append(features)
                y_importance.append(data["importance_label"])
                y_engagement.append(data["engagement_score"])
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train importance classifier
            self.importance_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.importance_classifier.fit(X_scaled, y_importance)
            
            # Train engagement predictor
            self.engagement_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
            self.engagement_predictor.fit(X_scaled, y_engagement)
            
            logger.info("Notification models trained successfully")
            
        except Exception as e:
            logger.error(f"Error training notification models: {e}")
    
    async def _generate_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for notification models"""
        training_data = []
        
        # Generate mock training data
        for _ in range(1000):
            notification_type = np.random.choice(list(NotificationType))
            user_id = f"user_{np.random.randint(1, 100)}"
            
            # Generate mock data
            data = {
                "price_change_percent": np.random.uniform(-50, 50),
                "opportunity_score": np.random.uniform(0, 1),
                "impact_score": np.random.uniform(0, 1),
                "confidence": np.random.uniform(0, 1),
                "urgency": np.random.uniform(0, 1)
            }
            
            # Generate labels
            importance_label = np.random.choice([0, 1, 2, 3])  # Low, Medium, High, Critical
            engagement_score = np.random.uniform(0, 1)
            
            training_data.append({
                "notification_type": notification_type.value,
                "user_id": user_id,
                "data": data,
                "importance_label": importance_label,
                "engagement_score": engagement_score
            })
        
        return training_data
