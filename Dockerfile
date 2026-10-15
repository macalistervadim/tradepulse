# 1. Базовый образ
FROM python:3.13-slim

# 2. Копирование скомпилированного бинарника uv из официального образа Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Настройка параметров окружения Python и uv
# UV_COMPILE_BYTECODE: компилирует .py в байт-код при установке (ускоряет холодный старт FastAPI)
# UV_LINK_MODE=copy: заставляет uv копировать файлы вместо жестких ссылок (важно для файловых систем контейнеров)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    APP_HOME=/app

WORKDIR $APP_HOME

# 4. Установка сторонних зависимостей с кэшированием слоев
# Копируем манифесты отдельно, чтобы не сбрасывать кэш пакетов при изменении бизнес-логики
COPY pyproject.toml uv.lock ./

# Устанавливаем только продакшен-зависимости (без pytest, ruff и dev-инструментов)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# 5. Создание непривилегированного пользователя в целях безопасности
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser $APP_HOME

# 6. Копирование исходного кода сервиса и финальная установка
COPY ./src ./src
COPY README.md ./

# Регистрируем сам проект в окружении (синхронизация метаданных и консольных скриптов)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Добавляем созданное окружение uv в переменную PATH
ENV PATH="$APP_HOME/.venv/bin:$PATH"

# 7. Права доступа и команда запуска
USER appuser
EXPOSE 8000

# Запуск ASGI-сервера Uvicorn
CMD ["uvicorn", "tradepulse.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
