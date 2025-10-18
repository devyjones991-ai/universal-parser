@echo off
echo Настройка Git репозитория для Universal Parser...

REM Проверяем наличие Git
git --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Git не установлен!
    echo Скачайте Git с https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Инициализация Git
echo Инициализация Git репозитория...
git init

REM Добавление файлов
echo Добавление файлов...
git add .

REM Первый коммит
echo Создание первого коммита...
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

echo.
echo ✅ Git репозиторий инициализирован!
echo.
echo Следующие шаги:
echo 1. Создай репозиторий на GitHub: https://github.com/new
echo 2. Название: universal-parser
echo 3. НЕ добавляй README, .gitignore, лицензию
echo 4. Выполни команды:
echo    git remote add origin https://github.com/YOUR_USERNAME/universal-parser.git
echo    git branch -M main
echo    git push -u origin main
echo.
pause


