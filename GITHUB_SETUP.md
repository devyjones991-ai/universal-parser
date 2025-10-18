# 🐙 Настройка GitHub репозитория

## Шаги для создания репозитория:

### 1. Создай репозиторий на GitHub
1. Перейди на https://github.com
2. Нажми "New repository"
3. Название: `universal-parser`
4. Описание: `Universal Parser - Marketplace monitoring platform`
5. Выбери "Public" или "Private"
6. НЕ добавляй README, .gitignore, лицензию (у нас уже есть)
7. Нажми "Create repository"

### 2. Команды для загрузки кода:

```bash
# В директории D:\universal-parser выполни:

# Инициализация Git (если еще не сделано)
git init

# Добавление всех файлов
git add .

# Первый коммит
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

# Добавление удаленного репозитория (замени YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/universal-parser.git

# Переименование основной ветки в main
git branch -M main

# Загрузка кода на GitHub
git push -u origin main
```

### 3. Настройка на сервере:

```bash
# На сервере выполни:

# Клонирование репозитория
git clone https://github.com/YOUR_USERNAME/universal-parser.git
cd universal-parser

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Установка Playwright браузеров
playwright install chromium

# Создание .env файла
cat > .env << EOF
TELEGRAM_BOT_TOKEN=7716605466:AAEUUkpbtqdGl8rX8imGnkr4Dr-sTQFOUec
TELEGRAM_CHAT_ID=0
ADMIN_CHAT_IDS=[]
DATABASE_URL=sqlite:///universal_parser.db
DEFAULT_TIMEOUT=15
MAX_CONCURRENT_REQUESTS=10
USE_PROXY=false
PROXY_URL=
EXPORT_FORMAT=json
MAX_RESULTS_PER_MESSAGE=50
DEBUG=false
LOG_LEVEL=INFO
EOF

# Инициализация базы данных
python -c "from db import init_db; init_db(); print('База данных инициализирована')"

# Тестирование
python test_parser.py

# Запуск
python main.py
```

### 4. Настройка автоматического обновления:

```bash
# Создание скрипта обновления
cat > update.sh << 'EOF'
#!/bin/bash
cd /home/devyjones/universal-parser
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart universal-parser
echo "Обновление завершено"
EOF

chmod +x update.sh
```

### 5. Создание релизов:

```bash
# Создание тега для версии
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0

# На GitHub:
# 1. Перейди в раздел "Releases"
# 2. Нажми "Create a new release"
# 3. Выбери тег v0.1.0
# 4. Заголовок: "Universal Parser v0.1.0"
# 5. Описание: скопируй из CHANGELOG.md
# 6. Нажми "Publish release"
```

## 🔄 Workflow для обновлений:

1. **Локальная разработка** → коммиты → push
2. **На сервере**: `./update.sh` для обновления
3. **Новая версия**: обновить версию → тег → релиз

## 📝 Полезные команды Git:

```bash
# Проверка статуса
git status

# Просмотр изменений
git diff

# Отмена изменений
git checkout -- filename

# Создание ветки для новой функции
git checkout -b feature/new-feature

# Слияние веток
git checkout main
git merge feature/new-feature

# Удаление ветки
git branch -d feature/new-feature
```


