# Настройка Git репозитория для Universal Parser
Write-Host "Настройка Git репозитория для Universal Parser..." -ForegroundColor Green

# Проверяем наличие Git
try {
    $gitVersion = git --version
    Write-Host "Git найден: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "ОШИБКА: Git не найден в PATH!" -ForegroundColor Red
    Write-Host "Попробуйте перезапустить PowerShell или добавить Git в PATH" -ForegroundColor Yellow
    exit 1
}

# Инициализация Git
Write-Host "Инициализация Git репозитория..." -ForegroundColor Yellow
git init

# Добавление файлов
Write-Host "Добавление файлов..." -ForegroundColor Yellow
git add .

# Первый коммит
Write-Host "Создание первого коммита..." -ForegroundColor Yellow
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

Write-Host ""
Write-Host "✅ Git репозиторий инициализирован!" -ForegroundColor Green
Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor Cyan
Write-Host "1. Создай репозиторий на GitHub: https://github.com/new" -ForegroundColor White
Write-Host "2. Название: universal-parser" -ForegroundColor White
Write-Host "3. НЕ добавляй README, .gitignore, лицензию" -ForegroundColor White
Write-Host "4. Выполни команды:" -ForegroundColor White
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/universal-parser.git" -ForegroundColor Gray
Write-Host "   git branch -M main" -ForegroundColor Gray
Write-Host "   git push -u origin main" -ForegroundColor Gray
Write-Host ""
Write-Host "Нажми любую клавишу для продолжения..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

