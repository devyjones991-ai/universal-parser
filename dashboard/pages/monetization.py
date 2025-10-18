"""Страница монетизации в дашборде"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json

# Настройка страницы
st.set_page_config(
    page_title="Монетизация - Universal Parser",
    page_icon="💰",
    layout="wide"
)

# API базовый URL
API_BASE_URL = "http://localhost:8000/api/v1"

def get_subscription_plans():
    """Получить тарифные планы"""
    try:
        response = requests.get(f"{API_BASE_URL}/subscription/plans")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_user_billing(user_id: str):
    """Получить биллинг пользователя"""
    try:
        response = requests.get(f"{API_BASE_URL}/subscription/user/{user_id}/billing")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_payment_stats():
    """Получить статистику платежей"""
    # Заглушка для демонстрации
    return {
        "total_revenue": 12500.0,
        "monthly_revenue": 3200.0,
        "active_subscriptions": 156,
        "conversion_rate": 12.5,
        "churn_rate": 3.2
    }

def main():
    st.title("💰 Монетизация и Биллинг")
    st.markdown("---")

    # Получаем данные
    plans = get_subscription_plans()
    stats = get_payment_stats()

    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Общий доход",
            value=f"${stats['total_revenue']:,.0f}",
            delta=f"+{stats['monthly_revenue']:,.0f} за месяц"
        )
    
    with col2:
        st.metric(
            label="Активные подписки",
            value=stats['active_subscriptions'],
            delta="+12 за неделю"
        )
    
    with col3:
        st.metric(
            label="Конверсия",
            value=f"{stats['conversion_rate']:.1f}%",
            delta="+2.1%"
        )
    
    with col4:
        st.metric(
            label="Отток",
            value=f"{stats['churn_rate']:.1f}%",
            delta="-0.5%"
        )

    st.markdown("---")

    # Тарифные планы
    st.subheader("📋 Тарифные планы")
    
    if plans:
        # Создаем DataFrame для отображения планов
        plans_data = []
        for plan in plans:
            plans_data.append({
                "Название": plan['name'],
                "Уровень": plan['tier'],
                "Цена/месяц": f"${plan['price_monthly']:.2f}",
                "Цена/год": f"${plan['price_yearly']:.2f}",
                "Экономия": f"{((plan['price_monthly'] * 12 - plan['price_yearly']) / (plan['price_monthly'] * 12) * 100):.1f}%",
                "Активен": "✅" if plan['is_active'] else "❌"
            })
        
        df_plans = pd.DataFrame(plans_data)
        st.dataframe(df_plans, use_container_width=True)
    else:
        # Заглушка для демонстрации
        st.info("Загрузка тарифных планов...")
        
        # Создаем демо-данные
        demo_plans = [
            {
                "Название": "Free",
                "Уровень": "free",
                "Цена/месяц": "$0.00",
                "Цена/год": "$0.00",
                "Экономия": "0%",
                "Активен": "✅"
            },
            {
                "Название": "Pro",
                "Уровень": "pro",
                "Цена/месяц": "$19.99",
                "Цена/год": "$199.99",
                "Экономия": "16.7%",
                "Активен": "✅"
            },
            {
                "Название": "Premium",
                "Уровень": "premium",
                "Цена/месяц": "$49.99",
                "Цена/год": "$499.99",
                "Экономия": "16.7%",
                "Активен": "✅"
            }
        ]
        
        df_plans = pd.DataFrame(demo_plans)
        st.dataframe(df_plans, use_container_width=True)

    st.markdown("---")

    # Графики доходов
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Динамика доходов")
        
        # Создаем демо-данные для графика
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        revenue_data = []
        
        for date in dates:
            base_revenue = 100
            trend = (date - dates[0]).days * 2
            noise = pd.Series(range(len(dates))).sample(1).iloc[0] * 0.1
            revenue = base_revenue + trend + noise
            revenue_data.append(max(0, revenue))
        
        df_revenue = pd.DataFrame({
            'Дата': dates,
            'Доход': revenue_data
        })
        
        fig_revenue = px.line(df_revenue, x='Дата', y='Доход', title='Доход по дням')
        fig_revenue.update_layout(height=400)
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        st.subheader("🥧 Распределение подписок")
        
        # Создаем данные для круговой диаграммы
        subscription_data = {
            'Free': 1200,
            'Pro': 120,
            'Premium': 36
        }
        
        fig_pie = px.pie(
            values=list(subscription_data.values()),
            names=list(subscription_data.keys()),
            title='Распределение пользователей по тарифам'
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Кэшбек и рефералы
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💸 Кэшбек программа")
        
        cashback_stats = {
            "Общий кэшбек выплачен": "$2,450.00",
            "Ожидает выплаты": "$180.50",
            "Средний кэшбек": "$15.30",
            "Активных участников": 156
        }
        
        for key, value in cashback_stats.items():
            st.metric(key, value)
    
    with col2:
        st.subheader("👥 Реферальная программа")
        
        referral_stats = {
            "Всего рефералов": 89,
            "Завершенных": 67,
            "Общие награды": "$1,340.00",
            "Средняя награда": "$20.00"
        }
        
        for key, value in referral_stats.items():
            st.metric(key, value)

    st.markdown("---")

    # Управление подписками
    st.subheader("⚙️ Управление подписками")
    
    tab1, tab2, tab3 = st.tabs(["Создать план", "Статистика платежей", "Настройки"])
    
    with tab1:
        st.write("### Создание нового тарифного плана")
        
        with st.form("create_plan"):
            col1, col2 = st.columns(2)
            
            with col1:
                plan_name = st.text_input("Название плана", value="Enterprise")
                plan_tier = st.selectbox("Уровень", ["free", "pro", "premium", "enterprise"])
                price_monthly = st.number_input("Цена за месяц ($)", min_value=0.0, value=99.99)
            
            with col2:
                price_yearly = st.number_input("Цена за год ($)", min_value=0.0, value=999.99)
                is_active = st.checkbox("Активен", value=True)
            
            features = st.text_area("Функции (по одной на строку)", value="Unlimited items\nAPI access\nPriority support")
            limits = st.text_area("Ограничения (JSON)", value='{"max_items": 1000, "api_calls_per_hour": 10000}')
            
            if st.form_submit_button("Создать план"):
                st.success("План создан успешно!")
    
    with tab2:
        st.write("### Статистика платежей")
        
        # Создаем демо-данные для таблицы платежей
        payments_data = []
        for i in range(20):
            payments_data.append({
                "ID": f"pay_{i+1:03d}",
                "Пользователь": f"user_{i+1:03d}",
                "Сумма": f"${(i+1) * 19.99:.2f}",
                "Статус": ["completed", "pending", "failed"][i % 3],
                "Дата": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "Метод": ["stripe", "paypal"][i % 2]
            })
        
        df_payments = pd.DataFrame(payments_data)
        st.dataframe(df_payments, use_container_width=True)
    
    with tab3:
        st.write("### Настройки монетизации")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Настройки кэшбека**")
            cashback_rate_pro = st.slider("Кэшбек Pro (%)", 0.0, 10.0, 2.0)
            cashback_rate_premium = st.slider("Кэшбек Premium (%)", 0.0, 10.0, 5.0)
            
            st.write("**Настройки рефералов**")
            referral_reward = st.number_input("Награда за реферала ($)", min_value=0.0, value=20.0)
        
        with col2:
            st.write("**Настройки уведомлений**")
            email_notifications = st.checkbox("Email уведомления", value=True)
            sms_notifications = st.checkbox("SMS уведомления", value=False)
            
            st.write("**Настройки безопасности**")
            require_2fa = st.checkbox("Требовать 2FA для платежей", value=True)
            auto_renew = st.checkbox("Автопродление по умолчанию", value=True)
        
        if st.button("Сохранить настройки"):
            st.success("Настройки сохранены!")

if __name__ == "__main__":
    main()
