# 🚀 Быстрый старт Universal Parser v0.1.0

## 📋 Что нужно сделать:

### 1. Создай репозиторий на GitHub
- Перейди на https://github.com/new
- Название: `universal-parser`
- Описание: `Universal Parser - Marketplace monitoring platform`
- НЕ добавляй README, .gitignore, лицензию
- Создай репозиторий

### 2. Загрузи код на GitHub
**Вариант A: Установи Git (рекомендуется)**
1. Скачай Git: https://git-scm.com/download/win
2. Установи и перезапусти PowerShell
3. Выполни: `setup_git.bat`

**Вариант B: Через веб-интерфейс**
1. На странице репозитория нажми "uploading an existing file"
2. Перетащи все файлы из `D:\universal-parser\`
3. Коммит: `feat: initial release v0.1.0`

### 3. Настрой на сервере
```bash
# Подключись к серверу
ssh -p 2222 devyjones@77.51.225.141

# Клонируй репозиторий
git clone https://github.com/YOUR_USERNAME/universal-parser.git
cd universal-parser

# Установи зависимости
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Настрой .env файл
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

# Инициализируй БД
python -c "from db import init_db; init_db(); print('База данных инициализирована')"

# Протестируй
python test_parser.py

# Запусти
python main.py
```

## ✅ Готово!

Твой Universal Parser v0.1.0 запущен! 🎉

## 📞 Если что-то не работает:

1. **Проверь логи**: `python main.py` (в консоли)
2. **Запусти тесты**: `python test_parser.py`
3. **Проверь .env**: `cat .env`
4. **Проверь зависимости**: `pip list`

## 🔄 Обновление:

```bash
# На сервере
cd universal-parser
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---
**Версия**: 0.1.0  
**Дата**: 2025-01-18


