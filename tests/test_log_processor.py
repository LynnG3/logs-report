import pytest
from pathlib import Path
from typing import List

from src.processors import LogParser, LogProcessor
from src.exceptions import LogFileError
from src.reports import DjangoReportData

@pytest.fixture
def log_parser() -> LogParser:
    """Инициализированный парсер логов."""
    return LogParser()

@pytest.fixture
def log_processor() -> LogProcessor:
    """Процессор логов для тестов без multiprocessing."""
    return LogProcessor(use_multiprocessing=False)


class TestLogParser:
    """Тесты парсера логов."""
    
    def test_parse_real_logs(
        self,
        log_parser: LogParser,
        sample_log_content: str
    ):
        """Тест парсинга реальных логов."""
        parsed_entries = []
        for line in sample_log_content.splitlines():
            result = log_parser.parse_log_line(line)
            if result:
                parsed_entries.append(result)
        
        assert parsed_entries, "Should parse at least some log entries"
        first_entry = parsed_entries[0]
        assert all(key in first_entry for key in ['timestamp', 'level', 'component'])
        
        request_entries = [
            entry for entry in parsed_entries 
            if entry['component'] == 'django.request'
        ]
        assert any('handler' in entry for entry in request_entries)

    def test_parse_invalid_log(self, log_parser: LogParser):
        """Тест парсинга невалидной строки лога."""
        invalid_lines = [
            "Not a log line at all",
            "2024-03-28 Invalid format",
            "",  # пустая строка
            "2024-03-28 10:15:30,123 INVALID django.request: GET /api/users/"
        ]
        for line in invalid_lines:
            result = log_parser.parse_log_line(line)
            assert result is None, f"Should return None for invalid line: {line}"

class TestLogProcessor:
    """Тесты процессора логов."""
    
    def test_process_real_files(
        self,
        log_processor: LogProcessor,
        real_log_files: List[Path]
    ):
        """Тест обработки реальных лог-файлов."""
        results = log_processor.process_files([str(p) for p in real_log_files])
        
        assert isinstance(results, list)
        assert results, "Should produce non-empty results"
        assert all(isinstance(r, DjangoReportData) for r in results)
        
        total_requests = sum(
            r.info_count + r.error_count + r.warning_count + r.debug_count
            for r in results
        )
        assert total_requests > 0, "Should find some requests"

    def test_process_nonexistent_file(self, log_processor: LogProcessor):
        """Тест обработки несуществующего файла."""
        with pytest.raises(LogFileError):
            log_processor.process_files(["nonexistent.log"])