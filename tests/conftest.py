"""Общие фикстуры для всех тестов."""
from pathlib import Path
from typing import List

import pytest


# Общие фикстуры доступны во всех тестах
@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Путь к директории с тестовыми данными."""
    return Path(__file__).parent.parent / "django_logs"


@pytest.fixture(scope="session")
def real_log_files(test_data_dir: Path) -> List[Path]:
    """Получаем список реальных лог-файлов."""
    files = list(test_data_dir.glob("*.log"))
    assert files, f"No log files found in {test_data_dir}"
    return sorted(files)


@pytest.fixture(scope="session")
def sample_log_content(real_log_files: List[Path]) -> str:
    """Читаем содержимое реального лог-файла."""
    return real_log_files[0].read_text()
