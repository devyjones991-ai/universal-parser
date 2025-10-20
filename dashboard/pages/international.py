"""Страница интернационализации в дашборде"""

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import asyncio

# Настройка страницы
st.set_page_config(
    page_title="Интернационализация - Universal Parser",
    page_icon="🌍",
    layout="wide"
)

# API базовый URL
API_BASE_URL = "http://localhost:8000/api/v1"

def fetch_data(endpoint: str, params: dict = None):
    """Получить данные с API"""
    try:
        response = requests.get(f"{API_BASE_URL}/international/{endpoint}", params=params)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return None

def main():
    st.title("🌍 Интернационализация и локализация")
    st.markdown("---")

    # Боковая панель с настройками локали
    with st.sidebar:
        st.header("🌐 Настройки локали")
        
        # Выбор языка
        locales_data = fetch_data("locales")
        if locales_data:
            locales = locales_data.get("locales", [])
            locale_options = {f"{loc['name']} ({loc['code']})": loc['code'] for loc in locales}
            selected_locale = st.selectbox("Язык интерфейса:", list(locale_options.keys()))
            current_locale = locale_options[selected_locale]
        else:
            current_locale = "en"
        
        # Выбор валюты
        currencies_data = fetch_data("currencies")
        if currencies_data:
            currencies = currencies_data.get("currencies", [])
            currency_options = {f"{curr['name']} ({curr['code']})": curr['code'] for curr in currencies}
            selected_currency = st.selectbox("Валюта:", list(currency_options.keys()))
            current_currency = currency_options[selected_currency]
        else:
            current_currency = "USD"
        
        # Выбор часового пояса
        timezones_data = fetch_data("timezones")
        if timezones_data:
            timezones = timezones_data.get("timezones", [])
            timezone_options = {f"{tz['display_name']} ({tz['name']})": tz['name'] for tz in timezones}
            selected_timezone = st.selectbox("Часовой пояс:", list(timezone_options.keys()))
            current_timezone = timezone_options[selected_timezone]
        else:
            current_timezone = "UTC"
        
        # Кнопка применения настроек
        if st.button("Применить настройки"):
            st.session_state.current_locale = current_locale
            st.session_state.current_currency = current_currency
            st.session_state.current_timezone = current_timezone
            st.success("Настройки применены!")
            st.rerun()

    # Основной контент
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌐 Локали", "💱 Валюты", "🕐 Часовые пояса", "📝 Переводы", "🔧 Настройки"
    ])

    with tab1:
        st.subheader("🌐 Поддерживаемые локали")
        
        # Получаем список локалей
        locales_data = fetch_data("locales")
        
        if locales_data:
            locales = locales_data.get("locales", [])
            
            # Создаем DataFrame для отображения
            df_locales = pd.DataFrame(locales)
            
            # Отображаем таблицу
            st.dataframe(df_locales, use_container_width=True)
            
            # Статистика по локалям
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Всего локалей", len(locales))
            
            with col2:
                rtl_count = len([loc for loc in locales if loc.get('is_rtl', False)])
                st.metric("RTL языки", rtl_count)
            
            with col3:
                st.metric("Латинские языки", len(locales) - rtl_count)
            
            with col4:
                st.metric("По умолчанию", locales_data.get("default", "en"))
            
            # Детальная информация о выбранной локали
            if current_locale:
                locale_info = fetch_data(f"locales/{current_locale}")
                if locale_info:
                    st.subheader(f"Информация о локали: {locale_info.get('name', current_locale)}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Код:** {locale_info.get('code')}")
                        st.write(f"**Язык:** {locale_info.get('language')}")
                        st.write(f"**Территория:** {locale_info.get('territory')}")
                        st.write(f"**RTL:** {'Да' if locale_info.get('is_rtl') else 'Нет'}")
                    
                    with col2:
                        st.write(f"**Валюта по умолчанию:** {locale_info.get('currency')}")
                        st.write(f"**Часовой пояс:** {locale_info.get('timezone')}")
                        st.write(f"**Эмодзи:** {locale_info.get('emoji', '🌍')}")
        else:
            st.warning("Не удалось загрузить данные о локалях")

    with tab2:
        st.subheader("💱 Валюты и конвертация")
        
        # Получаем список валют
        currencies_data = fetch_data("currencies")
        
        if currencies_data:
            currencies = currencies_data.get("currencies", [])
            
            # Фильтры валют
            col1, col2 = st.columns(2)
            
            with col1:
                currency_type = st.selectbox("Тип валюты:", ["Все", "Фиатные", "Криптовалюты"])
            
            with col2:
                search_currency = st.text_input("Поиск валюты:", placeholder="Введите код или название")
            
            # Фильтруем валюты
            filtered_currencies = currencies
            
            if currency_type == "Фиатные":
                filtered_currencies = [curr for curr in filtered_currencies if not curr.get('is_crypto', False)]
            elif currency_type == "Криптовалюты":
                filtered_currencies = [curr for curr in filtered_currencies if curr.get('is_crypto', False)]
            
            if search_currency:
                filtered_currencies = [
                    curr for curr in filtered_currencies
                    if search_currency.lower() in curr.get('code', '').lower() or
                       search_currency.lower() in curr.get('name', '').lower()
                ]
            
            # Отображаем валюты
            df_currencies = pd.DataFrame(filtered_currencies)
            st.dataframe(df_currencies, use_container_width=True)
            
            # Конвертер валют
            st.subheader("🔄 Конвертер валют")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                amount = st.number_input("Сумма:", min_value=0.0, value=100.0)
            
            with col2:
                from_currency = st.selectbox("Из валюты:", [curr['code'] for curr in currencies])
            
            with col3:
                to_currency = st.selectbox("В валюту:", [curr['code'] for curr in currencies])
            
            if st.button("Конвертировать"):
                conversion_data = fetch_data(
                    "currencies/convert",
                    {
                        "amount": amount,
                        "from_currency": from_currency,
                        "to_currency": to_currency
                    }
                )
                
                if conversion_data:
                    st.success(f"**{amount} {from_currency} = {conversion_data['converted_amount']:.2f} {to_currency}**")
                    st.info(f"Курс: 1 {from_currency} = {conversion_data['rate']:.6f} {to_currency}")
                else:
                    st.error("Ошибка конвертации валют")
            
            # Курсы валют
            st.subheader("📊 Курсы валют")
            
            base_currency = st.selectbox("Базовая валюта:", [curr['code'] for curr in currencies])
            target_currencies = st.multiselect(
                "Целевые валюты:",
                [curr['code'] for curr in currencies],
                default=["EUR", "RUB", "GBP", "JPY"]
            )
            
            if st.button("Получить курсы") and target_currencies:
                rates_data = fetch_data(
                    "currencies/rates",
                    {
                        "from_currency": base_currency,
                        "to_currencies": ",".join(target_currencies)
                    }
                )
                
                if rates_data:
                    rates_df = pd.DataFrame([
                        {"Валюта": curr, "Курс": rate}
                        for curr, rate in rates_data['rates'].items()
                    ])
                    
                    st.dataframe(rates_df, use_container_width=True)
                    
                    # График курсов
                    fig = px.bar(
                        rates_df,
                        x="Валюта",
                        y="Курс",
                        title=f"Курсы валют к {base_currency}"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Не удалось загрузить данные о валютах")

    with tab3:
        st.subheader("🕐 Часовые пояса")
        
        # Получаем список часовых поясов
        timezones_data = fetch_data("timezones")
        
        if timezones_data:
            timezones = timezones_data.get("timezones", [])
            
            # Группировка по регионам
            groups_data = fetch_data("timezones/groups")
            if groups_data:
                groups = groups_data.get("groups", {})
                
                for region, region_timezones in groups.items():
                    if region_timezones:
                        with st.expander(f"🌍 {region} ({len(region_timezones)} часовых поясов)"):
                            df_region = pd.DataFrame(region_timezones)
                            st.dataframe(df_region, use_container_width=True)
            
            # Конвертер часовых поясов
            st.subheader("🔄 Конвертер часовых поясов")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                datetime_input = st.datetime_input("Дата и время:", value=datetime.now())
            
            with col2:
                from_tz = st.selectbox("Из часового пояса:", [tz['name'] for tz in timezones])
            
            with col3:
                to_tz = st.selectbox("В часовой пояс:", [tz['name'] for tz in timezones])
            
            if st.button("Конвертировать время"):
                conversion_data = fetch_data(
                    "timezones/convert",
                    {
                        "datetime": datetime_input.isoformat(),
                        "from_timezone": from_tz,
                        "to_timezone": to_tz
                    }
                )
                
                if conversion_data:
                    st.success(f"**{conversion_data['original_datetime']} ({from_tz}) = {conversion_data['converted_datetime']} ({to_tz})**")
                    st.info(f"Разность: {conversion_data['time_difference']}")
                else:
                    st.error("Ошибка конвертации времени")
            
            # Текущее время в разных часовых поясах
            st.subheader("⏰ Текущее время")
            
            selected_timezones = st.multiselect(
                "Выберите часовые пояса:",
                [tz['name'] for tz in timezones],
                default=["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]
            )
            
            if selected_timezones:
                current_times = []
                for tz_name in selected_timezones:
                    time_data = fetch_data(f"timezones/current/{tz_name}")
                    if time_data:
                        current_times.append({
                            "Часовой пояс": tz_name,
                            "Время": time_data['current_time'],
                            "Смещение UTC": time_data['utc_offset'],
                            "Аббревиатура": time_data['abbreviation'],
                            "Летнее время": "Да" if time_data['is_dst'] else "Нет"
                        })
                
                if current_times:
                    df_times = pd.DataFrame(current_times)
                    st.dataframe(df_times, use_container_width=True)
            
            # Рабочие часы
            st.subheader("💼 Рабочие часы")
            
            col1, col2 = st.columns(2)
            
            with col1:
                work_tz = st.selectbox("Часовой пояс:", [tz['name'] for tz in timezones])
            
            with col2:
                work_hours = st.slider("Рабочие часы:", 0, 23, (9, 17))
            
            if st.button("Получить рабочие часы"):
                work_data = fetch_data(
                    f"timezones/working-hours/{work_tz}",
                    {
                        "start_hour": work_hours[0],
                        "end_hour": work_hours[1]
                    }
                )
                
                if work_data:
                    st.info(f"**Текущее время:** {work_data['current_time']}")
                    st.info(f"**Рабочие часы:** {work_data['work_start']} - {work_data['work_end']}")
                    st.info(f"**Рабочий день:** {'Да' if work_data['is_workday'] else 'Нет'}")
                    st.info(f"**Рабочее время:** {'Да' if work_data['is_working_hours'] else 'Нет'}")
        else:
            st.warning("Не удалось загрузить данные о часовых поясах")

    with tab4:
        st.subheader("📝 Переводы и локализация")
        
        # Получаем переводы для текущей локали
        if current_locale:
            translations_data = fetch_data("translations", {"locale": current_locale})
            
            if translations_data:
                translations = translations_data.get("translations", {})
                
                # Выбор пространства имен
                namespaces = list(translations.keys())
                selected_namespace = st.selectbox("Пространство имен:", ["Все"] + namespaces)
                
                if selected_namespace == "Все":
                    display_translations = translations
                else:
                    display_translations = translations.get(selected_namespace, {})
                
                # Отображаем переводы
                if display_translations:
                    st.json(display_translations)
                else:
                    st.info("Переводы не найдены")
            
            # Определение языка текста
            st.subheader("🔍 Определение языка")
            
            text_input = st.text_area("Введите текст для определения языка:", height=100)
            
            if st.button("Определить язык") and text_input:
                detection_data = fetch_data("detect-language", {"text": text_input})
                
                if detection_data:
                    st.success(f"**Определенный язык:** {detection_data['detected_language']}")
                    st.info(f"**Уверенность:** {detection_data['confidence'] * 100:.1f}%")
                    st.info(f"**RTL:** {'Да' if detection_data['is_rtl'] else 'Нет'}")
            
            # Форматирование валюты
            st.subheader("💰 Форматирование валюты")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                currency_amount = st.number_input("Сумма:", min_value=0.0, value=1234.56)
            
            with col2:
                currency_code = st.selectbox("Валюта:", [curr['code'] for curr in currencies])
            
            with col3:
                currency_locale = st.selectbox("Локаль:", [loc['code'] for loc in locales])
            
            if st.button("Форматировать валюту"):
                format_data = fetch_data(
                    "format/currency",
                    {
                        "amount": currency_amount,
                        "currency": currency_code,
                        "locale": currency_locale
                    }
                )
                
                if format_data:
                    st.success(f"**Форматированная сумма:** {format_data['formatted']}")
                    st.info(f"**Символ:** {format_data['symbol']}")
                    st.info(f"**Название:** {format_data['name']}")
            
            # Форматирование даты и времени
            st.subheader("📅 Форматирование даты и времени")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                datetime_input = st.datetime_input("Дата и время:", value=datetime.now())
            
            with col2:
                datetime_locale = st.selectbox("Локаль:", [loc['code'] for loc in locales])
            
            with col3:
                datetime_tz = st.selectbox("Часовой пояс:", [tz['name'] for tz in timezones])
            
            if st.button("Форматировать дату и время"):
                format_data = fetch_data(
                    "format/datetime",
                    {
                        "datetime_str": datetime_input.isoformat(),
                        "locale": datetime_locale,
                        "timezone": datetime_tz
                    }
                )
                
                if format_data:
                    st.success(f"**Форматированная дата и время:** {format_data['formatted']}")
                    st.info(f"**RTL:** {'Да' if format_data['is_rtl'] else 'Нет'}")

    with tab5:
        st.subheader("🔧 Настройки интернационализации")
        
        # Настройки по умолчанию
        st.subheader("⚙️ Настройки по умолчанию")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Язык по умолчанию", "English (en)")
        
        with col2:
            st.metric("Валюта по умолчанию", "USD")
        
        with col3:
            st.metric("Часовой пояс по умолчанию", "UTC")
        
        # RTL языки
        st.subheader("📝 RTL языки")
        
        rtl_data = fetch_data("rtl-languages")
        if rtl_data:
            rtl_languages = rtl_data.get("rtl_languages", [])
            
            df_rtl = pd.DataFrame(rtl_languages)
            st.dataframe(df_rtl, use_container_width=True)
        
        # Настройки для страны
        st.subheader("🏳️ Настройки для страны")
        
        country_code = st.text_input("Код страны (например, US, RU, DE):", value="US")
        
        if st.button("Получить настройки страны"):
            country_data = fetch_data(f"country-settings/{country_code}")
            
            if country_data:
                st.success(f"**Настройки для {country_code}:**")
                st.info(f"**Часовой пояс:** {country_data.get('timezone', 'N/A')}")
                st.info(f"**Валюта:** {country_data.get('currency', 'N/A')}")
                st.info(f"**Локаль:** {country_data.get('locale', 'N/A')}")
                st.info(f"**RTL:** {'Да' if country_data.get('is_rtl') else 'Нет'}")
        
        # Настройки для локали
        st.subheader("🌐 Настройки для локали")
        
        locale_code = st.selectbox("Код локали:", [loc['code'] for loc in locales])
        
        if st.button("Получить настройки локали"):
            locale_data = fetch_data(f"locale-settings/{locale_code}")
            
            if locale_data:
                st.success(f"**Настройки для {locale_code}:**")
                st.info(f"**Часовой пояс:** {locale_data.get('timezone', 'N/A')}")
                st.info(f"**Валюта:** {locale_data.get('currency', 'N/A')}")
                st.info(f"**RTL:** {'Да' if locale_data.get('is_rtl') else 'Нет'}")
                st.info(f"**Язык:** {locale_data.get('language', 'N/A')}")
                st.info(f"**Территория:** {locale_data.get('territory', 'N/A')}")
                st.info(f"**Отображаемое название:** {locale_data.get('display_name', 'N/A')}")

if __name__ == "__main__":
    main()


