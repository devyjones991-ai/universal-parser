#!/usr/bin/env python3
"""
Тестовый скрипт для проверки парсинга без Telegram бота
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
import json
from config import settings, parsing_profiles

async def test_wildberries_parsing():
    """Тестируем парсинг Wildberries"""
    print("Тестируем парсинг Wildberries...")
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Используем профиль из parsing_profiles
            profile = parsing_profiles.get("wildberries_simple")
            if not profile:
                print("Профиль wildberries_search не найден")
                return
            
            # Формируем URL с параметрами
            url = profile["url"]
            params = {}
            for key, value in profile["params"].items():
                if isinstance(value, str) and "{" in value:
                    params[key] = value.format(search_term="iphone")
                else:
                    params[key] = value
            
            print(f"Запрос к: {url}")
            print(f"Параметры: {params}")
            
            response = await client.get(url, params=params)
            print(f"Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Получен JSON ответ")
                
                # Извлекаем данные по пути
                if "data_path" in profile and profile["data_path"]:
                    try:
                        for path_part in profile["data_path"].split("."):
                            data = data[path_part]
                    except (KeyError, TypeError) as e:
                        print(f"Ошибка извлечения данных: {e}")
                        print(f"Доступные ключи: {list(data.keys()) if isinstance(data, dict) else 'Не словарь'}")
                        return False
                
                # Если data_path пустой, используем весь ответ
                if not isinstance(data, list):
                    data = [data]  # Преобразуем в список для единообразия
                
                print(f"Найдено товаров: {len(data)}")
                
                # Показываем первые 3 товара
                for i, item in enumerate(data[:3]):
                    print(f"\nТовар {i+1}:")
                    for field, api_field in profile["fields"].items():
                        # Извлекаем значение по вложенному пути
                        value = item
                        try:
                            for part in api_field.split("."):
                                value = value[part]
                        except (KeyError, TypeError):
                            value = "N/A"
                        print(f"   {field}: {value}")
                
                return True
            else:
                print(f"Ошибка HTTP: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

async def test_simple_parsing():
    """Тестируем простое парсинг HTML"""
    print("\nТестируем простое парсинг HTML...")
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Тестируем на простом сайте
            url = "https://example.com"
            response = await client.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "lxml")
                title = soup.find("title")
                print(f"Заголовок страницы: {title.text if title else 'Не найден'}")
                return True
            else:
                print(f"Ошибка HTTP: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    print("Запуск тестирования парсера...")
    print(f"Текущая директория: {os.getcwd()}")
    print(f"Настройки загружены: {settings.DATABASE_URL}")
    
    # Тестируем простое парсинг
    simple_ok = await test_simple_parsing()
    
    # Тестируем Wildberries
    wb_ok = await test_wildberries_parsing()
    
    print(f"\nРезультаты тестирования:")
    print(f"   Простое парсинг: {'OK' if simple_ok else 'FAIL'}")
    print(f"   Wildberries: {'OK' if wb_ok else 'FAIL'}")
    
    if simple_ok and wb_ok:
        print("\nВсе тесты прошли успешно!")
    else:
        print("\nНекоторые тесты не прошли")

if __name__ == "__main__":
    import os
    asyncio.run(main())
