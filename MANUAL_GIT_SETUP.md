# 🐙 Ручная настройка GitHub (без Git)

## Вариант 1: Установка Git (рекомендуется)

1. **Скачай Git для Windows**: https://git-scm.com/download/win
2. **Установи** с настройками по умолчанию
3. **Перезапусти** PowerShell/CMD
4. **Запусти** `setup_git.bat`

## Вариант 2: Загрузка через веб-интерфейс GitHub

### Шаг 1: Создай репозиторий на GitHub
1. Перейди на https://github.com
2. Нажми "New repository"
3. Название: `universal-parser`
4. Описание: `Universal Parser - Marketplace monitoring platform`
5. Выбери "Public" или "Private"
6. НЕ добавляй README, .gitignore, лицензию
7. Нажми "Create repository"

### Шаг 2: Загрузи файлы через веб-интерфейс
1. На странице репозитория нажми "uploading an existing file"
2. Перетащи все файлы из папки `D:\universal-parser\` в браузер
3. Добавь коммит сообщение: `feat: initial release v0.1.0`
4. Нажми "Commit changes"

### Шаг 3: Настройка на сервере

```bash
# На сервере выполни:

# 1. Клонирование репозитория
git clone https://github.com/YOUR_USERNAME/universal-parser.git
cd universal-parser

# 2. Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Установка Playwright браузеров
playwright install chromium

# 5. Создание .env файла
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

# 6. Инициализация базы данных
python -c "from db import init_db; init_db(); print('База данных инициализирована')"

# 7. Тестирование
python test_parser.py

# 8. Запуск
python main.py
```

## Вариант 3: Через GitHub Desktop

1. **Скачай GitHub Desktop**: https://desktop.github.com/
2. **Установи** и авторизуйся
3. **Создай** репозиторий через веб-интерфейс GitHub
4. **Клонируй** репозиторий через GitHub Desktop
5. **Скопируй** все файлы в папку репозитория
6. **Сделай** коммит и push

## 🚀 После загрузки на GitHub

### На сервере выполни:

```bash
# 1. Подключись к серверу
ssh -p 2222 devyjones@77.51.225.141

# 2. Клонируй репозиторий
git clone https://github.com/YOUR_USERNAME/universal-parser.git
cd universal-parser

# 3. Следуй инструкции из DEPLOYMENT.md
```

## 📝 Полезные ссылки

- **Git для Windows**: https://git-scm.com/download/win
- **GitHub Desktop**: https://desktop.github.com/
- **Создание репозитория**: https://github.com/new
- **Документация Git**: https://git-scm.com/doc

## 🔄 Обновление проекта

После изменений в коде:
1. **Загрузи** изменения на GitHub (через веб-интерфейс или Git)
2. **На сервере**: `git pull origin main`
3. **Перезапусти** сервис: `sudo systemctl restart universal-parser`


