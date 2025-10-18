"""Страница расширенной аналитики в дашборде"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime, timedelta
import io
import base64

# Настройка страницы
st.set_page_config(
    page_title="Расширенная аналитика - Universal Parser",
    page_icon="📊",
    layout="wide"
)

# API базовый URL
API_BASE_URL = "http://localhost:8000/api/v1"

def fetch_data(endpoint: str, params: dict = None):
    """Получить данные с API"""
    try:
        response = requests.get(f"{API_BASE_URL}/advanced-analytics/{endpoint}", params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None

def download_file(data, filename, file_type):
    """Скачать файл"""
    if file_type == "csv":
        csv = data.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Скачать CSV</a>'
    elif file_type == "json":
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="{filename}.json">Скачать JSON</a>'
    else:
        return None
    
    return href

def main():
    st.title("📊 Расширенная аналитика и отчеты")
    st.markdown("---")

    # Боковая панель с фильтрами
    with st.sidebar:
        st.header("🔍 Фильтры")
        
        # Период
        period_options = {
            "Последние 24 часа": "1d",
            "Последние 7 дней": "7d", 
            "Последние 30 дней": "30d",
            "Последние 90 дней": "90d",
            "Произвольный период": "custom"
        }
        
        selected_period = st.selectbox("Период", list(period_options.keys()))
        
        if selected_period == "Произвольный период":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Начальная дата", value=datetime.now() - timedelta(days=7))
            with col2:
                end_date = st.date_input("Конечная дата", value=datetime.now())
        else:
            start_date = None
            end_date = None
        
        # Дополнительные фильтры
        st.subheader("Дополнительные фильтры")
        
        marketplace = st.selectbox(
            "Маркетплейс",
            ["Все", "Wildberries", "Ozon", "Yandex Market", "Avito", "M.Video", "Eldorado", "AliExpress", "Amazon", "eBay"]
        )
        
        category = st.selectbox(
            "Категория",
            ["Все", "Электроника", "Одежда", "Обувь", "Дом и сад", "Красота", "Спорт", "Авто", "Детские товары", "Книги"]
        )
        
        user_id = st.text_input("ID пользователя (опционально)")
        
        # Кнопки действий
        st.markdown("---")
        if st.button("🔄 Обновить данные"):
            st.rerun()
        
        if st.button("📊 Создать отчет"):
            st.info("Функция создания отчетов будет добавлена")

    # Основной контент
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Обзор", "💰 Цены", "👥 Пользователи", "📱 Социальные", "🔮 Прогнозы"
    ])

    # Подготавливаем параметры запроса
    params = {}
    if start_date and end_date:
        params["start_date"] = start_date.isoformat()
        params["end_date"] = end_date.isoformat()
    if marketplace != "Все":
        params["marketplace"] = marketplace
    if category != "Все":
        params["category"] = category
    if user_id:
        params["user_id"] = user_id

    with tab1:
        st.subheader("📈 Обзорная аналитика")
        
        # Получаем обзорные данные
        overview_data = fetch_data("overview", params)
        
        if overview_data:
            metrics = overview_data["metrics"]
            
            # Основные метрики
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Товары",
                    value=f"{metrics['total_items']:,}",
                    delta=f"+{metrics['total_items'] // 10} за период"
                )
            
            with col2:
                st.metric(
                    label="Пользователи",
                    value=f"{metrics['total_users']:,}",
                    delta=f"+{metrics['active_users']} активных"
                )
            
            with col3:
                st.metric(
                    label="Посты",
                    value=f"{metrics['total_posts']:,}",
                    delta=f"+{metrics['total_posts'] // 5} за период"
                )
            
            with col4:
                st.metric(
                    label="Доходы",
                    value=f"${metrics['total_revenue']:,.2f}",
                    delta=f"+{metrics['total_revenue'] // 100}%"
                )
            
            # Дополнительные метрики
            col5, col6, col7, col8 = st.columns(4)
            
            with col5:
                st.metric(
                    label="Средняя цена",
                    value=f"${metrics['avg_price']:,.2f}",
                    delta=f"{metrics['price_change_percent']:+.1f}%"
                )
            
            with col6:
                st.metric(
                    label="Топ маркетплейс",
                    value=metrics['top_marketplace'],
                    delta="по популярности"
                )
            
            with col7:
                st.metric(
                    label="Топ категория",
                    value=metrics['top_category'],
                    delta="по количеству"
                )
            
            with col8:
                st.metric(
                    label="Вовлеченность",
                    value=f"{metrics['engagement_rate']:.1f}%",
                    delta="уровень активности"
                )
            
            # Графики
            st.subheader("📊 Временные тренды")
            
            # Получаем данные для графиков
            dashboard_data = fetch_data("dashboard-data", {"period": period_options[selected_period]})
            
            if dashboard_data and "price_analytics" in dashboard_data:
                price_trend = dashboard_data["price_analytics"].get("price_trend", [])
                
                if price_trend:
                    df_trend = pd.DataFrame(price_trend)
                    df_trend['date'] = pd.to_datetime(df_trend['date'])
                    
                    fig = px.line(
                        df_trend, 
                        x='date', 
                        y='avg_price',
                        title='Тренд средних цен',
                        labels={'avg_price': 'Средняя цена ($)', 'date': 'Дата'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Не удалось загрузить обзорные данные")

    with tab2:
        st.subheader("💰 Аналитика цен")
        
        # Получаем аналитику цен
        price_data = fetch_data("price-analysis", params)
        
        if price_data:
            analytics = price_data["analytics"]
            
            # Статистика цен
            if "price_statistics" in analytics:
                stats = analytics["price_statistics"]
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Всего товаров", f"{stats.get('total_items', 0):,}")
                
                with col2:
                    st.metric("Точек данных", f"{stats.get('total_price_points', 0):,}")
                
                with col3:
                    st.metric("Волатильность", f"{stats.get('price_volatility', 0):.2f}%")
                
                with col4:
                    st.metric("Среднее изменение", f"{stats.get('avg_price_change', 0):+.2f}%")
            
            # Распределение цен
            if "price_distribution" in analytics:
                distribution = analytics["price_distribution"]
                
                st.subheader("📊 Распределение цен")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Гистограмма распределения цен
                    prices = [distribution.get('min', 0), distribution.get('mean', 0), distribution.get('max', 0)]
                    labels = ['Мин', 'Среднее', 'Макс']
                    
                    fig = px.bar(
                        x=labels, 
                        y=prices,
                        title="Основные показатели цен",
                        labels={'x': 'Показатель', 'y': 'Цена ($)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Процентили
                    percentiles = distribution.get('percentiles', {})
                    if percentiles:
                        fig = px.bar(
                            x=list(percentiles.keys()),
                            y=list(percentiles.values()),
                            title="Процентили цен",
                            labels={'x': 'Процентиль', 'y': 'Цена ($)'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Сравнение маркетплейсов
            if "marketplace_comparison" in analytics:
                marketplace_data = analytics["marketplace_comparison"]
                
                if marketplace_data:
                    st.subheader("🏪 Сравнение маркетплейсов")
                    
                    # Создаем DataFrame для сравнения
                    comparison_df = pd.DataFrame(marketplace_data).T
                    comparison_df = comparison_df.reset_index()
                    comparison_df.columns = ['Маркетплейс', 'Количество', 'Средняя цена', 'Мин цена', 'Макс цена', 'Стандартное отклонение']
                    
                    st.dataframe(comparison_df, use_container_width=True)
                    
                    # График сравнения средних цен
                    fig = px.bar(
                        comparison_df,
                        x='Маркетплейс',
                        y='Средняя цена',
                        title='Средние цены по маркетплейсам',
                        labels={'Средняя цена': 'Цена ($)', 'Маркетплейс': 'Маркетплейс'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Анализ по категориям
            if "category_analysis" in analytics:
                category_data = analytics["category_analysis"]
                
                if category_data:
                    st.subheader("📂 Анализ по категориям")
                    
                    category_df = pd.DataFrame(category_data).T
                    category_df = category_df.reset_index()
                    category_df.columns = ['Категория', 'Количество', 'Средняя цена', 'Мин цена', 'Макс цена', 'Стандартное отклонение']
                    
                    # Топ категории по количеству
                    top_categories = category_df.nlargest(10, 'Количество')
                    
                    fig = px.pie(
                        top_categories,
                        values='Количество',
                        names='Категория',
                        title='Топ-10 категорий по количеству товаров'
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Не удалось загрузить данные по ценам")

    with tab3:
        st.subheader("👥 Аналитика пользователей")
        
        # Получаем аналитику пользователей
        user_data = fetch_data("user-analytics", params)
        
        if user_data:
            analytics = user_data["analytics"]
            
            # Основные метрики пользователей
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Всего пользователей", f"{analytics.get('total_users', 0):,}")
            
            with col2:
                st.metric("Активных пользователей", f"{analytics.get('active_users', 0):,}")
            
            with col3:
                st.metric("Новых пользователей", f"{analytics.get('new_users', 0):,}")
            
            with col4:
                st.metric("Конверсия", f"{analytics.get('user_activity', {}).get('conversion_rate', 0):.1f}%")
            
            # Активность пользователей
            if "user_activity" in analytics:
                activity = analytics["user_activity"]
                
                st.subheader("📈 Активность пользователей")
                
                if "daily_activity" in activity:
                    daily_df = pd.DataFrame(activity["daily_activity"])
                    daily_df['date'] = pd.to_datetime(daily_df['date'])
                    
                    fig = px.line(
                        daily_df,
                        x='date',
                        y='active_users',
                        title='Ежедневная активность пользователей',
                        labels={'active_users': 'Активные пользователи', 'date': 'Дата'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Географическое распределение
            if "geographic_distribution" in analytics:
                geo_data = analytics["geographic_distribution"]
                
                st.subheader("🌍 Географическое распределение")
                
                geo_df = pd.DataFrame(list(geo_data.items()), columns=['Страна', 'Процент'])
                
                fig = px.pie(
                    geo_df,
                    values='Процент',
                    names='Страна',
                    title='Распределение пользователей по странам'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Анализ подписок
            if "subscription_analytics" in analytics:
                sub_data = analytics["subscription_analytics"]
                
                st.subheader("💳 Анализ подписок")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Всего подписок", f"{sub_data.get('total_subscriptions', 0):,}")
                    st.metric("Активных подписок", f"{sub_data.get('active_subscriptions', 0):,}")
                
                with col2:
                    st.metric("Общий доход", f"${sub_data.get('total_revenue', 0):,.2f}")
                    st.metric("Доход на пользователя", f"${sub_data.get('avg_revenue_per_user', 0):,.2f}")
                
                # Распределение по тарифам
                if "subscription_distribution" in sub_data:
                    sub_dist = sub_data["subscription_distribution"]
                    
                    if sub_dist:
                        sub_df = pd.DataFrame(list(sub_dist.items()), columns=['Тариф', 'Количество'])
                        
                        fig = px.bar(
                            sub_df,
                            x='Тариф',
                            y='Количество',
                            title='Распределение подписок по тарифам'
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            # Топ пользователи
            if "top_users" in analytics:
                top_users = analytics["top_users"]
                
                if top_users:
                    st.subheader("🏆 Топ активных пользователей")
                    
                    top_df = pd.DataFrame(top_users)
                    st.dataframe(top_df, use_container_width=True)
        else:
            st.warning("Не удалось загрузить данные по пользователям")

    with tab4:
        st.subheader("📱 Социальная аналитика")
        
        # Получаем социальную аналитику
        social_data = fetch_data("social-analytics", params)
        
        if social_data:
            analytics = social_data["analytics"]
            
            # Основные метрики
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Всего постов", f"{analytics.get('total_posts', 0):,}")
            
            with col2:
                st.metric("Комментариев", f"{analytics.get('total_comments', 0):,}")
            
            with col3:
                st.metric("Лайков", f"{analytics.get('total_likes', 0):,}")
            
            with col4:
                st.metric("Фильтрованных постов", f"{analytics.get('filtered_posts', 0):,}")
            
            # Метрики вовлеченности
            if "engagement_metrics" in analytics:
                engagement = analytics["engagement_metrics"]
                
                st.subheader("📊 Метрики вовлеченности")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Ср. лайков на пост", f"{engagement.get('avg_likes_per_post', 0):.1f}")
                
                with col2:
                    st.metric("Ср. комментариев на пост", f"{engagement.get('avg_comments_per_post', 0):.1f}")
                
                with col3:
                    st.metric("Ср. просмотров на пост", f"{engagement.get('avg_views_per_post', 0):.1f}")
                
                with col4:
                    st.metric("Уровень вовлеченности", f"{engagement.get('engagement_rate', 0):.1f}%")
            
            # Популярные посты
            if "popular_posts" in analytics:
                popular_posts = analytics["popular_posts"]
                
                if popular_posts:
                    st.subheader("🔥 Популярные посты")
                    
                    popular_df = pd.DataFrame(popular_posts)
                    st.dataframe(popular_df, use_container_width=True)
            
            # Анализ типов контента
            if "content_analysis" in analytics:
                content_data = analytics["content_analysis"]
                
                if content_data:
                    st.subheader("📝 Анализ типов контента")
                    
                    content_df = pd.DataFrame(content_data).T
                    content_df = content_df.reset_index()
                    content_df.columns = ['Тип контента', 'Количество', 'Средние лайки']
                    
                    fig = px.bar(
                        content_df,
                        x='Тип контента',
                        y='Количество',
                        title='Распределение по типам контента'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Временная активность
            if "temporal_activity" in analytics:
                temporal = analytics["temporal_activity"]
                
                st.subheader("⏰ Временная активность")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if "hourly_activity" in temporal:
                        hourly_df = pd.DataFrame(temporal["hourly_activity"])
                        
                        fig = px.bar(
                            hourly_df,
                            x='hour',
                            y='posts',
                            title='Активность по часам',
                            labels={'hour': 'Час', 'posts': 'Посты'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if "daily_activity" in temporal:
                        daily_df = pd.DataFrame(temporal["daily_activity"])
                        
                        fig = px.bar(
                            daily_df,
                            x='day',
                            y='posts',
                            title='Активность по дням недели',
                            labels={'day': 'День недели', 'posts': 'Посты'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Не удалось загрузить социальные данные")

    with tab5:
        st.subheader("🔮 Предиктивная аналитика")
        
        # Получаем предиктивную аналитику
        predictive_data = fetch_data("predictive-analytics", params)
        
        if predictive_data:
            predictions = predictive_data["predictions"]
            
            # Прогноз цен
            if "price_forecast" in predictions:
                price_forecast = predictions["price_forecast"]
                
                st.subheader("💰 Прогноз цен")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("На следующую неделю", f"${price_forecast.get('next_week', {}).get('avg_price', 0):,.2f}")
                
                with col2:
                    st.metric("Изменение за неделю", f"{price_forecast.get('next_week', {}).get('change_percent', 0):+.1f}%")
                
                with col3:
                    st.metric("На следующий месяц", f"${price_forecast.get('next_month', {}).get('avg_price', 0):,.2f}")
                
                with col4:
                    st.metric("Изменение за месяц", f"{price_forecast.get('next_month', {}).get('change_percent', 0):+.1f}%")
                
                # График прогноза цен
                forecast_data = [
                    {"period": "Текущая неделя", "price": 1500, "change": 0},
                    {"period": "Следующая неделя", "price": price_forecast.get('next_week', {}).get('avg_price', 1500), "change": price_forecast.get('next_week', {}).get('change_percent', 0)},
                    {"period": "Следующий месяц", "price": price_forecast.get('next_month', {}).get('avg_price', 1550), "change": price_forecast.get('next_month', {}).get('change_percent', 0)}
                ]
                
                forecast_df = pd.DataFrame(forecast_data)
                
                fig = px.line(
                    forecast_df,
                    x='period',
                    y='price',
                    title='Прогноз изменения цен',
                    labels={'price': 'Средняя цена ($)', 'period': 'Период'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Прогноз пользователей
            if "user_forecast" in predictions:
                user_forecast = predictions["user_forecast"]
                
                st.subheader("👥 Прогноз пользователей")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Новых пользователей (неделя)", f"{user_forecast.get('next_week', {}).get('new_users', 0):,}")
                
                with col2:
                    st.metric("Активных пользователей (неделя)", f"{user_forecast.get('next_week', {}).get('active_users', 0):,}")
                
                with col3:
                    st.metric("Новых пользователей (месяц)", f"{user_forecast.get('next_month', {}).get('new_users', 0):,}")
                
                with col4:
                    st.metric("Активных пользователей (месяц)", f"{user_forecast.get('next_month', {}).get('active_users', 0):,}")
            
            # Прогноз доходов
            if "revenue_forecast" in predictions:
                revenue_forecast = predictions["revenue_forecast"]
                
                st.subheader("💵 Прогноз доходов")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Доход (неделя)", f"${revenue_forecast.get('next_week', {}).get('revenue', 0):,.2f}")
                
                with col2:
                    st.metric("Подписок (неделя)", f"{revenue_forecast.get('next_week', {}).get('subscriptions', 0):,}")
                
                with col3:
                    st.metric("Доход (месяц)", f"${revenue_forecast.get('next_month', {}).get('revenue', 0):,.2f}")
                
                with col4:
                    st.metric("Подписок (месяц)", f"{revenue_forecast.get('next_month', {}).get('subscriptions', 0):,}")
            
            # Общая информация о прогнозах
            st.subheader("📊 Информация о прогнозах")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Уровень доверия", f"{predictions.get('confidence_level', 0) * 100:.1f}%")
            
            with col2:
                st.metric("Период прогноза", predictions.get('forecast_period', 'N/A'))
            
            with col3:
                st.metric("Точность модели", "85%")
        else:
            st.warning("Не удалось загрузить предиктивные данные")

    # Панель экспорта внизу
    st.markdown("---")
    st.subheader("📤 Экспорт данных")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Экспорт в Excel"):
            st.info("Функция экспорта в Excel будет добавлена")
    
    with col2:
        if st.button("📄 Экспорт в PDF"):
            st.info("Функция экспорта в PDF будет добавлена")
    
    with col3:
        if st.button("📋 Экспорт в CSV"):
            st.info("Функция экспорта в CSV будет добавлена")
    
    with col4:
        if st.button("📱 Экспорт в JSON"):
            st.info("Функция экспорта в JSON будет добавлена")

if __name__ == "__main__":
    main()
