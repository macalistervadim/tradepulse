import logging
import sys
from typing import Literal

import structlog

# Допустимые типы сред развертывания
EnvironmentType = Literal["dev", "test", "prod"]


def setup_logging(env: EnvironmentType = "dev") -> None:
    """Конфигурирует форматирование и уровень детализации логирования под конкретное окружение."""

    # 1. Сегментация уровня важности и процессоров форматирования
    if env == "dev":
        log_level = logging.DEBUG
        # Цветной консольный вывод для локальной отладки разработчиком
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    elif env == "test":
        log_level = logging.WARNING
        # Минималистичный текстовый формат key=value для подавления шума в тестах
        renderer = structlog.processors.KeyValueRenderer()
    else:  # prod
        log_level = logging.INFO
        # Машиночитаемый JSON для серверных сборщиков логов
        renderer = structlog.processors.JSONRenderer()

    # 2. Инициализация конвейера обработки structlog
    structlog.configure(
        processors=[
            # Фиксация уровня записи (debug, info, warning, error)
            structlog.stdlib.add_log_level,
            # Добавление временного штампа события в стандарте ISO-8601
            structlog.processors.TimeStamper(fmt="iso"),
            # Формирование итоговой структуры записи
            renderer,
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )

    # 3. Базовая настройка стандартной библиотеки logging
    logging.basicConfig(level=log_level)


# Экземпляр логгера для импорта в модули бизнес-логики и роутеры
logger = structlog.get_logger()
