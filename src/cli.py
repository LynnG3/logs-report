import argparse
from typing import List, Optional

from .validators import ReportValidator


class CliParser:
    """Парсер аргументов командной строки."""

    def __init__(self):
        """Инициализация парсера с настройкой параметров."""
        self.parser = self._create_parser()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Создает и настраивает парсер аргументов.

        Returns:
            argparse.ArgumentParser: Настроенный парсер
        """
        parser = argparse.ArgumentParser(
            description="Django logs analyzer",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
        Examples:
            %(prog)s logs/app1.log --report handlers
            %(prog)s logs/*.log --report handlers
            %(prog)s logs/app1.log logs/app2.log --report handlers
                    """
                )

        parser.add_argument(
            "log_files",
            nargs="+",
            type=str,
            help="Paths to log files to analyze"
        )

        parser.add_argument(
            "--report",
            "-r",
            required=True,
            choices=ReportValidator.AVAILABLE_REPORTS,
            help="Type of report to generate"
        )

        return parser

    def parse(self, args: Optional[List[str]] = None) -> argparse.Namespace:
        """Парсит аргументы командной строки.

        Args:
            args: Список аргументов (если None, берутся из sys.argv)

        Returns:
            argparse.Namespace: Объект с распарсенными аргументами
        """
        return self.parser.parse_args(args)
