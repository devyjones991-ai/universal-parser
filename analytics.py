import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import io
import json
from db import get_price_history, get_user_tracked_items, TrackedItem, PriceHistory
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Сервис аналитики и отчетов"""
    
    def __init__(self):
        # Настройка стиля графиков
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def get_price_trends(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Получить тренды цен для пользователя"""
        try:
            tracked_items = get_user_tracked_items(user_id)
            trends = {}
            
            for item in tracked_items:
                price_history = get_price_history(user_id, item.id, days)
                
                if not price_history:
                    continue
                
                # Анализируем тренд
                prices = [ph.price for ph in price_history]
                dates = [ph.timestamp for ph in price_history]
                
                if len(prices) < 2:
                    continue
                
                # Вычисляем статистики
                current_price = prices[0]
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                
                # Определяем тренд
                price_change = current_price - prices[-1] if len(prices) > 1 else 0
                price_change_percent = (price_change / prices[-1] * 100) if prices[-1] > 0 else 0
                
                trends[item.name] = {
                    "item_id": item.id,
                    "marketplace": item.marketplace,
                    "current_price": current_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "avg_price": avg_price,
                    "price_change": price_change,
                    "price_change_percent": price_change_percent,
                    "data_points": len(prices),
                    "trend": "up" if price_change > 0 else "down" if price_change < 0 else "stable"
                }
            
            return trends
            
        except Exception as e:
            logger.error(f"Ошибка получения трендов для пользователя {user_id}: {e}")
            return {}
    
    def create_price_chart(self, user_id: int, tracked_item_id: int, days: int = 30) -> bytes:
        """Создать график изменения цены"""
        try:
            price_history = get_price_history(user_id, tracked_item_id, days)
            
            if not price_history:
                return None
            
            # Подготавливаем данные
            dates = [ph.timestamp for ph in price_history]
            prices = [ph.price for ph in price_history]
            
            # Создаем график
            fig, ax = plt.subplots(figsize=(12, 6))
            
            ax.plot(dates, prices, marker='o', linewidth=2, markersize=4)
            ax.set_title(f'Динамика цены за {days} дней', fontsize=14, fontweight='bold')
            ax.set_xlabel('Дата', fontsize=12)
            ax.set_ylabel('Цена (₽)', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            # Форматируем оси
            ax.tick_params(axis='x', rotation=45)
            
            # Сохраняем в байты
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка создания графика для товара {tracked_item_id}: {e}")
            return None
    
    def generate_analytics_report(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Сгенерировать аналитический отчет"""
        try:
            trends = self.get_price_trends(user_id, days)
            tracked_items = get_user_tracked_items(user_id)
            
            # Общая статистика
            total_items = len(tracked_items)
            active_trends = len(trends)
            
            # Анализ трендов
            up_trends = sum(1 for t in trends.values() if t["trend"] == "up")
            down_trends = sum(1 for t in trends.values() if t["trend"] == "down")
            stable_trends = sum(1 for t in trends.values() if t["trend"] == "stable")
            
            # Топ изменений
            top_changes = sorted(
                trends.values(),
                key=lambda x: abs(x["price_change_percent"]),
                reverse=True
            )[:5]
            
            # Рекомендации
            recommendations = self._generate_recommendations(trends)
            
            report = {
                "period_days": days,
                "total_items": total_items,
                "active_trends": active_trends,
                "trends_summary": {
                    "up": up_trends,
                    "down": down_trends,
                    "stable": stable_trends
                },
                "top_changes": top_changes,
                "recommendations": recommendations,
                "generated_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Ошибка генерации отчета для пользователя {user_id}: {e}")
            return {}
    
    def _generate_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Генерировать рекомендации на основе трендов"""
        recommendations = []
        
        if not trends:
            return ["Добавьте товары для отслеживания, чтобы получить рекомендации"]
        
        # Анализируем тренды
        up_trends = [t for t in trends.values() if t["trend"] == "up"]
        down_trends = [t for t in trends.values() if t["trend"] == "down"]
        
        if up_trends:
            avg_increase = sum(t["price_change_percent"] for t in up_trends) / len(up_trends)
            recommendations.append(
                f"📈 {len(up_trends)} товаров растут в цене (средний рост: {avg_increase:.1f}%)"
            )
        
        if down_trends:
            avg_decrease = sum(t["price_change_percent"] for t in down_trends) / len(down_trends)
            recommendations.append(
                f"📉 {len(down_trends)} товаров падают в цене (среднее падение: {avg_decrease:.1f}%)"
            )
        
        # Рекомендации по конкретным товарам
        for name, trend in trends.items():
            if trend["price_change_percent"] > 20:
                recommendations.append(
                    f"🚨 {name}: цена выросла на {trend['price_change_percent']:.1f}% - рассмотрите покупку"
                )
            elif trend["price_change_percent"] < -20:
                recommendations.append(
                    f"💰 {name}: цена упала на {abs(trend['price_change_percent']):.1f}% - хорошее время для покупки"
                )
        
        return recommendations[:5]  # Ограничиваем количество рекомендаций
    
    def export_to_excel(self, user_id: int, days: int = 30) -> bytes:
        """Экспорт данных в Excel"""
        try:
            tracked_items = get_user_tracked_items(user_id)
            
            # Создаем Excel файл с несколькими листами
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Лист с общей информацией
                items_data = []
                for item in tracked_items:
                    price_history = get_price_history(user_id, item.id, days)
                    
                    current_price = item.current_price or 0
                    min_price = min([ph.price for ph in price_history]) if price_history else current_price
                    max_price = max([ph.price for ph in price_history]) if price_history else current_price
                    
                    items_data.append({
                        "Название": item.name,
                        "Маркетплейс": item.marketplace.upper(),
                        "Текущая цена": current_price,
                        "Мин. цена": min_price,
                        "Макс. цена": max_price,
                        "Ссылка": item.url,
                        "Последнее обновление": item.last_updated.strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                df_items = pd.DataFrame(items_data)
                df_items.to_excel(writer, sheet_name='Товары', index=False)
                
                # Лист с историей цен
                all_history = []
                for item in tracked_items:
                    price_history = get_price_history(user_id, item.id, days)
                    for ph in price_history:
                        all_history.append({
                            "Товар": item.name,
                            "Дата": ph.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "Цена": ph.price,
                            "Остаток": ph.stock or 0,
                            "Рейтинг": ph.rating or 0
                        })
                
                if all_history:
                    df_history = pd.DataFrame(all_history)
                    df_history.to_excel(writer, sheet_name='История цен', index=False)
                
                # Лист с аналитикой
                trends = self.get_price_trends(user_id, days)
                trends_data = []
                for name, trend in trends.items():
                    trends_data.append({
                        "Товар": name,
                        "Текущая цена": trend["current_price"],
                        "Изменение (%)": trend["price_change_percent"],
                        "Тренд": trend["trend"],
                        "Мин. цена": trend["min_price"],
                        "Макс. цена": trend["max_price"],
                        "Средняя цена": trend["avg_price"]
                    })
                
                if trends_data:
                    df_trends = pd.DataFrame(trends_data)
                    df_trends.to_excel(writer, sheet_name='Аналитика', index=False)
            
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в Excel для пользователя {user_id}: {e}")
            return None

# Глобальный экземпляр сервиса
analytics_service = AnalyticsService()
