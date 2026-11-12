# Загрузка переменных окружения из .env по умолчанию
set dotenv-load := true

# По умолчанию при вызове `just` без аргументов выводим список доступных команд
default:
    @just --list

# ==============================================================================
# 1. Запуск и локальная разработка
# ==============================================================================

# Запуск локального сервера разработки с горячей перезагрузкой
run:
    uv run uvicorn tradepulse.main:app --app-dir src --reload --host 0.0.0.0 --port 8000

# Открытие защищенного публичного туннеля через tuna
tunnel port="8000":
    tuna http {{port}}

# ==============================================================================
# 2. Контроль качества кода (Quality Gate)
# ==============================================================================

# Комплексная проверка: сортировка импортов, линтинг и строгая типизация
check: lint typecheck

# Быстрая проверка линтером Ruff
lint:
    uv run ruff check .

# Автоматическое исправление ошибок линтера и форматирование кода
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Строгая статическая верификация типов через Mypy
typecheck:
    uv run mypy src

# ==============================================================================
# 3. Управление контейнерами Docker Compose
# ==============================================================================

# Запуск окружения разработки (api-dev + mailpit)
dev-up:
    docker compose --profile dev up -d

# Остановка всех запущенных сервисов Compose
dev-down:
    docker compose down

# Просмотр логов контейнеров в реальном времени
logs:
    docker compose logs -f

# Пересборка боевого образа приложения без кэша
build-prod:
    docker build --no-cache -t tradepulse-api:latest .

# ==============================================================================
# 4. Обслуживание зависимостей и окружения
# ==============================================================================

# Полная синхронизация виртуального окружения по lock-файлу
sync:
    uv sync

# Очистка временных файлов кэша Python и сборщиков
clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache build dist htmlcov
    find . -type d -name "__pycache__" -exec rm -rf {} +

# ==============================================================================
# 5. Управление миграциями базы данных (Alembic)
# ==============================================================================

# Создание новой ревизии на основе изменений в моделях
migrate-make message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Применение всех непримененных миграций к БД
migrate:
    uv run alembic upgrade head

# Откат последней примененной миграции
migrate-rollback:
    uv run alembic downgrade -1

# Просмотр текущей версии схемы в базе данных
migrate-current:
    uv run alembic current
    
# ==============================================================================
# 6. Автоматизированное тестирование (Pytest + Docker Test Profile)
# ==============================================================================

# Поднять изолированную тестовую БД и дождаться её полной готовности
test-db-up:
    docker compose --profile test up postgres-test -d --wait

# Остановить и удалить временную тестовую БД (очистка RAM/tmpfs)
test-db-down:
    docker compose --profile test down -v

# Полный цикл: поднять тестовую БД -> запустить тесты -> гарантированно погасить БД
test *args:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'docker compose --profile test down -v > /dev/null 2>&1 || true' EXIT
    docker compose --profile test up postgres-test -d --wait
    uv run pytest {{args}}

# Быстрый запуск тестов при уже поднятой тестовой БД (поддерживает передачу путей и флагов)
test-fast *args:
    uv run pytest {{args}}

# Запуск только быстрых модульных тестов без поднятия Docker
test-unit *args:
    uv run pytest -m unit {{args}}

# Полный прогон тестов с расчетом покрытия кода (coverage.py) и отчетом в терминале
test-cov:
    #!/usr/bin/env bash
    set -euo pipefail
    trap 'docker compose --profile test down -v > /dev/null 2>&1 || true' EXIT
    docker compose --profile test up postgres-test -d --wait
    uv run pytest --cov=src/tradepulse --cov-report=term-missing --cov-report=html

# ==============================================================================
# 7. Единый конвейер контроля качества (Quality Gate)
# ==============================================================================

# Комплексная проверка перед коммитом: линтер, строгая типизация и все тесты
qa: check test
