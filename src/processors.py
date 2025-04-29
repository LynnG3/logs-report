import multiprocessing as mp
import re
from enum import Enum
from collections import defaultdict
from pathlib import Path
from typing import Dict, Generator, List, Optional

from .exceptions import (
    LogFileError, LogProcessingError,
    MultipleFilesError
)
from .reports import DjangoReportData


class DjangoLogComponent(Enum):
    """Компоненты логов Django."""
    REQUEST = 'django.request'
    SECURITY = 'django.security'
    CORE = 'django.core.management'
    DB = 'django.db.backends'


class LogParser:
    """Парсер логов Django."""

    # Базовый паттерн для всех логов Django
    BASE_PATTERN = re.compile(
        r'''
        (?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d{3})\s+
        (?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+
        (?P<component>django\.\w+(?:\.\w+)*):
        \s+(?P<message>.+)
        ''',
        re.VERBOSE
    )

    # Паттерн для извлечения URL из request логов
    REQUEST_PATTERN = re.compile(
        r'''
        (?:GET|POST|PUT|DELETE|PATCH)\s+(?P<handler>/[^\s]+)|
        Error:\s+(?P<error_handler>/[^\s]+)
        ''',
        re.VERBOSE
    )

    @classmethod
    def parse_log_line(cls, line: str) -> Optional[dict]:
        """Парсит строку лога.

        Args:
            line: Строка лога

        Returns:
            dict: Распарсенные данные или None если строка не распознана
        """
        base_match = cls.BASE_PATTERN.match(line)
        if not base_match:
            return None

        data = base_match.groupdict()

        if data['component'] == DjangoLogComponent.REQUEST.value:
            request_match = cls.REQUEST_PATTERN.search(data['message'])
            if request_match:
                handler = (
                    request_match.group('handler')
                    or request_match.group('error_handler')
                )
                if handler:
                    data['handler'] = handler

        return data


class LogProcessor:
    """Процессор для обработки лог-файлов Django."""

    def __init__(
        self,
        num_workers: int = None,
        use_multiprocessing: bool = True
    ):
        """Инициализация процессора.

        Args:
            num_workers: Количество процессов для параллельной обработки
            (по умолчанию равно количеству CPU)
            use_multiprocessing: Использовать ли многопроцессорную обработку
            parser: парсер логов
        """
        self.num_workers = num_workers or mp.cpu_count()
        self.use_multiprocessing = use_multiprocessing
        self.parser = LogParser()

    def process_files(self, file_paths: List[str]) -> List[DjangoReportData]:
        """Параллельная обработка нескольких лог-файлов.

        Args:
            file_paths: Список путей к лог-файлам

        Returns:
            List[DjangoReportData]: Список агрегированных данных по ручкам

        Raises:
            LogFileError: Если возникла ошибка при работе с файлом
            LogProcessingError: Если возникла другая ошибка при обработке
        """
        try:
            if self.use_multiprocessing:
                with mp.Pool(self.num_workers) as pool:
                    results = pool.map(self._process_single_file, file_paths)
            else:
                results = [
                    self._process_single_file(path) for path in file_paths
                ]
            return self._merge_results(results)
        except LogFileError:
            raise
        except Exception as e:
            raise LogProcessingError(
                f"Error processing log files: {str(e)}"
            ) from e

    def _process_single_file(
        self,
        file_path: str
    ) -> Dict[str, Dict[str, int]]:
        """Обработка одного лог-файла.

        Args:
            file_path: Путь к файлу

        Returns:
            Dict: Словарь со статистикой по обработчикам
        """
        handlers_data = defaultdict(lambda: defaultdict(int))

        for line in self._read_logs(file_path):
            log_data = self.parser.parse_log_line(line)
            if not log_data:
                continue

            # Обрабатываем только request логи
            if (
                log_data['component'] == DjangoLogComponent.REQUEST.value
                and 'handler' in log_data
            ):
                handlers_data[log_data['handler']][
                    f"{log_data['level'].lower()}_count"
                ] += 1

        return dict(handlers_data)

    def _read_logs(self, file_path: str) -> Generator[str, None, None]:
        """Построчное чтение лог-файла.

        Args:
            file_path: Путь к файлу

        Yields:
            str: Строка лога

        Raises:
            ValueError: Если возникла ошибка при чтении файла
        """
        try:
            with Path(file_path).open('r', encoding='utf-8') as f:
                yield from f
        except OSError as e:
            raise LogFileError(file_path, str(e)) from e
        except Exception as e:
            raise LogProcessingError(
                f"Unexpected error reading file {file_path}: {str(e)}"
            ) from e

    def _merge_results(
        self,
        partial_results: List[Dict[str, Dict[str, int]]]
    ) -> List[DjangoReportData]:
        """Объединение результатов из всех обработанных файлов.

        Args:
            partial_results: Список результатов по каждому файлу

        Returns:
            List[DjangoReportData]: Список объектов с общей статистикой
        """
        merged_data = defaultdict(lambda: defaultdict(int))

        # Суммируем данные по всем файлам
        for result in partial_results:
            for handler, levels in result.items():
                for level, count in levels.items():
                    merged_data[handler][level] += count

        # Преобразуем в список DjangoReportData
        return [
            DjangoReportData(
                handler_name=handler,
                debug_count=levels.get('debug_count', 0),
                info_count=levels.get('info_count', 0),
                warning_count=levels.get('warning_count', 0),
                error_count=levels.get('error_count', 0),
                critical_count=levels.get('critical_count', 0)
            )
            for handler, levels in sorted(merged_data.items())
        ]
