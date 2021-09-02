import logging
from pathlib import Path
import subprocess
from unittest.mock import patch

import pytest

import config
import conversion_settings
import helper_functions
import pandoc_converter


def test_check_and_set_up_pandoc_if_required():
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = 'nsx'
    cs.export_format = 'gfm'
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    with patch('pandoc_converter.PandocConverter.generate_pandoc_options', spec=True) as mock_generate_pandoc_options:
        with patch('pandoc_converter.PandocConverter.find_pandoc_version', spec=True) as mock_find_pandoc_version:
            pandoc_processor.check_and_set_pandoc_options_if_required()

            mock_generate_pandoc_options.assert_called_once()
            mock_find_pandoc_version.assert_called_once()


@pytest.mark.parametrize(
    'conversion_input, markdown_conversion_input, export_format', [
        ('nsx', 'gfm', 'html'),
        ('html', 'gfm', 'html'),
        ('markdown', 'gfm', 'gfm'),
    ], ids=['nsx-html', 'html-html', 'markdown-gfm-gfm']
)
def test_check_and_set_up_pandoc_if_required_nsx_and_html(conversion_input, markdown_conversion_input, export_format):
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = conversion_input
    cs.export_format = export_format
    cs.markdown_conversion_input = markdown_conversion_input
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    with patch('pandoc_converter.PandocConverter.generate_pandoc_options', spec=True) as mock_generate_pandoc_options:
        with patch('pandoc_converter.PandocConverter.find_pandoc_version', spec=True) as mock_find_pandoc_version:
            pandoc_processor.check_and_set_pandoc_options_if_required()

            mock_generate_pandoc_options.assert_not_called()
            mock_find_pandoc_version.assert_not_called()


@pytest.mark.parametrize(
    'silent_mode, expected_capture_out', [
        (True, ''),
        (False, 'Found pandoc '),
    ], ids=['is_silent', 'not_silent']
)
def test_find_pandoc_version(caplog, capsys, silent_mode, expected_capture_out):
    config.yanom_globals.logger_level = logging.DEBUG
    config.yanom_globals.is_silent = silent_mode
    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    caplog.clear()
    pandoc_processor.find_pandoc_version()

    assert len(caplog.records) == 1

    for record in caplog.records:
        assert record.levelname == "DEBUG"
        assert 'Found pandoc version' in record.message

    captured = capsys.readouterr()
    assert expected_capture_out in captured.out


def test_find_pandoc_version_invalid_path_check_sys_exit(caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor._pandoc_path = 'invalid-path'
    caplog.clear()
    with pytest.raises(FileNotFoundError):
        pandoc_processor.find_pandoc_version()

    for record in caplog.records:
        assert record.levelname == "WARNING"


@pytest.mark.parametrize(
    'silent_mode, expected_capture_out', [
        (True, ''),
        (False, 'Unable to fetch pandoc version please check log files for additional information'),
    ], ids=['is_silent', 'not_silent']
)
def test_find_pandoc_version_force_subprocess_error(caplog, capsys, monkeypatch, silent_mode, expected_capture_out):
    def mock_run(ignored, capture_output, text, timeout):
        raise subprocess.CalledProcessError(3, "a_command'")

    config.yanom_globals.is_silent = silent_mode
    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    caplog.clear()
    with pytest.raises(SystemExit):
        monkeypatch.setattr(subprocess, 'run', mock_run)
        pandoc_processor.find_pandoc_version()

    assert 'Exiting as unable to get pandoc version' in caplog.messages

    captured = capsys.readouterr()
    assert expected_capture_out in captured.out


@pytest.mark.parametrize(
    'version, conversion_input, input_file_format, output_file_format, expected', [
        ('1.15', 'nsx', 'html', 'gfm', 'gfm'),
        ('1.15', 'nsx', 'html', 'obsidian', 'gfm'),
        ('1.15', 'nsx', 'html', 'pandoc_markdown', 'markdown'),
        ('1.15', 'nsx', 'html', 'commonmark', 'commonmark'),
        ('1.15', 'nsx', 'html', 'pandoc_markdown_strict', 'markdown_strict'),
        ('1.15', 'nsx', 'html', 'multimarkdown', 'markdown_mmd'),
        ('1.15', 'nsx', 'html', 'html', 'html'),
        ('1.15', 'markdown', 'gfm', 'html', 'html'),
    ]
)
def test_generate_pandoc_options_check_pandoc_conversion_option_lookup(caplog, version, conversion_input,
                                                                       input_file_format, output_file_format,
                                                                       expected):
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = conversion_input
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor._pandoc_version = version
    pandoc_processor.output_file_format = output_file_format
    caplog.clear()
    pandoc_processor.generate_pandoc_options()

    assert pandoc_processor.pandoc_options[-2] == expected


@pytest.mark.parametrize(
    'version, conversion_input, markdown_conversion_input, output_file_format, expected', [
        ('1.15', 'nsx', 'obsidian', 'gfm', 'html'),
        ('1.15', 'html', 'gfm', 'obsidian', 'html'),
        ('1.15', 'markdown', 'pandoc_markdown', 'gfm', 'markdown'),
    ]
)
def test_generate_pandoc_options_check_conversion_input_format_setting(caplog, version, conversion_input,
                                                                       markdown_conversion_input,
                                                                       output_file_format, expected):
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = conversion_input
    cs.markdown_conversion_input = markdown_conversion_input
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor._pandoc_version = version
    pandoc_processor.output_file_format = output_file_format
    caplog.clear()
    pandoc_processor.generate_pandoc_options()

    assert pandoc_processor.pandoc_options[2] == expected


@pytest.mark.parametrize(
    'version, conversion_input, input_file_format, output_file_format, expected', [
        ('1.15', 'nsx', 'html', 'gfm', ['gfm', '--no-wrap']),
        ('1.16', 'nsx', 'html', 'gfm', ['--wrap=none', '-o']),
        ('1.18', 'nsx', 'html', 'gfm', ['--wrap=none', '-o']),
        ('1.19', 'nsx', 'html', 'gfm', ['--wrap=none', '--atx-headers']),
        ('1.20', 'nsx', 'html', 'gfm', ['--wrap=none', '--atx-headers']),
        ('2.11.1', 'nsx', 'html', 'gfm', ['--wrap=none', '--atx-headers']),
        ('2.11.2', 'nsx', 'html', 'gfm', ['--wrap=none', '--markdown-headings=atx']),
        ('2.13', 'nsx', 'html', 'gfm', ['--wrap=none', '--markdown-headings=atx']),
    ]
)
def test_generate_pandoc_options_check_pandoc_version_conversion_settings(caplog, version, conversion_input,
                                                                          input_file_format, output_file_format,
                                                                          expected):
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = conversion_input
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor._pandoc_version = version
    pandoc_processor.output_file_format = output_file_format
    caplog.clear()
    pandoc_processor.generate_pandoc_options()

    assert pandoc_processor.pandoc_options[-2:] == expected


def test_convert_using_strings_forcing_non_zero_return_code_from_pandoc(caplog):
    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor.pandoc_options = [pandoc_processor._pandoc_path, '-fqwe', 'html', '-s', '-t', 'gfm']
    caplog.clear()

    result = pandoc_processor.convert_using_strings('hello world', 'my_note')

    assert result == ''

    assert len(caplog.records) == 1
    for record in caplog.records:
        assert 'Pandoc Return code=' in record.message


@pytest.mark.parametrize(
    'silent_mode, expected_capture_out', [
        (True, ''),
        (False, 'Error converting note'),
    ], ids=['is_silent', 'not_silent']
)
def test_convert_using_strings_forcing_subprocess_error(caplog, capsys, monkeypatch, silent_mode, expected_capture_out):
    def mock_run(ingored1, input, capture_output, encoding, text, timeout):
        raise subprocess.CalledProcessError(3, "a_command'")

    config.yanom_globals.is_silent = silent_mode
    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor.pandoc_options = [pandoc_processor._pandoc_path, '-fqwe', 'html', '-s', '-t', 'gfm']
    caplog.clear()

    monkeypatch.setattr(subprocess, 'run', mock_run)
    result = pandoc_processor.convert_using_strings('hello world', 'my_note')

    assert result == 'Error converting data'
    assert 'Unable to convert note "my_note".' == caplog.messages[0]

    captured = capsys.readouterr()
    assert expected_capture_out in captured.out


@pytest.mark.parametrize(
    'silent_mode, expected_capture_out', [
        (True, ''),
        (False, 'Error converting note'),
    ], ids=['is_silent', 'not_silent']
)
def test_convert_using_strings_html_to_markdown(caplog, silent_mode, expected_capture_out):
    config.yanom_globals.is_silent = silent_mode
    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor.pandoc_options = [pandoc_processor._pandoc_path,
                                       '-f',
                                       'html',
                                       '-s',
                                       '-t',
                                       'gfm',
                                       '--wrap=none',
                                       '--markdown-headings=atx'
                                       ]
    caplog.clear()

    result = pandoc_processor.convert_using_strings(
        '<p>hello world</p><p><img src="image.png" width="600"/></p><p>Goodbye world</p>',
        'my_note'
    )

    assert result == 'hello world\n\n<img src="image.png" width="600" />\n\nGoodbye world\n'
    # Note result ahs any html that will be embeded in markdown file sureounded by additonal line spacing,
    # Markdown standard s require one nblank line either side of the html content


def test_convert_using_strings_forcing_pandoc_not_installed():
    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    pandoc_processor.pandoc_options = ['fake_path', '-fqwe', 'html', '-s', '-t', 'gfm']

    with pytest.raises(FileNotFoundError):
        result = pandoc_processor.convert_using_strings('hello world', 'my_note')

        assert result == 'Error converting data'


@pytest.mark.parametrize(
    'is_linux, if_frozen, expected_ends_with', [
        (False, True, '/pandoc/pandoc'),
        (True, True, 'pandoc'),
        (False, False, 'pandoc'),
        (True, False, 'pandoc'),

    ], ids=['non-linux-frozen', 'linux-frozen', 'non-linux-non-frozen', 'linux-not-frozen']
)
def test_set_pandoc_path(monkeypatch, is_linux, if_frozen, expected_ends_with):
    def mock_is_system_linux(_ignored):
        return is_linux

    def mock_is_this_a_frozen_package(_ignored):
        return if_frozen

    cs = conversion_settings.ConversionSettings()
    pandoc_processor = pandoc_converter.PandocConverter(cs)
    monkeypatch.setattr(pandoc_converter.PandocConverter, 'is_system_linux', mock_is_system_linux)
    monkeypatch.setattr(pandoc_converter.PandocConverter, 'is_this_a_frozen_package', mock_is_this_a_frozen_package)
    pandoc_processor.set_pandoc_path()

    found_path_as_posix_string = helper_functions.path_to_posix_str(Path(pandoc_processor._pandoc_path))
    assert found_path_as_posix_string.endswith(expected_ends_with)
