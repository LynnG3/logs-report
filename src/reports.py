from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, List, NamedTuple


@dataclass
class DjangoReportData:
    """Базовая структура данных для хранения информации из логов.

    Attributes:
        handler_name: Название обработчика(ручки) API
        debug_count: Количество отладочных сообщений
        info_count: Количество информационных сообщений
        warning_count: Количество предупреждений
        error_count: Количество ошибок
        critical_count: Количество критических ошибок
    """
    STAT_FIELDS: ClassVar[List[str]] = [
        'debug_count',
        'info_count',
        'warning_count',
        'error_count',
        'critical_count'
    ]

    handler_name: str
    debug_count: int
    info_count: int
    warning_count: int
    error_count: int
    critical_count: int

    @classmethod
    def create_totals(
        cls,
        statistics: List['DjangoReportData']
    ) -> 'DjangoReportData':
        """Создает объект с суммарной статистикой.

        Args:
            statistics: Список объектов со статистикой

        Returns:
            ReportData: Объект с суммарной статистикой
        """
        return cls(
            handler_name="",
            **{
                field: sum(getattr(stat, field) for stat in statistics)
                for field in cls.STAT_FIELDS
            }
        )


class ColumnReportConfig(NamedTuple):
    """Конфигурация колонки отчета.

    Attributes:
        name: Название колонки в заголовке
        field: Имя поля в ReportData
        width: Ширина колонки для форматирования
    """
    name: str
    field: str
    width: int


class DjangoBaseReport(ABC):
    """Абстрактный базовый класс для отчетов по логам Django.

    Определяет общий интерфейс для генерации отчетов.
    """

    @property
    @abstractmethod
    def data_column_width(self) -> int:
        """Ширина колонки для данных."""
        pass

    @property
    @abstractmethod
    def identifier_column_width(self) -> int:
        """Ширина колонки для идентификатора записи."""
        pass

    @property
    @abstractmethod
    def no_data_message(self) -> str:
        """Сообщение при отсутствии данных."""
        pass

    @abstractmethod
    def generate(self, log_statistics: List[DjangoReportData]) -> str:
        """Генерирует отчет на основе полученных данных.

        Args:
            log_statistics: Список данных для формирования отчета

        Returns:
            str: Отформатированная строка с отчетом
        """
        pass


class HandlersReport(DjangoBaseReport):
    """
    Реализация отчета о состоянии обработчиков API.

    Формирует таблицу со статистикой по уровням логирования
    для каждой ручки.
    """

    @property
    def data_column_width(self) -> int:
        return 7

    @property
    def identifier_column_width(self) -> int:
        return 20

    @property
    def no_data_message(self) -> str:
        return "No data available for report."

    @property
    def identifier_config(self) -> ColumnReportConfig:
        """Конфигурация колонки с идентификатором записи."""
        return ColumnReportConfig(
            name="HANDLER",
            field="handler_name",
            width=self.identifier_column_width
        )

    @property
    def stat_columns(self) -> List[ColumnReportConfig]:
        """Список конфигураций колонок со статистикой."""
        return [
            ColumnReportConfig(
                "DEBUG", "debug_count", self.data_column_width
            ),
            ColumnReportConfig(
                "INFO", "info_count", self.data_column_width
            ),
            ColumnReportConfig(
                "WARNING", "warning_count", self.data_column_width
            ),
            ColumnReportConfig(
                "ERROR", "error_count", self.data_column_width
            ),
            ColumnReportConfig(
                "CRITICAL", "critical_count", self.data_column_width
            ),
        ]

    def generate(
        self,
        log_statistics: List[DjangoReportData]
    ) -> str:
        """Генерирует отчет о состоянии обработчиков.

        Args:
            log_statistics: Список данных по каждому обработчику

        Returns:
            str: Отформатированная таблица со статистикой

        """
        if not log_statistics:
            return self.no_data_message
        # Подготовака данных с сортировкой по имени ручек
        sorted_handlers = sorted(log_statistics, key=lambda x: x.handler_name)
        totals = DjangoReportData.create_totals(log_statistics)
        # Формирование отчета
        report_lines = [
            f"Total requests: {self._calculate_total(log_statistics)}\n",
            self._get_header(),
            *[
                self._format_handler_line(handler)
                for handler in sorted_handlers
            ],
            self._format_totals_line(totals)
        ]

        return "\n".join(report_lines)

    def _calculate_total(
        self,
        log_statistics: List[DjangoReportData]
    ) -> int:
        """Подсчитывает общее количество запросов.

        Args:
            log_statistics: Список статистики по обработчикам

        Returns:
            int: Общее количество запросов
        """
        return sum(
            sum(getattr(stat, field) for field in DjangoReportData.STAT_FIELDS)
            for stat in log_statistics
        )

    def _get_header(self) -> str:
        """Формирует заголовок таблицы.

        Returns:
            str: Отформатированная строка заголовка
        """
        columns = [
            f"{self.identifier_config.name:<{self.identifier_config.width}}",
            *(f"{col.name:<{col.width}}" for col in self.stat_columns)
        ]
        return "\t".join(columns)

    def _format_statistics(
        self,
        title: str,
        statistics: DjangoReportData
    ) -> str:
        """Форматирует строку статистики.

        Args:
            title: Название строки (имя ручки или пустая строка для итогов)
            statistics: Объект со статистикой

        Returns:
            str: Отформатированная строка статистики
        """
        columns = [
            f"{title:<{self.identifier_config.width}}",
            *(f"{getattr(statistics, col.field):<{col.width}}"
              for col in self.stat_columns)
        ]
        return "\t".join(columns)

    def _format_handler_line(
        self,
        handler: DjangoReportData
    ) -> str:
        """
        Форматирует строку статистики для одной ручки.

        Args:
            handler: Статистика ручки

        Returns:
            str: Отформатированная строка статистики
        """
        return self._format_statistics(handler.handler_name, handler)

    def _format_totals_line(
        self,
        totals: DjangoReportData
    ) -> str:
        """
        Форматирует итоговую строку статистики.

        Args:
            totals: Суммарная статистика

        Returns:
            str: Отформатированная строка с итогами
        """
        return self._format_statistics("", totals)
