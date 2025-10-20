"""Страница планировщика отчетов в дашборде"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import time

# Настройка страницы
st.set_page_config(
    page_title="Планировщик отчетов - Universal Parser",
    page_icon="📅",
    layout="wide"
)

# API базовый URL
API_BASE_URL = "http://localhost:8000/api/v1"

def fetch_data(endpoint: str, params: dict = None, method: str = "GET", data: dict = None):
    """Получить данные с API"""
    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}/report-scheduler/{endpoint}", params=params)
        elif method == "POST":
            response = requests.post(f"{API_BASE_URL}/report-scheduler/{endpoint}", params=params, json=data)
        elif method == "PUT":
            response = requests.put(f"{API_BASE_URL}/report-scheduler/{endpoint}", params=params, json=data)
        elif method == "DELETE":
            response = requests.delete(f"{API_BASE_URL}/report-scheduler/{endpoint}", params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Ошибка API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None

def main():
    st.title("📅 Планировщик отчетов")
    st.markdown("---")

    # Выбор пользователя
    user_id = st.selectbox(
        "Выберите пользователя:",
        ["user_1", "user_2", "user_3", "user_4", "user_5"],
        index=0
    )

    if not user_id:
        st.warning("Выберите пользователя для управления отчетами")
        return

    # Основные вкладки
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Мои расписания", "➕ Создать расписание", "📋 Шаблоны", "📈 Статистика"
    ])

    with tab1:
        st.subheader("📊 Мои расписания")
        
        # Получаем расписания пользователя
        schedules_data = fetch_data("schedules", {"user_id": user_id})
        
        if schedules_data:
            schedules = schedules_data.get("schedules", [])
            
            if schedules:
                # Создаем DataFrame для отображения
                df_schedules = pd.DataFrame(schedules)
                
                # Отображаем таблицу расписаний
                st.dataframe(df_schedules, use_container_width=True)
                
                # Действия с расписаниями
                st.subheader("🔧 Управление расписаниями")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    selected_report = st.selectbox(
                        "Выберите отчет для управления:",
                        [s["report_type"] for s in schedules]
                    )
                
                with col2:
                    action = st.selectbox(
                        "Действие:",
                        ["Включить/выключить", "Запустить сейчас", "Удалить"]
                    )
                
                with col3:
                    if st.button("Выполнить действие"):
                        if action == "Включить/выключить":
                            # Находим текущий статус
                            current_schedule = next(s for s in schedules if s["report_type"] == selected_report)
                            new_status = not current_schedule["is_active"]
                            
                            result = fetch_data(
                                f"schedules/{selected_report}/toggle",
                                {"user_id": user_id, "is_active": new_status},
                                method="POST"
                            )
                            
                            if result:
                                st.success(f"Расписание {'включено' if new_status else 'выключено'}")
                                st.rerun()
                        
                        elif action == "Запустить сейчас":
                            result = fetch_data(
                                f"schedules/{selected_report}/run-now",
                                {"user_id": user_id},
                                method="POST"
                            )
                            
                            if result:
                                st.success("Отчет запущен на генерацию")
                        
                        elif action == "Удалить":
                            if st.checkbox("Подтвердить удаление"):
                                result = fetch_data(
                                    f"schedules/{selected_report}",
                                    {"user_id": user_id},
                                    method="DELETE"
                                )
                                
                                if result:
                                    st.success("Расписание удалено")
                                    st.rerun()
            else:
                st.info("У вас нет настроенных расписаний")
        else:
            st.warning("Не удалось загрузить расписания")

    with tab2:
        st.subheader("➕ Создать новое расписание")
        
        # Получаем шаблоны отчетов
        templates_data = fetch_data("templates")
        
        if templates_data:
            templates = templates_data.get("templates", [])
            
            # Форма создания расписания
            with st.form("create_schedule_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Выбор типа отчета
                    report_options = {t["name"]: t["id"] for t in templates}
                    selected_report_name = st.selectbox("Тип отчета:", list(report_options.keys()))
                    selected_report_id = report_options[selected_report_name]
                    
                    # Описание отчета
                    selected_template = next(t for t in templates if t["id"] == selected_report_id)
                    st.info(f"Описание: {selected_template['description']}")
                    
                    # Расписание
                    schedule_type = st.selectbox(
                        "Частота:",
                        ["daily", "weekly", "monthly"],
                        format_func=lambda x: {"daily": "Ежедневно", "weekly": "Еженедельно", "monthly": "Ежемесячно"}[x]
                    )
                    
                    time_input = st.time_input("Время отправки:", value=datetime.strptime(selected_template.get("default_time", "09:00"), "%H:%M").time())
                    time_str = time_input.strftime("%H:%M")
                
                with col2:
                    # Email
                    email = st.text_input("Email для отправки:", value="user@example.com")
                    
                    # Формат экспорта
                    export_format = st.selectbox(
                        "Формат экспорта:",
                        ["pdf", "excel", "csv", "json"],
                        format_func=lambda x: {"pdf": "PDF", "excel": "Excel", "csv": "CSV", "json": "JSON"}[x]
                    )
                    
                    # Фильтры
                    st.subheader("🔍 Фильтры")
                    
                    # Период
                    period_type = st.selectbox("Период:", ["Последние N дней", "Произвольный период"])
                    
                    if period_type == "Последние N дней":
                        days = st.number_input("Количество дней:", min_value=1, max_value=365, value=7)
                        end_date = datetime.now().date()
                        start_date = end_date - timedelta(days=days)
                    else:
                        col_start, col_end = st.columns(2)
                        with col_start:
                            start_date = st.date_input("Начальная дата:", value=datetime.now().date() - timedelta(days=7))
                        with col_end:
                            end_date = st.date_input("Конечная дата:", value=datetime.now().date())
                    
                    # Дополнительные фильтры
                    marketplace = st.selectbox(
                        "Маркетплейс:",
                        ["Все", "Wildberries", "Ozon", "Yandex Market", "Avito", "M.Video", "Eldorado", "AliExpress", "Amazon", "eBay"]
                    )
                    
                    category = st.selectbox(
                        "Категория:",
                        ["Все", "Электроника", "Одежда", "Обувь", "Дом и сад", "Красота", "Спорт", "Авто", "Детские товары", "Книги"]
                    )
                
                # Подготавливаем фильтры
                filters = {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
                if marketplace != "Все":
                    filters["marketplace"] = marketplace
                if category != "Все":
                    filters["category"] = category
                
                # Кнопка создания
                if st.form_submit_button("Создать расписание"):
                    # Создаем расписание
                    schedule_data = {
                        "report_type": selected_report_id,
                        "schedule_type": schedule_type,
                        "time": time_str,
                        "email": email,
                        "filters": filters,
                        "export_format": export_format
                    }
                    
                    result = fetch_data(
                        "schedules",
                        {"user_id": user_id},
                        method="POST",
                        data=schedule_data
                    )
                    
                    if result:
                        st.success("Расписание создано успешно!")
                        st.rerun()
                    else:
                        st.error("Ошибка создания расписания")
        else:
            st.warning("Не удалось загрузить шаблоны отчетов")

    with tab3:
        st.subheader("📋 Шаблоны отчетов")
        
        # Получаем шаблоны
        templates_data = fetch_data("templates")
        
        if templates_data:
            templates = templates_data.get("templates", [])
            
            # Отображаем шаблоны
            for template in templates:
                with st.expander(f"📊 {template['name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Описание:** {template['description']}")
                        st.write(f"**Категория:** {template['category']}")
                        st.write(f"**Рекомендуемая частота:** {template['default_schedule']}")
                        st.write(f"**Рекомендуемое время:** {template['default_time']}")
                    
                    with col2:
                        st.write("**Параметры фильтрации:**")
                        for param in template['parameters']:
                            st.write(f"• {param}")
                        
                        if st.button(f"Использовать шаблон", key=f"use_{template['id']}"):
                            st.session_state.selected_template = template['id']
                            st.rerun()
        else:
            st.warning("Не удалось загрузить шаблоны")

    with tab4:
        st.subheader("📈 Статистика планировщика")
        
        # Получаем статус планировщика
        status_data = fetch_data("status")
        
        if status_data:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Статус планировщика",
                    "🟢 Работает" if status_data.get("is_running") else "🔴 Остановлен"
                )
            
            with col2:
                st.metric(
                    "Всего расписаний",
                    status_data.get("total_schedules", 0)
                )
            
            with col3:
                st.metric(
                    "Активных расписаний",
                    status_data.get("active_schedules", 0)
                )
            
            with col4:
                st.metric(
                    "Последняя проверка",
                    status_data.get("last_check", "N/A")[:19]
                )
        
        # Получаем историю отчетов
        history_data = fetch_data("history", {"user_id": user_id, "limit": 20})
        
        if history_data:
            history = history_data.get("history", [])
            
            if history:
                st.subheader("📋 История отчетов")
                
                # Создаем DataFrame для истории
                df_history = pd.DataFrame(history)
                df_history['last_run'] = pd.to_datetime(df_history['last_run'])
                df_history['next_run'] = pd.to_datetime(df_history['next_run'])
                
                # Отображаем таблицу
                st.dataframe(df_history, use_container_width=True)
                
                # График активности отчетов
                st.subheader("📊 Активность отчетов")
                
                # Группируем по дням
                df_history['date'] = df_history['last_run'].dt.date
                daily_counts = df_history.groupby('date').size().reset_index(name='count')
                
                if not daily_counts.empty:
                    fig = px.bar(
                        daily_counts,
                        x='date',
                        y='count',
                        title='Количество сгенерированных отчетов по дням',
                        labels={'count': 'Количество отчетов', 'date': 'Дата'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Распределение по типам отчетов
                report_counts = df_history['report_type'].value_counts()
                
                fig = px.pie(
                    report_counts,
                    values=report_counts.values,
                    names=report_counts.index,
                    title='Распределение отчетов по типам'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("История отчетов пуста")
        else:
            st.warning("Не удалось загрузить историю отчетов")

    # Боковая панель с быстрыми действиями
    with st.sidebar:
        st.subheader("🚀 Быстрые действия")
        
        if st.button("🔄 Обновить данные"):
            st.rerun()
        
        if st.button("▶️ Запустить планировщик"):
            result = fetch_data("start", method="POST")
            if result:
                st.success("Планировщик запущен")
            else:
                st.error("Ошибка запуска планировщика")
        
        if st.button("⏹️ Остановить планировщик"):
            result = fetch_data("stop", method="POST")
            if result:
                st.success("Планировщик остановлен")
            else:
                st.error("Ошибка остановки планировщика")
        
        st.subheader("📊 Статистика пользователя")
        
        if schedules_data:
            st.metric("Всего расписаний", schedules_data.get("total_schedules", 0))
            st.metric("Активных расписаний", schedules_data.get("active_schedules", 0))
        
        st.subheader("ℹ️ Информация")
        st.info("""
        **Планировщик отчетов** позволяет автоматически генерировать и отправлять отчеты по расписанию.
        
        **Поддерживаемые форматы:**
        - PDF
        - Excel
        - CSV
        - JSON
        
        **Частота отправки:**
        - Ежедневно
        - Еженедельно
        - Ежемесячно
        """)

if __name__ == "__main__":
    main()


