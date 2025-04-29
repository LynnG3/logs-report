"""Тесты для Cli и точки входа в приложение."""
import sys
from pathlib import Path
from typing import List

import pytest
from src.cli import CliParser
from src.exceptions import (
    LogProcessingError,
    MultipleFilesError
)
import main


class TestCliParser:
    """Тесты парсера командной строки."""
    
    def test_cli_parser_valid_args(self, test_data_dir: Path):
        """Тест парсинга валидных аргументов командной строки."""
        parser = CliParser()
        args = parser.parse([
            str(test_data_dir / "app1.log"),
            str(test_data_dir / "app2.log"),
            "--report",
            "handlers"
        ])
        
        assert len(args.log_files) == 2
        assert args.report == "handlers"

    def test_cli_parser_missing_report(self, test_data_dir: Path):
        """Тест отсутствия обязательного аргумента --report."""
        parser = CliParser()
        with pytest.raises(SystemExit):
            parser.parse([str(test_data_dir / "app1.log")])

    def test_cli_parser_invalid_report(self, test_data_dir: Path):
        """Тест невалидного значения аргумента --report."""
        parser = CliParser()
        with pytest.raises(SystemExit):
            parser.parse([
                str(test_data_dir / "app1.log"),
                "--report",
                "invalid_report"
            ])


class TestMain:
    """Тесты основной точки входа программы."""
    
    def test_main_success(self, capsys, real_log_files: List[Path]):
        """Тест успешного выполнения программы."""
        original_argv = sys.argv.copy()
        try:
            sys.argv = [
                "main.py",
                *[str(p) for p in real_log_files],
                "--report",
                "handlers"
            ]
            exit_code = main.main()
            captured = capsys.readouterr()
            
            assert exit_code == 0
            assert "Total requests:" in captured.out
            assert not captured.err
        finally:
            sys.argv = original_argv

    def test_main_no_logs_found(self, capsys, test_data_dir: Path):
        """Тест когда в логах нет записей."""
        # Создаем пустой лог-файл
        empty_log = test_data_dir / "empty.log"
        empty_log.write_text("")
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = [
                "main.py",
                str(empty_log),
                "--report",
                "handlers"
            ]
            exit_code = main.main()
            captured = capsys.readouterr()
            
            assert exit_code == 1
            assert "No logs found" in captured.err
        finally:
            sys.argv = original_argv
            empty_log.unlink()

    def test_main_log_processing_error(self, capsys, monkeypatch):
        """Тест ошибки обработки логов."""
        def mock_process_files(*args):
            raise LogProcessingError("Test processing error")
        
        monkeypatch.setattr(
            'src.processors.LogProcessor.process_files',
            mock_process_files
        )
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = [
                "main.py",
                "test.log",
                "--report",
                "handlers"
            ]
            exit_code = main.main()
            captured = capsys.readouterr()
            
            assert exit_code == 1
            assert "Processing error" in captured.err
        finally:
            sys.argv = original_argv


    def test_main_multiple_files_error(self, capsys, monkeypatch):
        """Тест ошибки обработки нескольких файлов."""
        def mock_process_files(*args):
            raise MultipleFilesError([("file1.log", "error1"), ("file2.log", "error2")])
        
        monkeypatch.setattr(
            'src.processors.LogProcessor.process_files',
            mock_process_files
        )
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = [
                "main.py",
                "file1.log",
                "file2.log",
                "--report",
                "handlers"
            ]
            exit_code = main.main()
            captured = capsys.readouterr()
            
            assert exit_code == 1
            assert "Errors occurred while processing files" in captured.err
            assert "file1.log" in captured.err
            assert "file2.log" in captured.err
        finally:
            sys.argv = original_argv


    def test_main_keyboard_interrupt(self, capsys, monkeypatch, test_data_dir: Path):
        """Тест прерывания программы пользователем."""
        def mock_process_files(*args):
            raise KeyboardInterrupt()
        
        monkeypatch.setattr(
            'src.processors.LogProcessor.process_files',
            mock_process_files
        )
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = [
                "main.py",
                str(test_data_dir / "app1.log"),
                "--report",
                "handlers"
            ]
            exit_code = main.main()
            captured = capsys.readouterr()
            
            assert exit_code == 130
            assert "cancelled by user" in captured.err
        finally:
            sys.argv = original_argv