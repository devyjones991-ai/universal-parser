# Universal Parser - Makefile

.PHONY: help install init test run clean docker-build docker-run docker-stop

# Цвета для вывода
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(GREEN)Universal Parser - Команды управления$(NC)"
	@echo ""
	@echo "$(YELLOW)Основные команды:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости
	@echo "$(GREEN)📦 Установка зависимостей...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Зависимости установлены$(NC)"

init: ## Инициализировать базу данных
	@echo "$(GREEN)🗄️ Инициализация базы данных...$(NC)"
	python init_db.py
	@echo "$(GREEN)✅ База данных инициализирована$(NC)"

test: ## Запустить тесты системы
	@echo "$(GREEN)🧪 Запуск тестов...$(NC)"
	python test_system.py
	@echo "$(GREEN)✅ Тесты завершены$(NC)"

run: ## Запустить приложение
	@echo "$(GREEN)🚀 Запуск Universal Parser...$(NC)"
	python main.py

clean: ## Очистить временные файлы
	@echo "$(YELLOW)🧹 Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache/
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

docker-build: ## Собрать Docker образ
	@echo "$(GREEN)🐳 Сборка Docker образа...$(NC)"
	docker build -t universal-parser .
	@echo "$(GREEN)✅ Docker образ собран$(NC)"

docker-run: ## Запустить в Docker
	@echo "$(GREEN)🐳 Запуск в Docker...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Приложение запущено в Docker$(NC)"

docker-stop: ## Остановить Docker контейнеры
	@echo "$(YELLOW)🛑 Остановка Docker контейнеров...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Docker контейнеры остановлены$(NC)"

docker-logs: ## Показать логи Docker
	@echo "$(GREEN)📋 Логи Docker контейнеров:$(NC)"
	docker-compose logs -f

setup: install init test ## Полная настройка системы
	@echo "$(GREEN)🎉 Система готова к работе!$(NC)"
	@echo "$(YELLOW)Для запуска используйте: make run$(NC)"

dev: ## Запуск в режиме разработки
	@echo "$(GREEN)🔧 Запуск в режиме разработки...$(NC)"
	export PYTHONPATH=.
	export DEBUG=true
	python main.py

backup: ## Создать резервную копию базы данных
	@echo "$(GREEN)💾 Создание резервной копии...$(NC)"
	@mkdir -p backups
	cp universal_parser.db backups/universal_parser_$(shell date +%Y%m%d_%H%M%S).db
	@echo "$(GREEN)✅ Резервная копия создана$(NC)"

restore: ## Восстановить из резервной копии
	@echo "$(YELLOW)⚠️ Восстановление из резервной копии...$(NC)"
	@ls -la backups/
	@echo "$(YELLOW)Выберите файл для восстановления:$(NC)"
	@read -p "Имя файла: " file; \
	if [ -f "backups/$$file" ]; then \
		cp "backups/$$file" universal_parser.db; \
		echo "$(GREEN)✅ База данных восстановлена$(NC)"; \
	else \
		echo "$(RED)❌ Файл не найден$(NC)"; \
	fi

status: ## Показать статус системы
	@echo "$(GREEN)📊 Статус системы Universal Parser$(NC)"
	@echo ""
	@echo "$(YELLOW)🐍 Python версия:$(NC)"
	@python --version
	@echo ""
	@echo "$(YELLOW)📦 Установленные пакеты:$(NC)"
	@pip list | grep -E "(aiogram|sqlalchemy|pandas|matplotlib)"
	@echo ""
	@echo "$(YELLOW)🗄️ База данных:$(NC)"
	@if [ -f "universal_parser.db" ]; then \
		echo "$(GREEN)✅ База данных существует$(NC)"; \
		ls -lh universal_parser.db; \
	else \
		echo "$(RED)❌ База данных не найдена$(NC)"; \
	fi
	@echo ""
	@echo "$(YELLOW)🐳 Docker статус:$(NC)"
	@docker-compose ps 2>/dev/null || echo "$(YELLOW)Docker не запущен$(NC)"
