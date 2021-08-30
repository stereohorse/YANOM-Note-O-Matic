from mock import patch
from pathlib import Path
import pytest
import logging
import sys

import config
import yanom


@pytest.mark.parametrize(
    'log_level, expected', [
        ('critical', logging.CRITICAL),
        ('error', logging.ERROR),
        ('warn', logging.WARNING),
        ('warning', logging.WARNING),
        ('info', logging.INFO),
        ('debug', logging.DEBUG),
        ('fred', logging.INFO),
        ]
)
def test_set_logging_level(log_level, expected, tmp_path):
    logger = yanom.setup_logging(tmp_path)
    yanom.set_logging_level(log_level, logger)
    assert config.yanom_globals.logger_level == expected
    config.yanom_globals.logger_level = 11


def test_set_logging_level_invalid_arg(tmp_path, caplog):
    logger = yanom.setup_logging(tmp_path)
    config.yanom_globals.logger_level = logging.INFO
    yanom.set_logging_level('bad-value', logger)
    assert config.yanom_globals.logger_level == logging.INFO
    assert f'Invalid log level on command line: "bad-value".  Using INFO level' in caplog.messages


@pytest.mark.parametrize(
    'command_line_args, expected', [
        (['--log', 'fred'], ('log', 'fred')),
        (['-l', 'fred'], ('log', 'fred')),
        (['--silent'], ('silent', True)),
        (['-s'], ('silent', True)),
        (['--ini'], ('ini', True)),
        (['-i'], ('ini', True)),
        (['--cli'], ('cli', True)),
        (['-c'], ('cli', True)),
        (['--source', 'Notes'], ('source', 'Notes')),
        ]
)
def test_command_line_parser(command_line_args, expected, tmp_path):
    logger = yanom.setup_logging(tmp_path)
    args = yanom.command_line_parser(command_line_args, logger)
    assert args[expected[0]] == expected[1]


@pytest.mark.parametrize(
    'command_line_args, value', [
        (['-s', 'Notes'], '2'),
        (['-i', '-c'], '2'),
        ]
)
def test_command_line_parser_bad_args(command_line_args, value, tmp_path):
    logger = yanom.setup_logging(tmp_path)
    with pytest.raises(SystemExit) as exc:
        args = yanom.command_line_parser(command_line_args, logger)
    assert isinstance(exc.type, type(SystemExit))
    assert str(exc.value) == value


def test_setup_logging(tmp_path):
    _ = yanom.setup_logging(tmp_path)
    normal_log_path = Path(tmp_path, f'logs/normal.log')
    error_log_path = Path(tmp_path, f'logs/error.log')
    warning_log_path = Path(tmp_path, f'logs/warning.log')
    debug_log_path = Path(tmp_path, f'logs/debug.log')
    assert normal_log_path.is_file()
    assert error_log_path.is_file()
    assert warning_log_path.is_file()
    assert debug_log_path.is_file()


def test_setup_logging_loggers_logging(tmp_path, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    yanom.setup_logging(tmp_path)
    logger = logging.getLogger(f'From pytest')
    logger.info("logging info")

    assert len(caplog.records) > 0

    for record in caplog.records:
        assert record.levelname == "INFO"
    assert "From pytest" in caplog.text

    caplog.clear()
    logger.debug("logging debug")

    assert len(caplog.records) > 0

    for record in caplog.records:
        assert record.levelname == "DEBUG"
    assert "From pytest" in caplog.text

    caplog.clear()
    logger.error("logging error")

    assert len(caplog.records) > 0

    for record in caplog.records:
        assert record.levelname == "ERROR"
    assert "From pytest" in caplog.text


def test_configure_environment_debug():
    with patch("yanom.run_yanom", autospec=True):
        yanom.main(["pytest", "-l", "debug"])
        assert config.yanom_globals.logger_level == logging.DEBUG


def test_configure_environment():
    with patch("yanom.run_yanom", autospec=True):
        config.yanom_globals.logger_level = logging.DEBUG
        command_line_sys_argv = ["pytest"]
        yanom.main(command_line_sys_argv)
        assert config.yanom_globals.logger_level == logging.INFO


def test_handle_unhandled_exception(caplog):
    assert sys.excepthook is yanom.handle_unhandled_exception
    try:
        1 / 0
    except ZeroDivisionError:
        yanom.handle_unhandled_exception(*sys.exc_info())

    assert "Unhandled exception" in caplog.text


def test_handle_unhandled_exception_keyboard_interupt(caplog):
    assert sys.excepthook is yanom.handle_unhandled_exception
    try:
        raise KeyboardInterrupt
    except KeyboardInterrupt:
        yanom.handle_unhandled_exception(*sys.exc_info())

    assert len(caplog.records) == 1
    assert "Cancelled by User" in caplog.text
