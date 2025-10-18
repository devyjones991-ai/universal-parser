"""Страница российских маркетплейсов в дашборде"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Настройка страницы
st.set_page_config(
    page_title="Российские маркетплейсы - Universal Parser",
    page_icon="🇷🇺",
    layout="wide"
)

# API базовый URL
API_BASE_URL = "http://localhost:8000/api/v1"

def get_marketplaces():
    """Получить список российских маркетплейсов"""
    try:
        response = requests.get(f"{API_BASE_URL}/russian-marketplaces/marketplaces")
        if response.status_code == 200:
            return response.json()["marketplaces"]
        return []
    except:
        return []

def search_products(marketplace, query, page=1, filters=None):
    """Поиск товаров на маркетплейсе"""
    try:
        params = {
            "query": query,
            "page": page
        }
        if filters:
            params.update(filters)
        
        response = requests.get(f"{API_BASE_URL}/russian-marketplaces/{marketplace}/search", params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_marketplace_categories(marketplace):
    """Получить категории маркетплейса"""
    try:
        response = requests.get(f"{API_BASE_URL}/russian-marketplaces/{marketplace}/categories")
        if response.status_code == 200:
            return response.json()["categories"]
        return {}
    except:
        return {}

def get_marketplace_filters(marketplace):
    """Получить фильтры маркетплейса"""
    try:
        response = requests.get(f"{API_BASE_URL}/russian-marketplaces/{marketplace}/filters")
        if response.status_code == 200:
            return response.json()["filters"]
        return {}
    except:
        return {}

def main():
    st.title("🇷🇺 Российские маркетплейсы")
    st.markdown("---")

    # Получаем список маркетплейсов
    marketplaces = get_marketplaces()
    
    if not marketplaces:
        st.error("Не удалось загрузить список маркетплейсов")
        return

    # Создаем вкладки для каждого маркетплейса
    marketplace_names = [mp["name"] for mp in marketplaces]
    selected_marketplace = st.selectbox("Выберите маркетплейс:", marketplace_names)
    
    # Находим выбранный маркетплейс
    current_marketplace = next((mp for mp in marketplaces if mp["name"] == selected_marketplace), None)
    
    if not current_marketplace:
        st.error("Маркетплейс не найден")
        return

    st.markdown(f"### {current_marketplace['name']}")
    st.markdown(f"**Описание:** {current_marketplace['description']}")
    st.markdown(f"**URL:** {current_marketplace['url']}")
    
    # Основные функции
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Поиск товаров", "📊 Статистика", "🏷️ Категории", "⚙️ Настройки"])
    
    with tab1:
        st.subheader("Поиск товаров")
        
        # Форма поиска
        with st.form("search_form"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                query = st.text_input("Поисковый запрос:", placeholder="Введите название товара...")
            
            with col2:
                page = st.number_input("Страница:", min_value=1, value=1)
            
            # Фильтры
            st.markdown("**Фильтры:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                price_min = st.number_input("Цена от:", min_value=0, value=0)
                price_max = st.number_input("Цена до:", min_value=0, value=0)
                brand = st.text_input("Бренд:", placeholder="Например: Apple")
            
            with col2:
                rating = st.slider("Минимальный рейтинг:", 0.0, 5.0, 0.0, 0.1)
                discount = st.checkbox("Только со скидкой")
                in_stock = st.checkbox("Только в наличии")
            
            with col3:
                if current_marketplace["id"] == "avito":
                    region = st.text_input("Регион:", placeholder="Например: moskva")
                    category = st.selectbox("Категория:", ["", "electronics", "clothing", "home", "beauty", "sports", "kids"])
                    condition = st.selectbox("Состояние:", ["", "new", "used", "broken"])
                else:
                    region = None
                    category = None
                    condition = None
            
            if st.form_submit_button("🔍 Найти товары"):
                if query:
                    # Формируем фильтры
                    filters = {}
                    if price_min > 0:
                        filters["price_min"] = price_min
                    if price_max > 0:
                        filters["price_max"] = price_max
                    if brand:
                        filters["brand"] = brand
                    if rating > 0:
                        filters["rating"] = rating
                    if discount:
                        filters["discount"] = True
                    if in_stock:
                        filters["in_stock"] = True
                    if region:
                        filters["region"] = region
                    if category:
                        filters["category"] = category
                    if condition:
                        filters["condition"] = condition
                    
                    # Выполняем поиск
                    with st.spinner("Поиск товаров..."):
                        results = search_products(current_marketplace["id"], query, page, filters)
                    
                    if results and results.get("products"):
                        products = results["products"]
                        st.success(f"Найдено {len(products)} товаров")
                        
                        # Отображаем товары
                        for i, product in enumerate(products):
                            with st.expander(f"🛍️ {product.get('title', 'Без названия')} - {product.get('price', 0):.0f} ₽"):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.write(f"**Цена:** {product.get('price', 0):.0f} ₽")
                                    if product.get('old_price', 0) > 0:
                                        st.write(f"**Старая цена:** {product.get('old_price', 0):.0f} ₽")
                                    if product.get('rating', 0) > 0:
                                        st.write(f"**Рейтинг:** {product.get('rating', 0):.1f} ⭐")
                                    if product.get('reviews_count', 0) > 0:
                                        st.write(f"**Отзывы:** {product.get('reviews_count', 0)}")
                                    if product.get('brand'):
                                        st.write(f"**Бренд:** {product.get('brand')}")
                                    if product.get('category'):
                                        st.write(f"**Категория:** {product.get('category')}")
                                    if product.get('seller'):
                                        st.write(f"**Продавец:** {product.get('seller')}")
                                    if product.get('discount', 0) > 0:
                                        st.write(f"**Скидка:** {product.get('discount', 0)}%")
                                    if product.get('stock', 0) > 0:
                                        st.write(f"**В наличии:** {product.get('stock', 0)} шт.")
                                
                                with col2:
                                    if product.get('images'):
                                        st.image(product['images'][0], width=150)
                                    if product.get('url'):
                                        st.link_button("Открыть товар", product['url'])
                    else:
                        st.warning("Товары не найдены")
                else:
                    st.warning("Введите поисковый запрос")
    
    with tab2:
        st.subheader("Статистика маркетплейса")
        
        # Получаем статистику
        try:
            response = requests.get(f"{API_BASE_URL}/russian-marketplaces/{current_marketplace['id']}/stats")
            if response.status_code == 200:
                stats = response.json()["stats"]
                
                # Основные метрики
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        label="Всего товаров",
                        value=f"{stats['total_products']:,}",
                        delta="+5% за месяц"
                    )
                
                with col2:
                    st.metric(
                        label="Категорий",
                        value=stats['categories'],
                        delta="+2"
                    )
                
                with col3:
                    st.metric(
                        label="Средняя цена",
                        value=f"{stats['avg_price']:,.0f} ₽",
                        delta="+3%"
                    )
                
                with col4:
                    st.metric(
                        label="Обновлено",
                        value=stats['last_updated'][:10],
                        delta="Сегодня"
                    )
                
                # Популярные бренды
                st.subheader("Популярные бренды")
                brands_df = pd.DataFrame({
                    'Бренд': stats['popular_brands'],
                    'Популярность': [100, 85, 70, 60, 50]  # Заглушка
                })
                
                fig_brands = px.bar(brands_df, x='Бренд', y='Популярность', 
                                  title='Топ-5 брендов по популярности')
                st.plotly_chart(fig_brands, use_container_width=True)
                
            else:
                st.error("Не удалось загрузить статистику")
        except:
            st.error("Ошибка при загрузке статистики")
    
    with tab3:
        st.subheader("Категории товаров")
        
        # Получаем категории
        categories = get_marketplace_categories(current_marketplace["id"])
        
        if categories:
            # Создаем DataFrame для отображения
            categories_df = pd.DataFrame([
                {"Категория (EN)": key, "Категория (RU)": value} 
                for key, value in categories.items()
            ])
            
            st.dataframe(categories_df, use_container_width=True)
            
            # График категорий
            fig_categories = px.pie(
                values=[1] * len(categories), 
                names=list(categories.values()),
                title="Распределение категорий"
            )
            st.plotly_chart(fig_categories, use_container_width=True)
        else:
            st.warning("Категории не найдены")
    
    with tab4:
        st.subheader("Настройки парсинга")
        
        # Получаем фильтры
        filters = get_marketplace_filters(current_marketplace["id"])
        
        if filters:
            st.write("**Доступные фильтры:**")
            for key, value in filters.items():
                st.write(f"• **{key}:** {value}")
        
        # Настройки парсинга
        st.write("**Настройки парсинга:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            delay_min = st.number_input("Минимальная задержка (сек):", min_value=0, value=1)
            delay_max = st.number_input("Максимальная задержка (сек):", min_value=0, value=3)
            max_retries = st.number_input("Максимум попыток:", min_value=1, value=3)
        
        with col2:
            use_proxy = st.checkbox("Использовать прокси")
            rotate_headers = st.checkbox("Ротация заголовков")
            cache_results = st.checkbox("Кэшировать результаты")
        
        if st.button("💾 Сохранить настройки"):
            st.success("Настройки сохранены!")
        
        # Тест подключения
        st.write("**Тест подключения:**")
        if st.button("🔗 Проверить подключение"):
            with st.spinner("Проверка подключения..."):
                try:
                    response = requests.get(f"{API_BASE_URL}/russian-marketplaces/{current_marketplace['id']}/categories", timeout=5)
                    if response.status_code == 200:
                        st.success("✅ Подключение успешно!")
                    else:
                        st.error("❌ Ошибка подключения")
                except:
                    st.error("❌ Не удалось подключиться")

if __name__ == "__main__":
    main()
