# 🧪 Руководство по тестированию Universal Parser

## 📋 Обзор системы тестирования

Наша система тестирования обеспечивает **полное покрытие** всех компонентов платформы с **автоматизированным CI/CD** и **множественными уровнями проверок**.

## 🏗 Архитектура тестирования

### Уровни тестирования

```
📊 Покрытие тестами
├── 🔧 Unit Tests (80%+ покрытие)
│   ├── Database operations
│   ├── Business logic
│   ├── Utility functions
│   └── Individual components
├── 🔗 Integration Tests
│   ├── API integrations
│   ├── Database connections
│   ├── External services
│   └── End-to-end workflows
├── ⚡ Performance Tests
│   ├── Load testing
│   ├── Stress testing
│   ├── Memory usage
│   └── Response times
└── 🔒 Security Tests
    ├── Vulnerability scanning
    ├── Dependency checks
    ├── Code security analysis
    └── Penetration testing
```

## 🚀 Быстрый старт

### Локальное тестирование

```bash
# Установка зависимостей
make install

# Запуск всех тестов
make test-all

# Быстрые тесты (без медленных)
make test-fast

# Параллельное выполнение
make test-parallel
```

### Docker тестирование

```bash
# Все тесты в Docker
make test-docker-all

# Конкретные типы тестов
make test-docker-unit
make test-docker-integration
make test-docker-performance
```

## 📁 Структура тестов

```
tests/
├── test_database.py          # Тесты базы данных
├── test_alert_system.py      # Тесты системы алертов
├── test_analytics.py         # Тесты аналитики
├── test_subscription.py      # Тесты подписок
├── test_telegram_bot.py      # Тесты Telegram-бота
├── test_scheduler.py         # Тесты планировщика
├── test_parser.py            # Тесты парсера
├── test_performance.py       # Тесты производительности
└── conftest.py              # Общие фикстуры
```

## 🧪 Типы тестов

### 1. Unit Tests (Модульные тесты)

**Покрытие:** 80%+ кода

```python
# Пример unit теста
def test_add_tracked_item(self, test_user):
    """Тест добавления товара для отслеживания"""
    item = add_tracked_item(
        user_id=test_user.id,
        item_id="12345",
        marketplace="wb",
        name="Test Product"
    )
    
    assert item.user_id == test_user.id
    assert item.item_id == "12345"
    assert item.is_active is True
```

**Запуск:**
```bash
make test-unit
# или
python run_tests.py --type unit --coverage
```

### 2. Integration Tests (Интеграционные тесты)

**Покрытие:** API, база данных, внешние сервисы

```python
# Пример integration теста
@pytest.mark.integration
async def test_full_parsing_workflow(self, parser):
    """Тест полного рабочего процесса парсинга"""
    async with parser:
        results = await parser.parse_by_profile("test_profile")
        assert len(results) > 0
```

**Запуск:**
```bash
make test-integration
# или
python run_tests.py --type integration
```

### 3. Performance Tests (Тесты производительности)

**Покрытие:** Нагрузочное тестирование, память, время выполнения

```python
# Пример performance теста
@pytest.mark.slow
async def test_database_performance(self):
    """Тест производительности базы данных"""
    start_time = time.time()
    
    for i in range(100):
        add_tracked_item(user_id, f"item_{i}", "wb", f"Product {i}")
    
    duration = time.time() - start_time
    assert duration < 5.0  # 100 товаров за 5 секунд
```

**Запуск:**
```bash
make test-performance
# или
python run_tests.py --type performance
```

### 4. Security Tests (Тесты безопасности)

**Покрытие:** Уязвимости, зависимости, безопасность кода

```bash
# Проверка безопасности
make security-check

# В Docker
make test-docker-security
```

## 🔧 Конфигурация тестирования

### pytest.ini

```ini
[tool:pytest]
testpaths = tests
addopts = 
    -v
    --cov=.
    --cov-report=html
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    database: Tests requiring database
```

### pyproject.toml

```toml
[tool.coverage.run]
source = ["."]
omit = ["*/tests/*", "*/venv/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
]
```

## 🐳 Docker тестирование

### docker-compose.test.yml

```yaml
services:
  test-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: universal_parser_test
  
  test-runner:
    build:
      dockerfile: Dockerfile.test
    depends_on:
      test-db:
        condition: service_healthy
```

### Запуск в Docker

```bash
# Все тесты
docker-compose -f docker-compose.test.yml up --build

# Конкретный сервис
docker-compose -f docker-compose.test.yml up test-runner
```

## 🚀 CI/CD Pipeline

### GitHub Actions (.github/workflows/ci.yml)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest tests/ -v --cov=.
```

### Pre-commit hooks

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

## 📊 Метрики качества

### Покрытие кода

- **Минимальное покрытие:** 80%
- **Целевое покрытие:** 90%+
- **Критические модули:** 95%+

### Производительность

- **Unit тесты:** < 30 секунд
- **Integration тесты:** < 2 минуты
- **Performance тесты:** < 10 минут
- **Полный набор:** < 15 минут

### Безопасность

- **Уязвимости:** 0 критических
- **Зависимости:** Все актуальные
- **Код:** Безопасные паттерны

## 🛠 Инструменты тестирования

### Основные

- **pytest** - Фреймворк тестирования
- **pytest-cov** - Покрытие кода
- **pytest-asyncio** - Асинхронные тесты
- **pytest-mock** - Мокирование

### Качество кода

- **black** - Форматирование
- **isort** - Сортировка импортов
- **flake8** - Линтинг
- **mypy** - Проверка типов
- **pylint** - Анализ кода

### Безопасность

- **bandit** - Анализ безопасности
- **safety** - Проверка зависимостей
- **pre-commit** - Pre-commit hooks

### Производительность

- **locust** - Нагрузочное тестирование
- **psutil** - Мониторинг ресурсов
- **pytest-benchmark** - Бенчмарки

## 📈 Отчеты и мониторинг

### HTML отчеты

```bash
# Генерация HTML отчета
make test-all
# Отчет: htmlcov/index.html
```

### XML отчеты

```bash
# Для CI/CD
pytest --cov=.
# Файлы: coverage.xml, test-results.xml
```

### JSON отчеты

```bash
# Безопасность
bandit -r . -f json -o bandit-report.json
safety check --json --output safety-report.json
```

## 🔍 Отладка тестов

### Подробный вывод

```bash
# Максимальная детализация
pytest -vvv --tb=long

# Только упавшие тесты
pytest --lf

# Остановка на первой ошибке
pytest -x
```

### Профилирование

```bash
# Время выполнения
pytest --durations=10

# Покрытие по файлам
pytest --cov-report=term-missing
```

## 🚨 Устранение проблем

### Частые проблемы

1. **Тесты падают из-за БД**
   ```bash
   # Очистка тестовой БД
   make clean-tests
   python init_db.py
   ```

2. **Медленные тесты**
   ```bash
   # Пропуск медленных тестов
   make test-fast
   ```

3. **Проблемы с Docker**
   ```bash
   # Очистка Docker
   make clean-docker-tests
   ```

### Логи и отладка

```bash
# Логи Docker тестов
docker-compose -f docker-compose.test.yml logs test-runner

# Отладка конкретного теста
pytest tests/test_database.py::TestUserManagement::test_get_or_create_user_new -vvv
```

## 📚 Лучшие практики

### Написание тестов

1. **Именование:** `test_что_тестируем_при_каких_условиях`
2. **Изоляция:** Каждый тест независим
3. **Моки:** Используйте моки для внешних зависимостей
4. **Фикстуры:** Переиспользуйте общие настройки

### Структура теста

```python
def test_functionality(self):
    """Описание что тестируем"""
    # Arrange - подготовка данных
    user = create_test_user()
    
    # Act - выполнение действия
    result = function_under_test(user)
    
    # Assert - проверка результата
    assert result.status == "success"
    assert result.data is not None
```

### Мокирование

```python
@patch('module.external_function')
def test_with_mock(self, mock_external):
    """Тест с моком внешней функции"""
    mock_external.return_value = "mocked_value"
    
    result = function_that_uses_external()
    
    assert result == "expected_result"
    mock_external.assert_called_once()
```

## 🎯 Заключение

Наша система тестирования обеспечивает:

- ✅ **Полное покрытие** всех компонентов
- ✅ **Автоматизированное** выполнение
- ✅ **Множественные уровни** проверок
- ✅ **CI/CD интеграция**
- ✅ **Мониторинг качества**
- ✅ **Безопасность и производительность**

**Результат:** Высококачественная, надежная и безопасная платформа! 🚀
