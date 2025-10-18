# 🐙 Команды Git для настройки репозитория

## Выполни эти команды в PowerShell:

### 1. Инициализация Git
```powershell
git init
```

### 2. Добавление файлов
```powershell
git add .
```

### 3. Первый коммит
```powershell
git commit -m "feat: initial release v0.1.0

- Базовая архитектура Universal Parser
- Система парсинга с поддержкой HTML, API и динамического контента
- Модели базы данных для пользователей, товаров, алертов
- Telegram Bot с полным функционалом
- Система алертов и уведомлений
- Аналитика и отчеты с графиками
- Система подписок (Free/Premium/Enterprise)
- Docker контейнеризация
- Профили парсинга для Wildberries, Ozon, Яндекс.Маркет"
```

### 4. Создай репозиторий на GitHub
1. Перейди на https://github.com/new
2. Название: `universal-parser`
3. Описание: `Universal Parser - Marketplace monitoring platform`
4. НЕ добавляй README, .gitignore, лицензию
5. Создай репозиторий

### 5. Подключение к GitHub
```powershell
# Замени YOUR_USERNAME на свой GitHub username
git remote add origin https://github.com/YOUR_USERNAME/universal-parser.git
git branch -M main
git push -u origin main
```

## 🚀 После загрузки на GitHub

### На сервере выполни:
```bash
# 1. Подключись к серверу
ssh -p 2222 devyjones@77.51.225.141

# 2. Клонируй репозиторий
git clone https://github.com/YOUR_USERNAME/universal-parser.git
cd universal-parser

# 3. Следуй инструкции из QUICK_START.md
```

## 🔄 Обновление проекта

После изменений в коде:
```powershell
git add .
git commit -m "описание изменений"
git push origin main
```

На сервере:
```bash
git pull origin main
```

