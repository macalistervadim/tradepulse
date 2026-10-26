import logging
import sys
from typing import Literal

import structlog
from structlog.types import Processor

EnvironmentType = Literal["dev", "test", "prod"]


def setup_logging(env: EnvironmentType = "dev") -> None:
    """Конфигурирует форматирование и уровень детализации логирования под конкретное окружение."""

    # Явно указываем общий тип процессора перед ветвлением
    renderer: Processor

    if env == "dev":
        log_level = logging.DEBUG
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    elif env == "test":
        log_level = logging.WARNING
        renderer = structlog.processors.KeyValueRenderer()
    else:  # prod
        log_level = logging.INFO
        renderer = structlog.processors.JSONRenderer()

    # Конфигурация конвейера structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
    )

    logging.basicConfig(level=log_level)


logger = structlog.get_logger()
