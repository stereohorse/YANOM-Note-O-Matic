from pathlib import Path
import pytest
import logging

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
    assert config.logger_level == expected
    config.set_logger_level(11)


def test_set_logging_level_invalid_arg(tmp_path, caplog):
    logger = yanom.setup_logging(tmp_path)
    config.set_logger_level(logging.INFO)
    yanom.set_logging_level('bad-value', logger)
    assert config.logger_level == logging.INFO
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
def test_command_line_parser(command_line_args, expected):
    args = yanom.command_line_parser(command_line_args)
    assert args[expected[0]] == expected[1]


@pytest.mark.parametrize(
    'command_line_args, value', [
        (['-s', 'Notes'], '2'),
        (['-i', '-c'], '2'),
        ]
)
def test_command_line_parser_bad_args(command_line_args, value):
    with pytest.raises(SystemExit) as exc:
        args = yanom.command_line_parser(command_line_args)
    assert isinstance(exc.type, type(SystemExit))
    assert str(exc.value) == value


def test_setup_logging(tmp_path):
    _ = yanom.setup_logging(tmp_path)
    normal_log_path = Path(tmp_path, f'{config.DATA_DIR}/logs/normal.log')
    error_log_path = Path(tmp_path, f'{config.DATA_DIR}/logs/error.log')
    warning_log_path = Path(tmp_path, f'{config.DATA_DIR}/logs/warning.log')
    debug_log_path = Path(tmp_path, f'{config.DATA_DIR}/logs/debug.log')
    assert normal_log_path.is_file()
    assert error_log_path.is_file()
    assert warning_log_path.is_file()
    assert debug_log_path.is_file()


def test_setup_logging_loggers_logging(tmp_path, caplog):
    config.set_logger_level(logging.DEBUG)
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


def test_configure_environment_debug(caplog):
    command_line_sys_argv = ["pytest", "-l", "debug"]
    yanom.main(command_line_sys_argv)
    assert config.logger_level == logging.DEBUG


def test_configure_environment(caplog):
    config.logger_level = logging.DEBUG
    command_line_sys_argv = ["pytest"]
    yanom.main(command_line_sys_argv)
    assert config.logger_level == logging.INFO
