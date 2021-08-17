from pathlib import Path

import pytest

import config
import conversion_settings


def test_read_settings_from_dictionary():
    cs = conversion_settings.ConversionSettings()
    cs.attachment_folder_name = 'old_folder_name'
    cs._creation_time_in_exported_file_name = False
    settings_dict = {'attachment_folder_name': 'new_folder_name', 'creation_time_in_exported_file_name': True}

    cs.set_from_dictionary(settings_dict)

    assert cs.attachment_folder_name == Path('new_folder_name')
    assert cs._creation_time_in_exported_file_name


@pytest.mark.parametrize(
    'silent', [True, False]
)
def test_read_invalid_settings_from_dictionary(caplog, silent):
    cs = conversion_settings.ConversionSettings()
    config.yanom_globals.is_silent = silent
    cs.set_from_dictionary({'invalid': True})

    assert len(caplog.records) > 0

    for record in caplog.records:
        assert record.levelname == "WARNING"


@pytest.mark.parametrize(
    'quick_setting, expected', [
        ('html', 'html'),
        ('pandoc_markdown_strict', 'pandoc_markdown_strict'),
        ('multimarkdown', 'multimarkdown'),
        ('pandoc_markdown', 'pandoc_markdown'),
        ('commonmark', 'commonmark'),
        ('obsidian', 'obsidian'),
        ('gfm', 'gfm'),
        ('q_own_notes', 'q_own_notes'),
        ('manual', 'manual'),
    ]
)
def test_quick_setting(quick_setting, expected):
    cs = conversion_settings.ConversionSettings()
    cs.set_quick_setting(quick_setting)

    assert cs.quick_setting == expected


@pytest.mark.parametrize(
    'quick_setting, expected', [
        ('html', 'html'),
        ('pandoc_markdown_strict', 'pandoc_markdown_strict'),
        ('multimarkdown', 'multimarkdown'),
        ('pandoc_markdown', 'pandoc_markdown'),
        ('commonmark', 'commonmark'),
        ('obsidian', 'obsidian'),
        ('gfm', 'gfm'),
        ('q_own_notes', 'q_own_notes'),
        ('manual', 'manual'),
    ]
)
def test_quick_setting_when_not_nsx(quick_setting, expected):
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = 'markdown'
    cs.set_quick_setting(quick_setting)

    assert cs.quick_setting == expected


@pytest.mark.parametrize(
    'silent', [True, False]
)
def test_invalid_quick_setting(caplog, silent):
    cs = conversion_settings.ConversionSettings()
    config.yanom_globals.is_silent = silent
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        cs.set_quick_setting('invalid')

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

    assert len(caplog.records) > 0

    for record in caplog.records:
        assert record.levelname == "ERROR"


def test_source_setting_empty_string_data_dir_does_exist(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path

    # create data dir in temp_path to simulate the data folder that will exist
    # because is is where config.ini lives and is in the yanom installs
    Path(tmp_path, config.yanom_globals.data_dir).mkdir()

    #set source with blank entry and test is using default data dir
    cs.source = ''

    assert cs.source == Path(tmp_path, config.yanom_globals.data_dir)
    assert cs._source_absolute_root == Path(tmp_path, config.yanom_globals.data_dir)


def test_source_setting_empty_string_data_dir_not_exist(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path

    # THis will raise error as dat dir does not exist.

    #set source with blank entry and test is using default data dir
    with pytest.raises(SystemExit):
        cs.source = ''


@pytest.mark.parametrize(
    'silent, expected_screen_output', [
        (True, ''),
        (False, 'Invalid source location'),
    ]
)
def test_source_setting_sub_directory_not_existing(tmp_path, caplog, capsys, silent, expected_screen_output):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    config.yanom_globals.is_silent = silent
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        cs.source = 'source-dir'

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1

    assert len(caplog.records) > 0

    for record in caplog.records:
        assert record.levelname == "ERROR"
    captured = capsys.readouterr()
    assert expected_screen_output in captured.out


def test_source_setting_valid_sub_directory(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path, config.yanom_globals.data_dir, "my-source").mkdir(parents=True)
    cs.source = 'my-source'

    assert cs.source == Path("my-source")
    assert cs._source_absolute_root == Path(tmp_path, config.yanom_globals.data_dir, "my-source")


def test_source_setting_valid_absolute_path(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path, config.yanom_globals.data_dir, "my-source").mkdir(parents=True)
    cs.source = str(Path(tmp_path, config.yanom_globals.data_dir, "my-source"))

    assert cs.source == Path("my-source")
    assert cs._source_absolute_root == Path(tmp_path, config.yanom_globals.data_dir, "my-source")


def test_source_setting_valid_absolute_path_not_in_data_dir(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path.parent, "somewhere_else/my-source").mkdir(parents=True)
    cs.source = str(Path(tmp_path.parent, "somewhere_else/my-source"))

    assert cs.source == Path(tmp_path.parent, "somewhere_else/my-source")
    assert cs._source_absolute_root == Path(tmp_path.parent, "somewhere_else/my-source")


def test_export_folder_setting_empty_string(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    cs.export_folder = ''

    assert cs.export_folder == Path(config.yanom_globals.default_export_folder)
    assert cs.export_folder_absolute == Path(tmp_path, config.yanom_globals.data_dir, config.yanom_globals.default_export_folder)


def test_export_folder_setting_valid_absolute_path(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path, config.yanom_globals.data_dir, "my-target").mkdir(parents=True)
    cs.export_folder = str(Path(tmp_path, config.yanom_globals.data_dir, "my-target"))

    assert cs.export_folder == Path("my-target")
    assert cs.export_folder_absolute == Path(tmp_path, config.yanom_globals.data_dir, "my-target")


def test_export_folder_setting_absolute_path_not_in_data_dir(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path.parent, "somewhere_else/my-target").mkdir(parents=True)
    cs.export_folder = str(Path(tmp_path.parent, "somewhere_else/my-target"))

    assert cs.export_folder == Path(tmp_path.parent, "somewhere_else/my-target")
    assert cs.export_folder_absolute == Path(tmp_path.parent, "somewhere_else/my-target")


def test_export_folder_setting_default_data_dir(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path, config.yanom_globals.data_dir,).mkdir(parents=True)
    cs.export_folder = str(Path(tmp_path, config.yanom_globals.data_dir))

    assert cs.export_folder == Path(tmp_path, config.yanom_globals.data_dir)
    assert cs.export_folder_absolute == Path(tmp_path, config.yanom_globals.data_dir)


@pytest.mark.parametrize(
    'silent, expected_screen_output', [
        (True, ''),
        (False, 'Invalid path provided. Path is to existing file not a directory'),
    ]
)
def test_export_folder_setting_provide_a_file_not_directory(tmp_path, caplog, capsys, silent, expected_screen_output):
    config.yanom_globals.is_silent = silent
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path, "my-target-file.txt").touch()

    with pytest.raises(SystemExit) as exc:
        cs.export_folder = str(Path(tmp_path, "my-target-file.txt"))

    assert f"Invalid path provided. Path is to existing file not a directory '{Path(tmp_path, 'my-target-file.txt')}'" in caplog.messages
    captured = capsys.readouterr()
    assert expected_screen_output in captured.out


def test_front_matter_setter_invalid(caplog):
    cs = conversion_settings.ConversionSettings()
    cs.front_matter_format = 'toml'
    with pytest.raises(ValueError) as exc:
        cs.front_matter_format = 'invalid'

    assert 'Invalid value provided for for front matter format. ' in exc.value.args[0]

    assert cs.front_matter_format == 'toml'


def test_metadata_schema_invalid_value(caplog):
    cs = conversion_settings.ConversionSettings()
    cs.metadata_schema = 1

    assert len(caplog.records) > 0

    for record in caplog.records:
        assert record.levelname == "WARNING"


@pytest.mark.parametrize(
    'schema, result', [
        ('time', ['time']),
        ('time, date', ['time', 'date']),
        ('time,date', ['time', 'date']),
        (' time , date ', ['time', 'date']),
    ]
)
def test_metadata_schema_string(schema, result):
    cs = conversion_settings.ConversionSettings()
    cs.metadata_schema = schema

    assert cs.metadata_schema == result


def test_export_format_setter_valid_value():
    cs = conversion_settings.ConversionSettings()
    cs.export_format = 'html'

    assert cs.export_format == 'html'


def test_export_format_setter_invalid_value():
    cs = conversion_settings.ConversionSettings()
    cs.export_format = 'html'

    with pytest.raises(ValueError) as exc:
        cs.export_format = 'invalid'

    assert 'Invalid value provided for for export format. ' in exc.value.args[0]

    assert cs.export_format == 'html'


def test_quick_setting_setter_valid_value():
    cs = conversion_settings.ConversionSettings()
    cs.quick_setting = 'obsidian'

    assert cs.quick_setting == 'obsidian'


def test_quick_setting_setter_invalid_value():
    cs = conversion_settings.ConversionSettings()
    cs.quick_setting = 'obsidian'

    with pytest.raises(ValueError) as exc:
        cs.quick_setting = 'invalid'

    assert 'Invalid value provided for for quick setting. ' in exc.value.args[0]

    assert cs.quick_setting == 'obsidian'


def test_source_absolute_path_property():
    cs = conversion_settings.ConversionSettings()
    cs._source_absolute_root = Path('my/path')

    assert cs.source_absolute_root == Path('my/path')


def test_conversion_input_setter_invalid_value():
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = 'nsx'

    with pytest.raises(ValueError) as exc:
        cs.conversion_input = 'invalid'

    assert 'Invalid value provided for for conversion input. ' in exc.value.args[0]

    assert cs.conversion_input == 'nsx'


def test_markdown_conversion_input_setter_invalid_value():
    cs = conversion_settings.ConversionSettings()
    cs.markdown_conversion_input = 'gfm'

    with pytest.raises(ValueError) as exc:
        cs.markdown_conversion_input = 'invalid'

    assert 'Invalid value provided for for markdown conversion input. ' in exc.value.args[0]

    assert cs.markdown_conversion_input == 'gfm'



@pytest.mark.parametrize(
    'string_to_test, expected', [
        ("!?hello", Path('!-hello')),
        ("", Path(config.yanom_globals.default_attachment_folder)),
    ]
)
def test_attachment_folder_name_setter(string_to_test, expected):
    cs = conversion_settings.ConversionSettings()

    cs.attachment_folder_name = string_to_test

    assert cs.attachment_folder_name == expected


@pytest.mark.parametrize(
    'string_to_test, expected', [
        ("!?hello", Path('!-hello')),
        ("", Path(config.yanom_globals.default_export_folder)),
    ]
)
def test_attachment_export_folder_setter(string_to_test, expected):
    cs = conversion_settings.ConversionSettings()

    cs.export_folder = string_to_test

    assert cs.export_folder == expected
