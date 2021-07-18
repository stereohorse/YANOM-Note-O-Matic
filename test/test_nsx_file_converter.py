import logging
from mock import patch
from pathlib import Path
import pytest

import config
import nsx_file_converter
import pandoc_converter
import sn_note_page
import sn_notebook


@pytest.fixture
def all_notes_dict(all_notes):
    return {id(note): note for note in all_notes}


def test_build_dictionary_of_inter_note_links(conv_setting, all_notes_dict, ):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')
    nsx_fc._note_pages = all_notes_dict
    nsx_fc.build_dictionary_of_inter_note_links()

    assert len(nsx_fc._inter_note_link_processor.replacement_links) == 9
    assert len(nsx_fc._inter_note_link_processor.renamed_links_not_corrected) == 1


def test_generate_note_page_filename_and_path(nsx, conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    # Note with no links
    note_page_1_json = {'parent_id': 'note_book1', 'title': 'Page 1 title', 'mtime': 1619298559, 'ctime': 1619298539,
                        'attachment': {}, 'content': 'content', 'tag': [1]}
    note_page_1 = sn_note_page.NotePage(nsx, 1, note_page_1_json)
    note_page_1.notebook_folder_name = 'note_book1'
    note_page_1._raw_content = """<div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div>"""

    nsx_fc._note_pages = {id(note_page_1): note_page_1}
    nsx_fc.generate_note_page_filename_and_path()

    for note in nsx_fc._note_pages.values():
        assert note.file_name == Path('Page 1 title.md')


def test_generate_note_page_filename_and_path_duplicate_titles(nsx, conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    note_page_1_json = {'parent_id': 'note_book1', 'title': 'Page 1 title', 'mtime': 1619298559, 'ctime': 1619298539,
                        'attachment': {}, 'content': 'content', 'tag': [1]}
    note_page_1 = sn_note_page.NotePage(nsx, 1, note_page_1_json)
    note_page_1.notebook_folder_name = 'note_book1'
    note_page_1._raw_content = """<div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div>"""

    note_page_2_json = {'parent_id': 'note_book1', 'title': 'Page 1 title', 'mtime': 1619298559, 'ctime': 1619298539,
                        'attachment': {}, 'content': 'content', 'tag': [1]}
    note_page_2 = sn_note_page.NotePage(nsx, 1, note_page_2_json)
    note_page_2.notebook_folder_name = 'note_book1'
    note_page_2._raw_content = """<div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div>"""

    nsx_fc._note_pages = {
        id(note_page_1): note_page_1,
        id(note_page_2): note_page_2
    }

    nsx_fc.generate_note_page_filename_and_path()

    assert nsx_fc._note_pages[id(note_page_1)]._file_name == Path('Page 1 title.md')
    assert nsx_fc._note_pages[id(note_page_2)]._file_name == Path('Page 1 title-1.md')


def test_fetch_json_data(conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    with patch('zip_file_reader.read_json_data', spec=True, return_value='fake_json'):
        result = nsx_fc.fetch_json_data('data_id')

        assert result == 'fake_json'


def test_fetch_attachment_file(conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    with patch('zip_file_reader.read_binary_file', spec=True, return_value='fake_binary'):
        result = nsx_fc.fetch_attachment_file('data_id', 'note title')

        assert result == 'fake_binary'


def test_add_notebooks(conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc._notebook_ids = ['1234', 'abcd']
    with patch('zip_file_reader.read_json_data', spec=True, return_value={'title': "notebook"}):
        nsx_fc.add_notebooks()

    assert len(nsx_fc._notebooks) == 2


def test_add_recycle_bin_notebook(conv_setting, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')
    with patch('zip_file_reader.read_json_data', autospec=True, return_value=None):
        nsx_fc.add_recycle_bin_notebook()

    assert "Creating recycle bin notebook" in caplog.messages

    assert len(nsx_fc._notebooks) == 1
    assert 'recycle-bin' in nsx_fc._notebooks.keys()


def test_create_export_folder_if_not_exist(conv_setting, caplog, tmp_path):
    config.yanom_globals.logger_level = logging.DEBUG
    Path(tmp_path, config.yanom_globals.data_dir).mkdir()

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc.conversion_settings.working_directory = tmp_path
    nsx_fc.conversion_settings.export_folder = 'notes'

    nsx_fc.create_export_folder_if_not_exist()

    assert Path(tmp_path, config.yanom_globals.data_dir, 'notes').exists()

    assert "Creating export folder if it does not exist" in caplog.messages


def test_create_export_folder_if_not_exist_force_exception_invalid_path_missing_parent_dir(conv_setting, caplog,
                                                                                           tmp_path):
    config.yanom_globals.logger_level = logging.DEBUG
    Path(tmp_path, config.yanom_globals.data_dir).mkdir()

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc.conversion_settings.working_directory = tmp_path
    nsx_fc.conversion_settings.export_folder = 'notes'
    Path(conv_setting.working_directory, config.yanom_globals.data_dir).rmdir()  # remove a directory to

    expected_error_log_caplog_message = f"Unable to create the export folder there is a problem with the path.\n[Errno 2] No such file or directory: '{Path(conv_setting.working_directory, config.yanom_globals.data_dir, nsx_fc.conversion_settings.export_folder)}'"

    with pytest.raises(SystemExit):
        nsx_fc.create_export_folder_if_not_exist(parents=False)  # use parents false to force error

    # assert "Creating export folder if it does not exist" in caplog.messages
    assert expected_error_log_caplog_message in caplog.messages


def test_create_export_folder_if_not_exist_force_exception_directory_already_exists(conv_setting, caplog, tmp_path):
    config.yanom_globals.logger_level = logging.DEBUG
    Path(tmp_path, config.yanom_globals.data_dir).mkdir()

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc.conversion_settings.working_directory = tmp_path
    nsx_fc.conversion_settings.export_folder = 'notes'

    Path(conv_setting.working_directory, config.yanom_globals.data_dir, 'notes').mkdir()  # make exist

    expected_error_log_caplog_message = f"Export folder already exists - '{Path(conv_setting.working_directory, config.yanom_globals.data_dir, 'notes')}'"

    nsx_fc.create_export_folder_if_not_exist()  # use parents false to force error

    assert expected_error_log_caplog_message in caplog.messages


@pytest.mark.parametrize(
    'silent, expected_out', [
        (True, ''),
        (False, "Unable to create the export folder because path is to an existing file not a directory."),
    ]
)
def test_create_export_folder_if_not_exist_force_exception_path_is_to_existing_file(silent, expected_out, conv_setting, caplog, capsys, tmp_path):
    config.yanom_globals.logger_level = logging.DEBUG
    config.yanom_globals.is_silent = silent
    Path(tmp_path, config.yanom_globals.data_dir).mkdir()

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc.conversion_settings.working_directory = tmp_path
    nsx_fc.conversion_settings.export_folder = 'notes'

    Path(conv_setting.working_directory, config.yanom_globals.data_dir, 'notes').touch()  # make exist as a file

    expected_error_log_caplog_message = f"Unable to create the export folder because path is to an existing file not a directory.\n[Errno 17] File exists: '{Path(conv_setting.working_directory, config.yanom_globals.data_dir, 'notes')}'"

    with pytest.raises(SystemExit):
        nsx_fc.create_export_folder_if_not_exist()

    assert expected_error_log_caplog_message in caplog.messages

    captured = capsys.readouterr()
    assert expected_out in captured.out


def test_create_notebook_folders(conv_setting, caplog, tmp_path, nsx):
    config.yanom_globals.logger_level = logging.DEBUG

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')
    with patch('zip_file_reader.read_json_data', autospec=True, return_value=None):
        test_notebook = sn_notebook.Notebook(nsx, '1234')
        nsx_fc._notebooks = {'1234': test_notebook}

        nsx_fc.create_notebook_and_attachment_folders()

    assert "Creating folders for notebooks" in caplog.messages
    assert nsx_fc.notebooks['1234'].folder_name == Path('Unknown Notebook')
    assert Path(tmp_path, config.yanom_globals.data_dir, conv_setting.export_folder, 'Unknown Notebook').exists()
    assert Path(tmp_path, config.yanom_globals.data_dir, conv_setting.export_folder, 'Unknown Notebook',
                conv_setting.attachment_folder_name).exists()


def test_create_notebook_folders_force_fail_to_create_attachment_folder(conv_setting, caplog, nsx, monkeypatch):
    config.yanom_globals.logger_level = logging.DEBUG

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    with patch('zip_file_reader.read_json_data', autospec=True, return_value=None):
        test_notebook = sn_notebook.Notebook(nsx, '1234')
        nsx_fc._notebooks = {'1234': test_notebook}

        monkeypatch.setattr(sn_notebook.Notebook, 'full_path_to_notebook', None)
        result = nsx_fc.create_notebook_and_attachment_folders()

    assert nsx_fc._notebooks['1234'].full_path_to_notebook is None

    assert "Creating folders for notebooks" in caplog.messages
    # confirm notebook folder was created
    assert Path(conv_setting.working_directory,
                config.yanom_globals.data_dir,
                nsx_fc.conversion_settings.export_folder,
                nsx_fc._notebooks['1234'].folder_name).exists()
    # confirm the attachment folder was not created
    assert not Path(conv_setting.working_directory,
                    config.yanom_globals.data_dir,
                    nsx_fc.conversion_settings.export_folder,
                    nsx_fc._notebooks['1234'].folder_name,
                    nsx_fc.conversion_settings.attachment_folder_name).exists()
    # confirm the notebook is listed to be skipped
    assert result == ['1234']


def test_remove_notebooks_to_be_skipped(conv_setting, nsx):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': 'Notebook Title'}):
        test_notebook1 = sn_notebook.Notebook(nsx, '1234')
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': 'Notebook Title2'}):
        test_notebook2 = sn_notebook.Notebook(nsx, '7890')

    nsx_fc._notebooks = {'1234': test_notebook1, '7890': test_notebook2}
    notebooks_to_skip = ['1234']
    nsx_fc.remove_notebooks_to_be_skipped(notebooks_to_skip)
    assert nsx_fc._notebooks == {'7890': test_notebook2}


@pytest.mark.parametrize(
    'silent_mode', [True, False]
)
def test_add_note_pages(conv_setting, caplog, silent_mode):
    config.yanom_globals.logger_level = logging.DEBUG
    config.yanom_globals.is_silent = silent_mode

    nsx_fc = nsx_file_converter.NSXFile(Path('fake_file'), conv_setting, 'fake_pandoc_converter')

    nsx_fc._note_page_ids = ['1234']

    with patch('zip_file_reader.read_json_data',
               spec=True,
               return_value={'title': 'note title',
                             'ctime': 1620808218,
                             'mtime': 1620808218,
                             'parent_id': '1234',
                             'encrypt': False
                             }
               ):
        caplog.clear()
        nsx_fc.add_note_pages()

    assert nsx_fc.note_page_count == 1

    assert nsx_fc.note_pages['1234'].title == 'note title'

    assert caplog.records[0].message == 'Creating note page objects'


@pytest.mark.parametrize(
    'silent_mode', [True, False]
)
def test_add_note_pages_missing_data_in_nsx_file(conv_setting, caplog, silent_mode):
    config.yanom_globals.logger_level = logging.DEBUG
    config.yanom_globals.is_silent = silent_mode

    nsx_fc = nsx_file_converter.NSXFile(Path('fake_file'), conv_setting, 'fake_pandoc_converter')

    nsx_fc._note_page_ids = ['1234']

    with patch('zip_file_reader.read_json_data',
               spec=True,
               return_value=None,
               ):
        caplog.clear()
        nsx_fc.add_note_pages()

    assert nsx_fc.note_page_count == 0
    expected_log_message = msg = f"There are {len(nsx_fc._note_page_ids) - len(nsx_fc._note_pages)} less note pages to process " \
                      f"than note page id's in the nsx file.\nPlease review log file as there may be issues " \
                      f"with the nsx file."
    assert 'Creating note page objects' in caplog.messages
    assert f"Unable to locate note data for note id '1234' from nsx file'{nsx_fc._nsx_file_name.name}'. No note data to process " in caplog.messages
    assert expected_log_message in caplog.messages


def test_add_note_pages_encrypted_note(conv_setting, caplog):
    config.yanom_globals.logger_level = logging.DEBUG

    nsx_fc = nsx_file_converter.NSXFile(Path('fake_file'), conv_setting, 'fake_pandoc_converter')

    nsx_fc._note_page_ids = ['1234']

    with patch('zip_file_reader.read_json_data', spec=True,
               return_value={'title': 'note title', 'ctime': 1620808218, 'mtime': 1620808218, 'parent_id': '1234',
                             'encrypt': True}):
        caplog.clear()
        nsx_fc.add_note_pages()

    assert nsx_fc.note_page_count == 0

    assert len(nsx_fc.note_pages) == 0

    assert 'Creating note page objects' in caplog.messages
    assert "The Note - 'note title' - is encrypted and has not been converted." in caplog.messages

    assert nsx_fc._encrypted_notes == ['note title']


def test_add_note_pages_encrypted_note_no_encrypt_key_in_note_data(conv_setting, caplog):
    config.yanom_globals.logger_level = logging.DEBUG

    nsx_fc = nsx_file_converter.NSXFile(Path('fake_file'), conv_setting, 'fake_pandoc_converter')

    nsx_fc._note_page_ids = ['1234']

    with patch('zip_file_reader.read_json_data', spec=True,
               return_value={'title': 'note title', 'ctime': 1620808218, 'mtime': 1620808218, 'parent_id': '1234'}):
        caplog.clear()
        nsx_fc.add_note_pages()

    assert nsx_fc.note_page_count == 1

    assert len(nsx_fc.note_pages) == 1

    assert 'Creating note page objects' in caplog.messages
    assert f"The Note - 'note title' - has no encryption flag, it may or may not be encrypted. Assuming it is not." in caplog.messages


@pytest.fixture
def note_pages(all_notes):
    return {id(note): note for note in all_notes}


@pytest.fixture
def notebooks(nsx):
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': 'notebook 1'}):
        test_notebook1 = sn_notebook.Notebook(nsx, 'note_book1')
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': 'recycle bin'}):
        test_notebook2 = sn_notebook.Notebook(nsx, 'recycle-bin')
    return {'note_book1': test_notebook1, 'recycle-bin': test_notebook2}


def test_add_note_pages_to_notebooks(conv_setting, caplog, note_pages, notebooks):
    config.yanom_globals.logger_level = logging.DEBUG

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')
    nsx_fc._notebooks = notebooks
    nsx_fc._note_pages = note_pages

    caplog.clear()
    nsx_fc.add_note_pages_to_notebooks()

    assert len(nsx_fc.notebooks['note_book1'].note_pages) == 6
    assert len(nsx_fc.notebooks['recycle-bin'].note_pages) == 5

    assert "Add note pages to notebooks" in caplog.records[0].message


def test_process_notebooks(conv_setting, notebooks):

    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')
    nsx_fc._notebooks = notebooks

    with patch('sn_notebook.Notebook.process_notebook_pages', spec=True) as mock_process_notebook_pages:
        nsx_fc.process_notebooks()

        mock_process_notebook_pages.assert_called()
        assert nsx_fc._note_book_count == 2


def test_get_notebook_ids(conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc._nsx_json_data = {"notebook": ["1234", "2345", "3456"]}
    nsx_fc.get_notebook_ids()
    assert nsx_fc._notebook_ids == ["1234", "2345", "3456"]


@pytest.mark.parametrize(
    'nsx_json_data', [
        {"notebook": []},
        {"notebook": None},
        {"tag": ['tag1']}
    ]
)
def test_get_notebook_ids_no_ids(nsx_json_data, conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc._nsx_json_data = nsx_json_data
    nsx_fc.get_notebook_ids()
    assert not nsx_fc._notebook_ids


def test_get_note_page_ids(conv_setting):
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc._nsx_json_data = {"note": ["1234", "2345", "3456"]}
    nsx_fc.get_note_page_ids()
    assert nsx_fc._note_page_ids == ["1234", "2345", "3456"]


@pytest.mark.parametrize(
    'nsx_json_data, silent, expected', [
        ({"note": []}, False, "No note page ID's were found in"),
        ({"note": []}, True, ''),
        ({"note": None}, False, "No note page ID's were found in"),
        ({"tag": ['tag1']}, False, "No note page ID's were found in"),
    ]
)
def test_get_note_page_ids_no_ids(nsx_json_data, conv_setting, silent, expected, capsys, caplog):
    config.yanom_globals.is_silent = silent
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')

    nsx_fc._nsx_json_data = nsx_json_data
    nsx_fc.get_note_page_ids()
    assert not nsx_fc._note_page_ids
    assert f"No note page ID's were found in fake_file. nsx file can not be processed" in caplog.messages

    captured = capsys.readouterr()
    assert expected in captured.out


@pytest.mark.parametrize(
    'silent_mode', [True, False]
)
def test_save_note_pages(notebooks, all_notes_dict, conv_setting, silent_mode):
    config.yanom_globals.is_silent = silent_mode
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, 'fake_pandoc_converter')
    nsx_fc._notebooks = notebooks
    nsx_fc._note_pages = all_notes_dict
    nsx_fc.add_note_pages_to_notebooks()

    with patch('file_writer.store_file', spec=True) as mock_store_file:
        nsx_fc.save_note_pages()

        assert mock_store_file.call_count == 11

#
# @pytest.mark.parametrize(
#     'silent_mode, expected', [
#         (True, ''),
#         (False, 'Saving attachments'),
#     ]
# )
# def test_store_attachments(notebooks, all_notes_dict, conv_setting, silent_mode, expected, capsys):
#     with capsys.disabled():
#         config.yanom_globals.is_silent = silent_mode
#         pc = pandoc_converter.PandocConverter(conv_setting)
#         nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, pc)
#         nsx_fc._notebooks = notebooks
#         nsx_fc._note_pages = all_notes_dict
#         nsx_fc.add_note_pages_to_notebooks()
#         nsx_fc.process_notebooks()
#         attachments = nsx_fc.build_list_of_attachments()
#
#     with patch('nsx_file_converter.NSXFile.fetch_attachment_file', autospec=True):
#         with patch('file_writer.store_file', spec=True) as mock_store_file:
#             nsx_fc.store_attachments(attachments)
#
#         assert mock_store_file.call_count == 4
#
#         captured = capsys.readouterr()
#         assert expected in captured.out
#
#
# def test_store_attachments_attachment_paths_are_exiting_directory(notebooks, all_notes_dict, conv_setting,
#                                                                   caplog, tmp_path):
#     pc = pandoc_converter.PandocConverter(conv_setting)
#     nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, pc)
#     nsx_fc._notebooks = notebooks
#     nsx_fc._note_pages = all_notes_dict
#     nsx_fc.add_note_pages_to_notebooks()
#     nsx_fc.process_notebooks()
#
#     with patch('nsx_file_converter.NSXFile.fetch_attachment_file', autospec=True):
#         with patch('file_writer.store_file', spec=True) as mock_store_file:
#             for note_page_id in nsx_fc._note_pages:
#                 for attachment in nsx_fc._note_pages[note_page_id].attachments.values():
#                     attachment._full_path = tmp_path
#
#             attachments = nsx_fc.build_list_of_attachments()
#
#             caplog.clear()
#             nsx_fc.store_attachments(attachments)
#
#             assert mock_store_file.call_count == 0
#             assert "Unable to save attachment for the note" in caplog.messages[0]
#             assert len(caplog.records) == 4


@pytest.mark.parametrize(
    'silent_mode', [True, False]
)
def test_store_attachments(notebooks, all_notes_dict, conv_setting, silent_mode):
    config.yanom_globals.is_silent = silent_mode
    pc = pandoc_converter.PandocConverter(conv_setting)
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, pc)
    nsx_fc._notebooks = notebooks
    nsx_fc._note_pages = all_notes_dict
    nsx_fc.add_note_pages_to_notebooks()
    with patch('nsx_file_converter.NSXFile.fetch_attachment_file', autospec=True):
        with patch('file_writer.store_file', spec=True) as mock_store_file:
            nsx_fc.process_notebooks()

        assert mock_store_file.call_count == 4


def test_process_nsx_file_no_config_json(conv_setting, caplog):
    pc = pandoc_converter.PandocConverter(conv_setting)
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, pc)
    with patch('nsx_file_converter.NSXFile.fetch_json_data', autospec=True, return_value=None):
        nsx_fc.process_nsx_file()

    assert f"No config.json found in nsx file '{nsx_fc._nsx_file_name}'. Skipping nsx file" in caplog.messages


def test_process_nsx_file_no_notebook_ids(conv_setting, caplog):
    pc = pandoc_converter.PandocConverter(conv_setting)
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, pc)
    with patch('nsx_file_converter.NSXFile.fetch_json_data', autospec=True, return_value={'tag': 'tag1'}):
        nsx_fc.process_nsx_file()

    assert f"No notebook ids found in nsx file '{nsx_fc._nsx_file_name}'. Skipping nsx file" in caplog.messages


def test_process_nsx_file_no_note_page_ids(conv_setting, caplog):
    pc = pandoc_converter.PandocConverter(conv_setting)
    nsx_fc = nsx_file_converter.NSXFile('fake_file', conv_setting, pc)
    with patch('nsx_file_converter.NSXFile.fetch_json_data', autospec=True, return_value={'notebook': '1234', 'tag': 'tag1'}):
        nsx_fc.process_nsx_file()

    assert f"No note page ids found in nsx file '{nsx_fc._nsx_file_name}'. Skipping nsx file" in caplog.messages
