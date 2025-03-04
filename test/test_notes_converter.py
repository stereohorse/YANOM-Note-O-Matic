import logging

from mock import patch
import os
from pathlib import Path
import pytest

import config
import config_data
import content_link_management
import conversion_settings
import file_converter_HTML_to_MD
import file_converter_MD_to_HTML
import file_converter_MD_to_MD
import notes_converter
import nsx_file_converter


def touch(path):
    with open(path, 'a'):
        os.utime(path, None)


class FakeNSXFile:
    def __init__(self):
        self.inter_note_link_processor = FakeInterLinkProcessor()
        self.note_page_count = 1
        self.note_book_count = 2
        self.image_count = 3
        self.attachment_count = 4
        self.null_attachments = []
        self.encrypted_notes = []
        self.exported_notes = []

    @staticmethod
    def process_nsx_file():
        print('nsx_file process_nsx_file called')
        return


class FakeInterLinkProcessor:
    def __init__(self):
        self.renamed_links_not_corrected = [1, 2]
        self.replacement_links = [1, 2, 3]
        self.unmatched_links_msg = "missing links message"


class FakeConfigData:
    def __init__(self):
        self.conversion_settings = 'fake_conversion_settings'


def test_configure_for_ini_settings(caplog):
    args = ''
    nc = notes_converter.NotesConvertor(args, 'config_data_fake')
    nc.config_data = FakeConfigData()

    caplog.clear()

    nc.configure_for_ini_settings()

    assert len(caplog.records) == 1
    assert caplog.records[0].message == 'Using settings from config  ini file'
    assert nc.conversion_settings == 'fake_conversion_settings'


def test_run_interactive_command_line_interface(caplog, tmp_path):
    args = {'source': tmp_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()

    with patch('interactive_cli.StartUpCommandLineInterface.run_cli', spec=True,
               return_value=nc.conversion_settings) as mock_run_cli:
        caplog.clear()
        nc.run_interactive_command_line_interface()

        mock_run_cli.assert_called_once()
        assert 'Using conversion settings from interactive command line tool' in caplog.messages


def test_evaluate_command_line_arguments_when_will_be_interactive_command_line_used(caplog):
    test_source_path = str(Path(__file__).parent.absolute())
    config.yanom_globals.logger_level = logging.DEBUG
    args = {'silent': False, 'ini': False, 'source': test_source_path, 'export': 'hello'}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()

    with patch('notes_converter.NotesConvertor.configure_for_ini_settings', spec=True,
               ) as mock_configure_for_ini_settings:
        with patch('notes_converter.NotesConvertor.run_interactive_command_line_interface', spec=True,
                   ) as mock_run_interactive_command_line_interface:
            caplog.clear()
            nc.evaluate_command_line_arguments()

            mock_configure_for_ini_settings.assert_called_once()
            mock_run_interactive_command_line_interface.assert_called_once()

            assert nc.conversion_settings.export_folder == Path('hello')
            assert nc.conversion_settings.source == Path(test_source_path)

            assert 'Starting interactive command line tool' in caplog.messages


@pytest.mark.parametrize(
    'silent, ini', [
        (True, True),
        (True, False),
        (False, True),
    ]
)
def test_evaluate_command_line_arguments_when_going_to_use_ini_file(caplog, silent, ini):
    test_source_path = str(Path(__file__).parent.absolute())
    config.yanom_globals.logger_level = logging.DEBUG
    args = {'silent': silent, 'ini': ini, 'source': test_source_path, 'export': 'hello'}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()

    with patch('notes_converter.NotesConvertor.configure_for_ini_settings', spec=True,
               ) as mock_configure_for_ini_settings:
        with patch('notes_converter.NotesConvertor.run_interactive_command_line_interface', spec=True,
                   ) as mock_run_interactive_command_line_interface:
            caplog.clear()
            nc.evaluate_command_line_arguments()

            mock_configure_for_ini_settings.assert_called_once()
            mock_run_interactive_command_line_interface.assert_not_called()


def test_evaluate_command_line_arguments_when_blank_source_export_in_args(caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    args = {'silent': False, 'ini': False, 'source': '', 'export': ''}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()

    with patch('notes_converter.NotesConvertor.configure_for_ini_settings', spec=True,
               ) as mock_configure_for_ini_settings:
        with patch('notes_converter.NotesConvertor.run_interactive_command_line_interface', spec=True,
                   ) as mock_run_interactive_command_line_interface:
            caplog.clear()
            nc.evaluate_command_line_arguments()

            mock_configure_for_ini_settings.assert_called_once()
            mock_run_interactive_command_line_interface.assert_called_once()

            assert nc.conversion_settings.export_folder == 'notes'
            assert nc.conversion_settings.source == ''

            assert 'Starting interactive command line tool' in caplog.messages


def test_update_processing_stats():
    test_source_path = str(Path(__file__).parent.absolute())
    args = {'source': test_source_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)

    nc.update_processing_stats(FakeNSXFile())
    assert nc._note_page_count == 1
    assert nc._note_book_count == 2
    assert nc._image_count == 3
    assert nc._attachment_count == 4


def test_process_nsx_files(capsys):
    test_source_path = str(Path(__file__).parent.absolute())
    args = {'source': test_source_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)

    nc._nsx_backups = [FakeNSXFile()]

    nc.process_nsx_files()

    captured = capsys.readouterr()
    assert 'nsx_file process_nsx_file called' in captured.out
    assert nc._note_page_count == 1
    assert nc._note_book_count == 2
    assert nc._image_count == 3
    assert nc._attachment_count == 4


@pytest.mark.parametrize(
    'filetype', ['nsx', 'html']
)
def test_generate_file_list_multiple_files(tmp_path, filetype):
    test_source_path = tmp_path
    args = {'source': test_source_path}
    touch(Path(tmp_path, f'file1.{filetype}'))
    touch(Path(tmp_path, f'file2.{filetype}'))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings.source = Path(tmp_path)

    result = nc.generate_file_list(f'{filetype}', nc.conversion_settings.source_absolute_root)

    assert len(result) == 2
    assert Path(tmp_path, f'file1.{filetype}') in result
    assert Path(tmp_path, f'file2.{filetype}') in result


def test_generate_file_list_single_file_source(tmp_path):
    test_source_path = tmp_path
    args = {'source': test_source_path}
    touch(Path(tmp_path, 'file1.nsx'))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings.source = Path(tmp_path, 'file1.nsx')

    result = nc.generate_file_list('nsx', nc.conversion_settings.source_absolute_root)

    assert len(result) == 1
    assert Path(tmp_path, f'file1.nsx') in result


@pytest.mark.parametrize(
    'silent', [True, False]
)
def test_convert_nsx(tmp_path, silent):
    config.yanom_globals.is_silent = silent
    test_source_path = tmp_path
    args = {'source': test_source_path}
    touch(Path(tmp_path, 'file1.nsx'))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings.source = Path(tmp_path)

    with patch('notes_converter.NotesConvertor.process_nsx_files', spec=True) as mock_process_nsx_files:
        nc.convert_nsx()

    mock_process_nsx_files.assert_called_once()
    assert len(nc._nsx_backups) == 1
    assert isinstance(nc._nsx_backups[0], nsx_file_converter.NSXFile)


def test_convert_html(tmp_path):
    test_source_path = tmp_path
    args = {'source': test_source_path}
    touch(Path(tmp_path, 'file1.html'))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings.orphans = 'orphan'
    nc.conversion_settings._working_directory = Path(tmp_path)
    nc.conversion_settings.export_folder = Path(tmp_path, 'notes')
    Path(nc.conversion_settings.export_folder).mkdir()
    nc.conversion_settings._source = Path(tmp_path, 'file1.html')
    nc.conversion_settings._source_absolute_root = Path(tmp_path)

    nc.convert_html()
    assert Path(tmp_path, 'file1.html').exists()
    assert Path(tmp_path, 'notes', 'file1.md').exists()


def test_convert_html_rename_existing_file(tmp_path):
    test_source_path = tmp_path
    args = {'source': test_source_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings.orphans = 'orphan'
    nc.conversion_settings._working_directory = Path(tmp_path)
    nc.conversion_settings.export_folder = Path(tmp_path, 'notes')
    nc.conversion_settings.orphans = 'orphan'

    touch(Path(tmp_path, 'file1.html'))
    # add link to existing file so it does not get moved to orphans
    content_for_source = f'<a href="file1.md">existing file</a><a href="{Path(tmp_path, "notes", "file1.md")}">existing file</a>'
    Path(tmp_path, 'file1.html').write_text(content_for_source)
    # create the notes export folder and create the existing file
    Path(tmp_path, 'notes').mkdir()
    touch(Path(tmp_path, 'notes', 'file1.md'))

    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)

    nc.convert_html()

    assert Path(tmp_path, 'file1.html').exists()
    assert Path(tmp_path, 'notes', 'file1.md').exists()
    assert Path(tmp_path, 'notes', 'file1-old-1.md').exists()
    assert Path(tmp_path, 'notes', 'file1-old-1.md').stat().st_size == 0
    assert Path(tmp_path, 'notes', 'file1.md').stat().st_size > 0


def test_process_files(tmp_path):
    args = {'source': tmp_path}
    touch(Path(tmp_path, 'file1.html'))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path, 'file1.html')
    nc.conversion_settings._source_absolute_root = Path(tmp_path)

    files_to_convert = [Path(tmp_path, 'file1.html')]
    file_converter = file_converter_HTML_to_MD.HTMLToMDConverter(nc.conversion_settings, files_to_convert)

    nc.process_files(files_to_convert, file_converter)

    assert nc._note_page_count == 1


def test_process_files_copy_attachments(tmp_path):
    args = {'source': tmp_path}
    touch(Path(tmp_path, 'file1.html'))
    file1_content = '<a href="attachments/a-file.pdf">an attachment</a>'
    Path(tmp_path, 'file1.html').write_text(file1_content)
    Path(tmp_path, 'attachments').mkdir()
    Path(tmp_path, 'attachments', 'a-file.pdf').touch()

    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings.export_folder = Path(tmp_path, 'notes')
    nc.conversion_settings._source = Path(tmp_path, 'file1.html')
    nc.conversion_settings._source_absolute_root = Path(tmp_path)

    files_to_convert = [Path(tmp_path, 'file1.html')]
    file_converter = file_converter_HTML_to_MD.HTMLToMDConverter(nc.conversion_settings, files_to_convert)

    nc.process_files(files_to_convert, file_converter)

    assert nc._note_page_count == 1
    assert Path(tmp_path, 'notes', 'file1.md').exists()
    assert Path(tmp_path, 'notes', 'attachments').exists()
    assert Path(tmp_path, 'notes', 'attachments', 'a-file.pdf').exists()


@pytest.mark.parametrize(
    'silent', [True, False]
)
def test_process_files_copy_attachments_source_and_export_same_folder(tmp_path, silent):
    config.yanom_globals.is_silent = silent
    args = {'source': tmp_path}

    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings.export_folder = Path(tmp_path)

    touch(Path(tmp_path, 'file1.html'))
    file1_content = '<a href="attachments/a-file.pdf">an attachment</a>'
    Path(tmp_path, 'file1.html').write_text(file1_content)
    Path(tmp_path, 'attachments').mkdir()
    Path(tmp_path, 'attachments', 'a-file.pdf').touch()

    nc.conversion_settings._source = Path(tmp_path, 'file1.html')
    nc.conversion_settings._source_absolute_root = Path(tmp_path)

    files_to_convert = [Path(tmp_path, 'file1.html')]
    file_converter = file_converter_HTML_to_MD.HTMLToMDConverter(nc.conversion_settings, files_to_convert)

    nc.process_files(files_to_convert, file_converter)

    assert nc._note_page_count == 1
    assert Path(tmp_path, 'file1.md').exists()


@pytest.mark.parametrize(
    'silent_mode, expected_out', [
        (True, ''),
        (False, f" files found at path")
    ]
)
def test_exit_if_no_files_found_with_no_file(tmp_path, caplog, silent_mode, expected_out):
    config.yanom_globals.is_silent = silent_mode
    test_source_path = tmp_path
    args = {'source': test_source_path}
    touch(Path(tmp_path, 'file1.html'))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)

    files_to_convert = None
    extension = 'html'

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        caplog.clear()
        nc.exit_if_no_files_found(files_to_convert, extension)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0

    assert len(caplog.records) == 1
    assert expected_out in caplog.records[0].message


@pytest.mark.parametrize(
    'input_file, file_converter_type, export_format', [
        ('file1.md', file_converter_MD_to_MD.MDToMDConverter, 'gfm'),
        ('file1.md', file_converter_MD_to_HTML.MDToHTMLConverter, 'html'),
    ]
)
def test_convert_markdown(tmp_path, input_file, file_converter_type, export_format):
    test_source_path = tmp_path
    args = {'source': test_source_path}
    touch(Path(tmp_path, input_file))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)
    nc.conversion_settings.export_format = export_format

    with patch('notes_converter.NotesConvertor.process_files', spec=True) as mock_process_files:
        nc.convert_markdown()

    args = mock_process_files.call_args.args
    assert args[0] == {Path(tmp_path, input_file)}
    assert isinstance(args[1], file_converter_type)


@pytest.mark.parametrize(
    'input_file, file_converter_type, export_format, conversion_input', [
        ('file1.md', file_converter_MD_to_MD.MDToMDConverter, 'gfm', 'markdown'),
        ('file1.html', file_converter_HTML_to_MD.HTMLToMDConverter, 'html', 'html'),
        ('file1.md', file_converter_MD_to_HTML.MDToHTMLConverter, 'html', 'markdown')
    ]
)
def test_convert_notes(tmp_path, input_file, file_converter_type, export_format, conversion_input):
    test_source_path = tmp_path
    args = {'silent': True, 'ini': False, 'source': test_source_path}
    touch(Path(tmp_path, input_file))
    nc = notes_converter.NotesConvertor(args, 'config_data')
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._working_directory = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)
    nc.conversion_settings.export_format = export_format
    nc.conversion_settings.conversion_input = conversion_input

    with patch('notes_converter.NotesConvertor.process_files', spec=True) as mock_process_files:
        with patch('notes_converter.NotesConvertor.evaluate_command_line_arguments', spec=True) \
                as mock_evaluate_command_line_arguments:
            nc.convert_notes()

            mock_evaluate_command_line_arguments.assert_called_once()
            mock_evaluate_command_line_arguments.assert_called_once()
            mock_process_files.assert_called_once()
            args = mock_process_files.call_args.args
            assert args[0] == {Path(tmp_path, input_file)}
            assert isinstance(args[1], file_converter_type)


def test_convert_notes_nsx_file_type(tmp_path, capsys, caplog):
    test_source_path = tmp_path
    input_file = 'file1.nsx'
    args = {'silent': True, 'ini': False, 'source': test_source_path}
    touch(Path(tmp_path, input_file))
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)
    nc.conversion_settings.conversion_input = 'nsx'

    with patch('notes_converter.NotesConvertor.process_nsx_files', spec=True) as mock_process_nsx_files:
        with patch('notes_converter.NotesConvertor.evaluate_command_line_arguments', spec=True):
            caplog.clear()
            nc.convert_notes()

    mock_process_nsx_files.assert_called_once()
    assert len(nc._nsx_backups) == 1

    captured = capsys.readouterr()

    assert 'Processing Completed' in caplog.records[-1].message
    assert 'Found pandoc' in captured.out


def test_get_list_of_orphan_files(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').touch()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').touch()
    Path(tmp_path, 'some_folder/three.png').touch()
    Path(tmp_path, 'some_folder/attachments/four.csv').touch()
    Path(tmp_path, 'some_folder/four.csv').touch()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    test_source_path = tmp_path
    args = {'silent': True, 'ini': False, 'source': test_source_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)
    nc._exported_files = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md'),
                          Path(tmp_path, 'some_folder/data/my_notebook/note.md'),
                          }
    nc._attachment_details = {
        'nine.md': {
            'copyable_absolute': {
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf'),
            },
            'non_copyable_absolute': {'fake'},
        },
    }
    expected_files = {Path(tmp_path, 'some_folder/attachments/four.csv'),
                      Path(tmp_path, 'some_folder/data/my_notebook/six.csv'),
                      Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf'),
                      Path(tmp_path, 'some_folder/attachments/four.csv'),
                      Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png'),
                      Path(tmp_path, 'some_folder/data/attachments/two.csv'),
                      Path(tmp_path, 'some_folder/three.png'),
                      }

    set_of_all_files = content_link_management.get_set_of_all_files(tmp_path)
    files = nc.get_list_of_orphan_files(set_of_all_files)

    assert len(files) == 7
    for file in expected_files:
        assert file in files


def test_handle_orphan_files_as_required_orphans_set_to_orphans_folder(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').touch()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').touch()
    Path(tmp_path, 'some_folder/three.png').touch()
    Path(tmp_path, 'some_folder/attachments/four.csv').touch()
    Path(tmp_path, 'some_folder/four.csv').touch()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    test_source_path = tmp_path
    args = {'silent': True, 'ini': False, 'source': test_source_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)
    nc.conversion_settings.export_folder = Path(tmp_path, 'notes')
    nc._exported_files = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md'),
                          Path(tmp_path, 'some_folder/data/my_notebook/note.md')}
    nc._attachment_details = {
        'nine.md': {
            'copyable_absolute': {
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf'),
            },
            'non_copyable_absolute': {'fake'},
        },
    }
    nc.conversion_settings.orphans = 'orphan'

    nc.handle_orphan_files_as_required()

    assert len(nc._orphan_files) == 7

    assert Path(tmp_path, 'notes/orphan/some_folder/data/my_notebook/attachments/one.png').exists()
    assert Path(tmp_path, 'notes/orphan/some_folder/data/attachments/two.csv').exists()
    assert Path(tmp_path, 'notes/orphan/some_folder/three.png').exists()
    assert Path(tmp_path, 'notes/orphan/some_folder/attachments/four.csv').exists()
    assert Path(tmp_path, 'notes/orphan/some_folder/four.csv').exists()
    assert Path(tmp_path, 'notes/orphan/some_folder/data/my_other_notebook/attachments/five.pdf').exists()
    assert Path(tmp_path, 'notes/orphan/some_folder/data/my_notebook/six.csv').exists()

    # Also check original files are also inplace - the originals are not moved we only copy them
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').exists()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').exists()
    Path(tmp_path, 'some_folder/three.png').exists()
    Path(tmp_path, 'some_folder/attachments/four.csv').exists()
    Path(tmp_path, 'some_folder/four.csv').exists()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').exists()


def test_handle_orphan_files_as_required_orphans_copy(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').touch()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').touch()
    Path(tmp_path, 'some_folder/three.png').touch()
    Path(tmp_path, 'some_folder/attachments/four.csv').touch()
    Path(tmp_path, 'some_folder/four.csv').touch()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    test_source_path = tmp_path
    args = {'silent': True, 'ini': False, 'source': test_source_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)
    nc.conversion_settings.export_folder = Path(tmp_path, 'notes')
    nc._exported_files = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md'),
                          Path(tmp_path, 'some_folder/data/my_notebook/note.md')}
    nc._attachment_details = {
        'nine.md': {
            'copyable_absolute': {
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf'),
            },
            'non_copyable_absolute': {'fake'},
        },
    }
    nc.conversion_settings.orphans = 'copy'

    nc.handle_orphan_files_as_required()

    assert len(nc._orphan_files) == 7

    assert Path(tmp_path, 'notes/some_folder/data/my_notebook/attachments/one.png').exists()
    assert Path(tmp_path, 'notes/some_folder/data/attachments/two.csv').exists()
    assert Path(tmp_path, 'notes/some_folder/three.png').exists()
    assert Path(tmp_path, 'notes/some_folder/attachments/four.csv').exists()
    assert Path(tmp_path, 'notes/some_folder/four.csv').exists()
    assert Path(tmp_path, 'notes/some_folder/data/my_other_notebook/attachments/five.pdf').exists()
    assert Path(tmp_path, 'notes/some_folder/data/my_notebook/six.csv').exists()

    # Also check original files are also inplace - the originals are not moved we only copy them
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').exists()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').exists()
    Path(tmp_path, 'some_folder/three.png').exists()
    Path(tmp_path, 'some_folder/attachments/four.csv').exists()
    Path(tmp_path, 'some_folder/four.csv').exists()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').exists()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').exists()


def test_handle_orphan_files_as_required_orphans_ignore(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').touch()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').touch()
    Path(tmp_path, 'some_folder/three.png').touch()
    Path(tmp_path, 'some_folder/attachments/four.csv').touch()
    Path(tmp_path, 'some_folder/four.csv').touch()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    test_source_path = tmp_path
    args = {'silent': True, 'ini': False, 'source': test_source_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.conversion_settings = conversion_settings.ConversionSettings()
    nc.conversion_settings._source = Path(tmp_path)
    nc.conversion_settings._source_absolute_root = Path(tmp_path)
    nc.conversion_settings.export_folder = Path(tmp_path, 'notes')
    nc._exported_files = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md'),
                          Path(tmp_path, 'some_folder/data/my_notebook/note.md')}
    nc._attachment_details = {
        'nine.md': {
            'copyable_absolute': {
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png'),
                Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf'),
            },
            'non_copyable_absolute': {'fake'},
        },
    }
    nc.conversion_settings.orphans = 'ignore'

    nc.handle_orphan_files_as_required()

    assert len(nc._orphan_files) == 7

    assert not Path(tmp_path, 'notes/some_folder/data/my_notebook/attachments/one.png').exists()
    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').exists()

@pytest.mark.parametrize(
    'conversion_count, message, expected', [
        (1, 'message', '1 message'),
        (2, 'message', '2 messages'),
    ]
)
def test_print_result_if_any(conversion_count, message, expected, capsys, tmp_path):
    args = {'silent': True, 'ini': False, 'source': tmp_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.print_result_if_any(conversion_count, message)
    captured = capsys.readouterr()
    assert expected in captured.out


def test_print_result_if_any_no_message_expected(capsys, tmp_path):
    args = {'silent': True, 'ini': False, 'source': tmp_path}
    cd = config_data.ConfigData(f"{config.yanom_globals.data_dir}/config.ini", 'gfm', allow_no_value=True)
    nc = notes_converter.NotesConvertor(args, cd)
    nc.print_result_if_any(0, 'message')
    captured = capsys.readouterr()
    assert 'message' not in captured.out
