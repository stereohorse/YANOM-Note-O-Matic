from pathlib import Path

import pytest

import config
import conversion_settings
from embeded_file_types import EmbeddedFileTypes


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

    # set source with blank entry and test is using default data dir
    cs.source = ''

    assert cs.source == Path(tmp_path, config.yanom_globals.data_dir)
    assert cs._source_absolute_root == Path(tmp_path, config.yanom_globals.data_dir)


def test_source_setting_empty_string_data_dir_not_exist(tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path

    # THis will raise error as dat dir does not exist.

    # set source with blank entry and test is using default data dir
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
    assert cs.export_folder_absolute == Path(tmp_path,
                                             config.yanom_globals.data_dir,
                                             config.yanom_globals.default_export_folder
                                             )


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
    Path(tmp_path, config.yanom_globals.data_dir, ).mkdir(parents=True)
    cs.export_folder = str(Path(tmp_path, config.yanom_globals.data_dir))

    assert cs.export_folder == Path(tmp_path, config.yanom_globals.data_dir)
    assert cs.export_folder_absolute == Path(tmp_path, config.yanom_globals.data_dir)


@pytest.mark.parametrize(
    'silent, expected_screen_output', [
        (True, ''),
        (False, 'Invalid path provided '),
    ]
)
def test_exit_if_path_is_invalid(tmp_path, capsys, silent, expected_screen_output):
    config.yanom_globals.is_silent = silent
    cs = conversion_settings.ConversionSettings()

    with pytest.raises(SystemExit):
        cs.exit_if_path_is_invalid(str(Path(tmp_path, "no\0where")), str(Path(tmp_path, "no:where")))

    captured = capsys.readouterr()
    assert expected_screen_output in captured.out


@pytest.mark.parametrize(
    'silent, expected_screen_output', [
        (True, ''),
        (False, 'Invalid path provided. Path is to existing file not a directory'),
    ]
)
def test_export_folder_setting_provide_invalid_directory(tmp_path, caplog, capsys, silent, expected_screen_output):
    config.yanom_globals.is_silent = silent
    cs = conversion_settings.ConversionSettings()
    cs.working_directory = tmp_path
    Path(tmp_path, "my-target-file.txt").touch()

    with pytest.raises(SystemExit):
        cs.export_folder = str(Path(tmp_path, "my-target-file.txt"))

    assert f"Invalid path provided. Path is to existing file " \
           f"not a directory '{Path(tmp_path, 'my-target-file.txt')}'" \
           in caplog.messages

    captured = capsys.readouterr()
    assert expected_screen_output in captured.out


def test_front_matter_setter_invalid():
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


def test_set_common_quick_settings_defaults_for_nsx_input():
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = 'nsx'
    cs.metadata_schema = ['hello']

    cs.set_common_quick_settings_defaults()

    assert cs.metadata_schema == ['title', 'ctime', 'mtime', 'tag']


def test_set_common_quick_settings_defaults_for_nimbus_input():
    cs = conversion_settings.ConversionSettings()
    cs.conversion_input = 'nimbus'
    cs.metadata_schema = ['hello']

    cs.set_common_quick_settings_defaults()

    assert cs.metadata_schema == ['title', 'tag']
    assert cs.first_column_as_header is False


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
        ("/hello/all", Path("/hello/all")),
    ]
)
def test_attachment_export_folder_setter(string_to_test, expected, tmp_path):
    cs = conversion_settings.ConversionSettings()
    cs._working_directory = tmp_path
    export_path = Path(string_to_test)
    cs.export_folder = export_path

    assert cs.export_folder == Path(expected)
    assert cs.export_folder_absolute == Path(tmp_path, config.yanom_globals.data_dir, expected)


@pytest.mark.parametrize(
    'value', ['ignore', 'copy', 'orphan']
)
def test_orphans_setter(value):
    cs = conversion_settings.ConversionSettings()
    cs.orphans = value

    assert cs.orphans == value


def test_orphans_setter_invalid_value():
    cs = conversion_settings.ConversionSettings()
    cs.orphans = 'ignore'
    with pytest.raises(ValueError) as exc:
        cs.orphans = 'invalid value'

    assert 'Invalid value provided for for orphan file option. Attempted to use invalid value -' in exc.value.args[0]

    assert cs.orphans == 'ignore'


@pytest.mark.parametrize(
    'value, expected, caplog_length', [
        (
                ['ignore', 'me', 'always'],
                ['ignore', 'me', 'always'],
                0,
        ),
        (
                'single-item',
                ['single-item'],
                0,
        ),
        (
                [],
                [''],
                0,
        ),
        (
                (),
                ['md', 'pdf'],
                1,
        ),
    ]
)
def test_embed_these_document_types_setter(value, expected, caplog_length, caplog):
    cs = conversion_settings.ConversionSettings()
    cs._embed_these_document_types = ['md', 'pdf']
    cs._embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    cs._embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    cs._embed_these_video_types = ['mp4', 'webm', 'ogv']
    cs._embed_files = EmbeddedFileTypes(cs._embed_these_document_types, cs._embed_these_image_types,
                                        cs._embed_these_audio_types, cs._embed_these_video_types)

    assert cs.embed_files.documents == ['md', 'pdf']

    cs.embed_these_document_types = value

    assert cs.embed_these_document_types == expected
    assert cs.embed_files.documents == expected
    assert len(caplog.records) == caplog_length


@pytest.mark.parametrize(
    'value, expected, caplog_length', [
        (
                ['ignore', 'me', 'always'],
                ['ignore', 'me', 'always'],
                0,
        ),
        (
                'single-item',
                ['single-item'],
                0,
        ),
        (
                [],
                [''],
                0,
        ),
        (
                (),
                ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'],
                1,
        ),
    ]
)
def test_embed_these_image_types_setter(value, expected, caplog_length, caplog):
    cs = conversion_settings.ConversionSettings()
    cs._embed_these_document_types = ['md', 'pdf']
    cs._embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    cs._embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    cs._embed_these_video_types = ['mp4', 'webm', 'ogv']
    cs._embed_files = EmbeddedFileTypes(cs._embed_these_document_types, cs._embed_these_image_types,
                                        cs._embed_these_audio_types, cs._embed_these_video_types)

    assert cs.embed_files.images == ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']

    cs.embed_these_image_types = value

    assert cs.embed_these_image_types == expected
    assert cs.embed_files.images == expected
    assert len(caplog.records) == caplog_length


@pytest.mark.parametrize(
    'value, expected, caplog_length', [
        (
                ['ignore', 'me', 'always'],
                ['ignore', 'me', 'always'],
                0,
        ),
        (
                'single-item',
                ['single-item'],
                0,
        ),
        (
                [],
                [''],
                0,
        ),
        (
                (),
                ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac'],
                1,
        ),
    ]
)
def test_embed_these_audio_types_setter(value, expected, caplog_length, caplog):
    cs = conversion_settings.ConversionSettings()
    cs._embed_these_document_types = ['md', 'pdf']
    cs._embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    cs._embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    cs._embed_these_video_types = ['mp4', 'webm', 'ogv']
    cs._embed_files = EmbeddedFileTypes(cs._embed_these_document_types, cs._embed_these_image_types,
                                        cs._embed_these_audio_types, cs._embed_these_video_types)

    assert cs.embed_files.audio == ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']

    cs.embed_these_audio_types = value

    assert cs.embed_these_audio_types == expected
    assert cs.embed_files.audio == expected
    assert len(caplog.records) == caplog_length


@pytest.mark.parametrize(
    'value, expected, caplog_length', [
        (
                ['ignore', 'me', 'always'],
                ['ignore', 'me', 'always'],
                0,
        ),
        (
                'single-item',
                ['single-item'],
                0,
        ),
        (
                [],
                [''],
                0,
        ),
        (
                (),
                ['mp4', 'webm', 'ogv'],
                1,
        ),
    ]
)
def test_embed_these_video_types_setter(value, expected, caplog_length, caplog):
    cs = conversion_settings.ConversionSettings()
    cs._embed_these_document_types = ['md', 'pdf']
    cs._embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    cs._embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    cs._embed_these_video_types = ['mp4', 'webm', 'ogv']
    cs._embed_files = EmbeddedFileTypes(cs._embed_these_document_types, cs._embed_these_image_types,
                                        cs._embed_these_audio_types, cs._embed_these_video_types)

    assert cs.embed_files.video == ['mp4', 'webm', 'ogv']

    cs.embed_these_video_types = value

    assert cs.embed_these_video_types == expected
    assert cs.embed_files.video == expected
    assert len(caplog.records) == caplog_length


def test_keep_nimbus_row_and_column_headers_setter():
    cs = conversion_settings.ConversionSettings()
    cs._keep_nimbus_row_and_column_headers = True

    assert cs.keep_nimbus_row_and_column_headers

    cs.keep_nimbus_row_and_column_headers = False

    assert not cs.keep_nimbus_row_and_column_headers


def test_str():
    cs = conversion_settings.ConversionSettings()
    expected = """ConversionSettings(valid_conversion_inputs=['html', 'markdown', 'nimbus', 'nsx'], valid_markdown_conversion_inputs='['obsidian', 'gfm', 'commonmark', 'q_own_notes', 'pandoc_markdown_strict', 'pandoc_markdown', 'multimarkdown']', valid_quick_settings='['manual', 'q_own_notes', 'obsidian', 'gfm', 'commonmark', 'pandoc_markdown', 'pandoc_markdown_strict', 'multimarkdown', 'html']', valid_export_formats='['q_own_notes', 'obsidian', 'gfm', 'pandoc_markdown', 'commonmark', 'pandoc_markdown_strict', 'multimarkdown', 'html']', valid_front_matter_formats]'['yaml', 'toml', 'json', 'text', 'none']', markdown_conversion_input='gfm, quick_setting='gfm', export_format='gfm', yaml_front_matter=yaml, metadata_schema='['']', tag_prefix='#', first_row_as_header=True, first_column_as_header=True, spaces_in_tags=False, split_tags=False, export_folder='notes', attachment_folder_name='attachments', creation_time_in_exported_file_name='False', orphans='orphan, make file links absolute='False', embed_these_document_types='['md', 'pdf']', embed_these_image_types='['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']', embed_these_audio_types='['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']', embed_these_video_types='['mp4', 'webm', 'ogv']', keep_nimbus_row_and_column_headers='False', unrecognised_tag_format='html')"""
    result = str(cs)

    assert result == expected


@pytest.mark.parametrize(
    'value', ['text', 'html']
)
def test_unrecognised_tag_format_setter(value):
    cs = conversion_settings.ConversionSettings()
    cs.unrecognised_tag_format = value

    assert cs.unrecognised_tag_format == value


def test_unrecognised_tag_format_setter_invalid_value():
    cs = conversion_settings.ConversionSettings()
    cs.unrecognised_tag_format = 'html'
    with pytest.raises(ValueError) as exc:
        cs.unrecognised_tag_format = 'invalid value'

    assert 'Invalid value provided for for unrecognised tag format option. Attempted to use invalid value -' in exc.value.args[0]

    assert cs.unrecognised_tag_format == 'html'
