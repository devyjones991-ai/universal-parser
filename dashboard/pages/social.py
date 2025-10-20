"""Страница социальных функций в дашборде"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Настройка страницы
st.set_page_config(
    page_title="Социальные функции - Universal Parser",
    page_icon="👥",
    layout="wide"
)

# API базовый URL
API_BASE_URL = "http://localhost:8000/api/v1"

def get_user_profile(user_id: str):
    """Получить профиль пользователя"""
    try:
        response = requests.get(f"{API_BASE_URL}/social/profiles/{user_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_user_stats(user_id: str):
    """Получить статистику пользователя"""
    try:
        response = requests.get(f"{API_BASE_URL}/social/profiles/{user_id}/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_social_feed(user_id: str, page: int = 1):
    """Получить социальную ленту"""
    try:
        response = requests.get(f"{API_BASE_URL}/social/feed", params={
            "user_id": user_id,
            "page": page,
            "limit": 20
        })
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_leaderboard(leaderboard_id: str):
    """Получить лидерборд"""
    try:
        response = requests.get(f"{API_BASE_URL}/social/leaderboards/{leaderboard_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_achievements():
    """Получить список достижений"""
    try:
        response = requests.get(f"{API_BASE_URL}/social/achievements")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def main():
    st.title("👥 Социальные функции и геймификация")
    st.markdown("---")

    # Выбор пользователя
    user_id = st.selectbox(
        "Выберите пользователя:",
        ["user_1", "user_2", "user_3", "user_4", "user_5"],
        index=0
    )

    if not user_id:
        st.warning("Выберите пользователя для просмотра социальных функций")
        return

    # Получаем данные пользователя
    profile = get_user_profile(user_id)
    stats = get_user_stats(user_id)

    if not profile or not stats:
        st.error("Не удалось загрузить данные пользователя")
        return

    # Основные вкладки
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Профиль", "📊 Статистика", "📱 Социальная лента", 
        "🏆 Достижения", "📈 Лидерборды"
    ])

    with tab1:
        st.subheader("👤 Профиль пользователя")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Аватар
            if profile.get('avatar_url'):
                st.image(profile['avatar_url'], width=150)
            else:
                st.image("https://via.placeholder.com/150x150/cccccc/666666?text=Avatar", width=150)
            
            # Основная информация
            st.write(f"**Имя:** {profile.get('display_name', 'Не указано')}")
            st.write(f"**Уровень:** {profile.get('level', 1)}")
            st.write(f"**Очки опыта:** {profile.get('experience_points', 0):,}")
            st.write(f"**Общие очки:** {profile.get('total_points', 0):,}")
            st.write(f"**Репутация:** {profile.get('reputation', 0)}")
        
        with col2:
            # Биография
            st.write("**О себе:**")
            st.write(profile.get('bio', 'Биография не указана'))
            
            # Контактная информация
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                st.write(f"**Местоположение:** {profile.get('location', 'Не указано')}")
                st.write(f"**Веб-сайт:** {profile.get('website', 'Не указан')}")
            with col2_2:
                st.write(f"**Последний раз онлайн:** {profile.get('last_seen', 'Неизвестно')}")
                st.write(f"**Профиль создан:** {profile.get('created_at', 'Неизвестно')[:10]}")

        # Настройки приватности
        st.subheader("🔒 Настройки приватности")
        col3, col4 = st.columns(2)
        
        with col3:
            st.write(f"**Публичный профиль:** {'✅' if profile.get('is_public') else '❌'}")
            st.write(f"**Показывать email:** {'✅' if profile.get('show_email') else '❌'}")
            st.write(f"**Показывать телефон:** {'✅' if profile.get('show_phone') else '❌'}")
        
        with col4:
            st.write(f"**Принимать запросы в друзья:** {'✅' if profile.get('allow_friend_requests') else '❌'}")
            st.write(f"**Принимать сообщения:** {'✅' if profile.get('allow_messages') else '❌'}")

    with tab2:
        st.subheader("📊 Статистика пользователя")
        
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Друзья",
                value=stats.get('friends_count', 0),
                delta="+2 за неделю"
            )
        
        with col2:
            st.metric(
                label="Подписчики",
                value=stats.get('followers_count', 0),
                delta="+5 за неделю"
            )
        
        with col3:
            st.metric(
                label="Посты",
                value=stats.get('posts_count', 0),
                delta="+1 за день"
            )
        
        with col4:
            st.metric(
                label="Комментарии",
                value=stats.get('comments_count', 0),
                delta="+3 за день"
            )

        # Дополнительная статистика
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.metric(
                label="Лайки получено",
                value=stats.get('likes_received', 0),
                delta="+10 за неделю"
            )
        
        with col6:
            st.metric(
                label="Достижения",
                value=stats.get('achievements_count', 0),
                delta="+1 за месяц"
            )
        
        with col7:
            st.metric(
                label="Группы",
                value=stats.get('groups_count', 0),
                delta="+1 за месяц"
            )
        
        with col8:
            st.metric(
                label="Репутация",
                value=stats.get('reputation', 0),
                delta="+5 за неделю"
            )

        # Графики активности
        st.subheader("📈 Графики активности")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # График постов по дням
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
            posts_data = [max(0, int(stats.get('posts_count', 0) / 30) + (i % 3)) for i in range(30)]
            
            df_posts = pd.DataFrame({
                'Дата': dates,
                'Посты': posts_data
            })
            
            fig_posts = px.line(df_posts, x='Дата', y='Посты', title='Посты по дням')
            st.plotly_chart(fig_posts, use_container_width=True)
        
        with col2:
            # График лайков
            likes_data = [max(0, int(stats.get('likes_received', 0) / 30) + (i % 5)) for i in range(30)]
            
            df_likes = pd.DataFrame({
                'Дата': dates,
                'Лайки': likes_data
            })
            
            fig_likes = px.bar(df_likes, x='Дата', y='Лайки', title='Лайки по дням')
            st.plotly_chart(fig_likes, use_container_width=True)

    with tab3:
        st.subheader("📱 Социальная лента")
        
        # Получаем социальную ленту
        feed = get_social_feed(user_id)
        
        if feed and feed.get('posts'):
            posts = feed['posts']
            st.success(f"Загружено {len(posts)} постов")
            
            for post in posts:
                with st.expander(f"📝 {post.get('content', 'Без содержания')[:50]}..."):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Автор:** {post.get('author', {}).get('display_name', 'Неизвестно')}")
                        st.write(f"**Содержание:** {post.get('content', '')}")
                        st.write(f"**Тип:** {post.get('post_type', 'text')}")
                        if post.get('marketplace'):
                            st.write(f"**Маркетплейс:** {post.get('marketplace')}")
                    
                    with col2:
                        st.write(f"**Лайки:** {post.get('like_count', 0)} ❤️")
                        st.write(f"**Комментарии:** {post.get('comment_count', 0)} 💬")
                        st.write(f"**Просмотры:** {post.get('view_count', 0)} 👁️")
                        st.write(f"**Дата:** {post.get('created_at', '')[:10]}")
        else:
            st.info("Социальная лента пуста")

    with tab4:
        st.subheader("🏆 Достижения")
        
        # Получаем достижения
        achievements = get_achievements()
        
        if achievements:
            # Создаем DataFrame для отображения
            achievements_data = []
            for achievement in achievements:
                achievements_data.append({
                    "Название": achievement.get('name', ''),
                    "Описание": achievement.get('description', ''),
                    "Категория": achievement.get('category', ''),
                    "Тип": achievement.get('type', ''),
                    "Награда": f"{achievement.get('points_reward', 0)} очков",
                    "Скрытое": "✅" if achievement.get('is_hidden') else "❌"
                })
            
            df_achievements = pd.DataFrame(achievements_data)
            st.dataframe(df_achievements, use_container_width=True)
            
            # График достижений по категориям
            category_counts = df_achievements['Категория'].value_counts()
            fig_categories = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Достижения по категориям"
            )
            st.plotly_chart(fig_categories, use_container_width=True)
        else:
            st.warning("Достижения не найдены")

    with tab5:
        st.subheader("📈 Лидерборды")
        
        # Создаем демо-данные для лидербордов
        leaderboards_data = [
            {"id": "parsing", "name": "Парсинг товаров", "category": "parsing"},
            {"id": "social", "name": "Социальная активность", "category": "social"},
            {"id": "trading", "name": "Торговля", "category": "trading"}
        ]
        
        selected_leaderboard = st.selectbox(
            "Выберите лидерборд:",
            [lb["name"] for lb in leaderboards_data]
        )
        
        # Создаем демо-данные для лидерборда
        demo_entries = []
        for i in range(20):
            demo_entries.append({
                "rank": i + 1,
                "user": f"user_{i+1}",
                "score": 1000 - (i * 50),
                "level": max(1, 10 - i),
                "points": 1000 - (i * 50)
            })
        
        df_leaderboard = pd.DataFrame(demo_entries)
        
        # Отображаем лидерборд
        st.dataframe(
            df_leaderboard[['rank', 'user', 'score', 'level']],
            use_container_width=True,
            hide_index=True
        )
        
        # График лидерборда
        fig_leaderboard = px.bar(
            df_leaderboard.head(10),
            x='user',
            y='score',
            title=f"Топ-10 в лидерборде '{selected_leaderboard}'"
        )
        fig_leaderboard.update_xaxes(tickangle=45)
        st.plotly_chart(fig_leaderboard, use_container_width=True)

    # Боковая панель с быстрыми действиями
    with st.sidebar:
        st.subheader("🚀 Быстрые действия")
        
        if st.button("📝 Создать пост"):
            st.info("Функция создания поста будет добавлена")
        
        if st.button("👥 Найти друзей"):
            st.info("Функция поиска друзей будет добавлена")
        
        if st.button("🏆 Проверить достижения"):
            st.info("Функция проверки достижений будет добавлена")
        
        if st.button("📊 Обновить статистику"):
            st.rerun()
        
        st.subheader("📈 Прогресс уровня")
        
        # Прогресс-бар уровня
        current_level = profile.get('level', 1)
        current_exp = profile.get('experience_points', 0)
        required_exp = current_level * 1000
        progress = min(100, (current_exp / required_exp) * 100) if required_exp > 0 else 0
        
        st.progress(progress / 100)
        st.write(f"Уровень {current_level}")
        st.write(f"Опыт: {current_exp:,} / {required_exp:,}")
        
        if progress >= 100:
            st.success("🎉 Готов к повышению уровня!")

if __name__ == "__main__":
    main()


