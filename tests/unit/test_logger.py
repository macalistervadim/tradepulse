import pytest

from tradepulse.core.logger import EnvironmentType, setup_logging

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("env", ["dev", "test", "prod"])
def test_setup_logging_environments(env: EnvironmentType) -> None:
    """Проверка конфигурации structlog для всех окружений (dev, test, prod)."""
    setup_logging(env=env)
