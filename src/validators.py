from typing import List


class ReportValidator:
    """Валидатор для проверки имени отчета."""

    AVAILABLE_REPORTS: List[str] = ['handlers']

    @classmethod
    def is_valid_report_name(cls, report_name: str) -> bool:
        """Проверяет корректность имени отчета.

        Args:
            report_name: Имя отчета для проверки

        Returns:
            bool: True если имя отчета корректно, иначе False
        """
        return report_name in cls.AVAILABLE_REPORTS
