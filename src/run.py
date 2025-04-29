import sys


from .exceptions import (
    LogFileError, LogProcessingError,
    MultipleFilesError
)
from .cli import CliParser
from .processors import LogProcessor
from .reports import HandlersReport


def main() -> int:
    """
    Точка входа в приложение.

    Returns:
        int: Код возврата (0 - успех, 1 - ошибка, 130 - прервано пользователем)
    """
    try:
        # Парсинг аргументов командной строки
        cli_parser = CliParser()
        args = cli_parser.parse()
        # Инициализация компонентов
        processor = LogProcessor()
        report_generator = HandlersReport()
        try:
            # Обработка логов
            log_statistics = processor.process_files(args.log_files)

            # Проверка наличия данных
            if not log_statistics:
                print("No logs found in the provided files", file=sys.stderr)
                return 1

            # Генерация отчета
            report = report_generator.generate(log_statistics)
            print(report)
            return 0

        except MultipleFilesError as e:
            print("Errors occurred while processing files:", file=sys.stderr)
            for path, error in e.failed_files:
                print(f"  {path}: {error}", file=sys.stderr)
            return 1
        except LogFileError as e:
            print(f"File error: {e}", file=sys.stderr)
            return 1
        except LogProcessingError as e:
            print(f"Processing error: {e}", file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
