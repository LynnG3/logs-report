"""Исключения для приложения."""
from typing import List


class LogProcessingError(Exception):
    """Базовое исключение для ошибок обработки логов."""

    pass


class LogFileError(LogProcessingError):
    """Ошибка при работе с файлом лога."""

    def __init__(self, file_path: str, message: str):
        self.file_path = file_path
        self.message = message
        super().__init__(
            f"Error processing file {file_path}: {message}"
        )


class MultipleFilesError(LogProcessingError):
    """Ошибка при обработке нескольких файлов."""
    def __init__(self, failed_files: List[tuple[str, Exception]]):
        self.failed_files = failed_files
        messages = [f"{path}: {err}" for path, err in failed_files]
        super().__init__(
            "Errors in multiple files:\n" + "\n".join(messages)
        )
