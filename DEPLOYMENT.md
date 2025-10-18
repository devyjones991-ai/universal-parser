# 🚀 Инструкция по развертыванию Universal Parser

## Версия: 0.1.0

### 📋 Требования к серверу

- **OS**: Ubuntu 20.04+ / Debian 10+
- **Python**: 3.9+
- **RAM**: минимум 1GB (рекомендуется 2GB+)
- **Диск**: минимум 2GB свободного места
- **Порты**: 22 (SSH), 80 (HTTP, опционально)

### 🔧 Подготовка сервера

```bash
# 1. Обновляем систему
sudo apt update && sudo apt upgrade -y

# 2. Устанавливаем Python и зависимости
sudo apt install python3 python3-pip python3-venv git curl wget -y

# 3. Устанавливаем системные зависимости для парсинга
sudo apt install build-essential libxml2-dev libxslt-dev libffi-dev libssl-dev -y

# 4. Создаем пользователя для приложения (если нужно)
sudo useradd -m -s /bin/bash parser
sudo usermod -aG sudo parser
```

### 📦 Установка приложения

```bash
# 1. Переходим в домашнюю директорию
cd /home/devyjones

# 2. Создаем директорию для проекта
mkdir -p universal-parser
cd universal-parser

# 3. Загружаем архив (замените на ваш способ загрузки)
# Вариант A: Через SCP
# scp -P 2222 D:\universal-parser-v0.1.0.zip devyjones@77.51.225.141:/home/devyjones/universal-parser/

# Вариант B: Через wget (если загрузили на файлообменник)
# wget https://example.com/universal-parser-v0.1.0.zip

# 4. Распаковываем архив
unzip universal-parser-v0.1.0.zip

# 5. Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# 6. Обновляем pip
pip install --upgrade pip

# 7. Устанавливаем зависимости
pip install -r requirements.txt

# 8. Устанавливаем Playwright браузеры
playwright install chromium
```

### ⚙️ Настройка конфигурации

```bash
# 1. Создаем .env файл
cat > .env << EOF
# Telegram Bot
TELEGRAM_BOT_TOKEN=7716605466:AAEUUkpbtqdGl8rX8imGnkr4Dr-sTQFOUec
TELEGRAM_CHAT_ID=0
ADMIN_CHAT_IDS=[]

# База данных
DATABASE_URL=sqlite:///universal_parser.db

# Настройки парсинга
DEFAULT_TIMEOUT=15
MAX_CONCURRENT_REQUESTS=10
USE_PROXY=false
PROXY_URL=

# Настройки экспорта
EXPORT_FORMAT=json
MAX_RESULTS_PER_MESSAGE=50

# Настройки сервера
DEBUG=false
LOG_LEVEL=INFO
EOF

# 2. Создаем директории для данных
mkdir -p data logs

# 3. Устанавливаем права доступа
chmod 755 data logs
```

### 🗄️ Инициализация базы данных

```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Инициализируем базу данных
python -c "from db import init_db; init_db(); print('База данных инициализирована')"
```

### 🧪 Тестирование

```bash
# Запускаем тесты
python test_parser.py

# Должно показать:
# ✅ Простое парсинг: OK
# ✅ Wildberries: OK
# ✅ Все тесты прошли успешно!
```

### 🚀 Запуск приложения

#### Вариант 1: Прямой запуск
```bash
# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем приложение
python main.py
```

#### Вариант 2: Systemd сервис (рекомендуется)
```bash
# 1. Создаем сервис файл
sudo tee /etc/systemd/system/universal-parser.service > /dev/null << EOF
[Unit]
Description=Universal Parser Bot
After=network.target

[Service]
Type=simple
User=devyjones
WorkingDirectory=/home/devyjones/universal-parser
Environment=PATH=/home/devyjones/universal-parser/venv/bin
ExecStart=/home/devyjones/universal-parser/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 2. Перезагружаем systemd
sudo systemctl daemon-reload

# 3. Включаем автозапуск
sudo systemctl enable universal-parser

# 4. Запускаем сервис
sudo systemctl start universal-parser

# 5. Проверяем статус
sudo systemctl status universal-parser
```

### 📊 Мониторинг

```bash
# Просмотр логов
sudo journalctl -u universal-parser -f

# Проверка статуса
sudo systemctl status universal-parser

# Перезапуск сервиса
sudo systemctl restart universal-parser

# Остановка сервиса
sudo systemctl stop universal-parser
```

### 🔄 Обновление приложения

```bash
# 1. Останавливаем сервис
sudo systemctl stop universal-parser

# 2. Создаем бэкап
cp -r /home/devyjones/universal-parser /home/devyjones/universal-parser-backup-$(date +%Y%m%d)

# 3. Загружаем новую версию
# (замените на ваш способ обновления)

# 4. Обновляем зависимости
source venv/bin/activate
pip install -r requirements.txt

# 5. Запускаем сервис
sudo systemctl start universal-parser
```

### 🛠️ Устранение неполадок

#### Проблема: Сервис не запускается
```bash
# Проверяем логи
sudo journalctl -u universal-parser -n 50

# Проверяем права доступа
ls -la /home/devyjones/universal-parser/

# Проверяем Python
/home/devyjones/universal-parser/venv/bin/python --version
```

#### Проблема: Ошибки парсинга
```bash
# Проверяем интернет соединение
curl -I https://example.com

# Проверяем DNS
nslookup search.wb.ru

# Тестируем парсинг
cd /home/devyjones/universal-parser
source venv/bin/activate
python test_parser.py
```

### 📞 Поддержка

При возникновении проблем:
1. Проверьте логи: `sudo journalctl -u universal-parser -f`
2. Запустите тесты: `python test_parser.py`
3. Проверьте конфигурацию: `cat .env`

---

**Версия документации**: 0.1.0  
**Дата обновления**: 2025-01-18


