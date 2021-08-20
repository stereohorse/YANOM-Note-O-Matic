import logging
from mock import patch
from pathlib import Path
import pytest

import config
import sn_note_page
import sn_notebook


def test_create_notebook_folder_folder_does_not_already_exist(tmp_path, nsx, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'abcd')

        notebook.conversion_settings.export_folder = 'export-folder'
        notebook.folder_name = Path('notebook1')

        Path(tmp_path, config.yanom_globals.data_dir, notebook.conversion_settings.export_folder).mkdir(parents=True, exist_ok=True)

        notebook.create_notebook_folder()

    assert Path(tmp_path, config.yanom_globals.data_dir, notebook.conversion_settings.export_folder, notebook.folder_name).exists()

    assert notebook.folder_name == Path('notebook1')
    assert notebook._full_path_to_notebook == Path(tmp_path, config.yanom_globals.data_dir, notebook.conversion_settings.export_folder, notebook.folder_name)

    assert f'Creating notebook folder for {notebook_title}' in caplog.messages


def test_create_notebook_folder_folder_already_exist(tmp_path, nsx, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'abcd')

        notebook.conversion_settings.export_folder = 'export-folder'
        notebook.conversion_settings.renaming = 'rename'
        notebook.folder_name = 'notebook1'

        Path(tmp_path, config.yanom_globals.data_dir, notebook.conversion_settings.export_folder, notebook.folder_name).mkdir(parents=True, exist_ok=True)
        expected_folder_name = Path('notebook1-1')

        notebook.create_notebook_folder()

    assert Path(tmp_path, config.yanom_globals.data_dir, notebook.conversion_settings.export_folder,
                expected_folder_name).exists()

    assert notebook.folder_name == expected_folder_name
    assert notebook._full_path_to_notebook == Path(tmp_path, config.yanom_globals.data_dir,
                                                   notebook.conversion_settings.export_folder, expected_folder_name)

    assert f'Creating notebook folder for {notebook_title}' in caplog.messages


def test_create_notebook_folder_folder_unable_to_create_folder(tmp_path, nsx, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'abcd')

        notebook.conversion_settings.export_folder = 'export-folder'
        notebook.folder_name = 'notebook1'

        expected_folder_name = None

        notebook.create_notebook_folder(parents=False)

    assert notebook.folder_name == 'notebook1'
    assert notebook._full_path_to_notebook is None

    assert f"Unable to create notebook folder there is a problem with the path.\n[Errno 2] No such file or directory: '{Path(tmp_path, config.yanom_globals.data_dir, 'export-folder', 'notebook1')}'" in caplog.messages


def test_create_attachment_folder(tmp_path, nsx, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'abcd')
        notebook._full_path_to_notebook = Path(tmp_path, config.yanom_globals.data_dir,
                                               notebook.conversion_settings.export_folder, 'notebook1')
        notebook._full_path_to_notebook.mkdir(parents=True, exist_ok=True)
        notebook.conversion_settings.attachment_folder_name = 'attachments'

        notebook.create_attachment_folder()

    assert Path(tmp_path, config.yanom_globals.data_dir,
                notebook.conversion_settings.export_folder,
                'notebook1', 'attachments').exists()

    assert f'Creating attachment folder' in caplog.messages


def test_create_attachment_folder_when_note_book_folder_not_created(tmp_path, nsx, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'abcd')
        notebook._full_path_to_notebook = ''
        notebook.conversion_settings.attachment_folder_name = 'attachments'

        notebook.create_attachment_folder()

    assert not Path(tmp_path, config.yanom_globals.data_dir, notebook.conversion_settings.export_folder, 'notebook1', 'attachments').exists()

    assert f"Attachment folder for '{notebook_title}' was not created as the notebook folder has not been created" in caplog.messages
    assert f'Creating attachment folder' not in caplog.messages


def test_pair_up_note_pages_and_notebooks_note_title_does_not_already_exist(nsx):
    note_jason = {'parent_id': 'note_book2', 'title': 'Page 8 title',
                        'mtime': 1619298559, 'ctime': 1619298539, 'attachment': {}, 'content': 'content', 'tag': [9]}
    note_page = sn_note_page.NotePage(nsx, '1234', note_jason)
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'notebook_id_abcd')
        notebook.folder_name = Path('notebook_folder')

        notebook.note_titles = ['abcd']

        notebook.pair_up_note_pages_and_notebooks(note_page)

    assert note_page.notebook_folder_name == Path('notebook_folder')
    assert note_page.parent_notebook_id == 'notebook_id_abcd'

    assert note_page.title in notebook.note_titles
    assert note_page in notebook.note_pages


def test_pair_up_note_pages_and_notebooks_note_title_already_exists(nsx):
    note_jason = {'parent_id': 'note_book2', 'title': 'Page 8 title',
                        'mtime': 1619298559, 'ctime': 1619298539, 'attachment': {}, 'content': 'content', 'tag': [9]}
    note_page = sn_note_page.NotePage(nsx, '1234', note_jason)
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'notebook_id_abcd')
        notebook.folder_name = Path('notebook_folder')

        notebook.note_titles = ['abcd', 'Page 8 title', 'Page 8 title-1']

        notebook.pair_up_note_pages_and_notebooks(note_page)

    assert note_page.notebook_folder_name == Path('notebook_folder')
    assert note_page.parent_notebook_id == 'notebook_id_abcd'

    assert note_page.title == 'Page 8 title-2'
    assert note_page.title in notebook.note_titles
    assert note_page in notebook.note_pages


@pytest.mark.parametrize(
    'silent_mode, expected', [
        (True, ''),
        (False, "Processing 'notebook1' Notebook")
    ]
)
def test_process_notebook_pages(all_notes, tmp_path, nsx, silent_mode, expected, capsys, caplog):
    config.yanom_globals.is_silent = silent_mode
    notebook_title = 'notebook1'
    with patch('zip_file_reader.read_json_data', autospec=True, return_value={'title': notebook_title}):
        notebook = sn_notebook.Notebook(nsx, 'notebook_id_abcd')
        notebook.folder_name = 'notebook_folder'
        notebook.note_pages = all_notes

        with patch('sn_note_page.NotePage.process_note', spec=True) as mock_process_note:
            notebook.process_notebook_pages()

        mock_process_note.assert_called()

    assert f"Processing note book {notebook.title} - {notebook.notebook_id}" in caplog.messages

    captured = capsys.readouterr()
    assert expected in captured.out


@pytest.mark.parametrize(
    'json, expected', [
        (None, {'title': 'Unknown Notebook'}),
        ({'title': 'notebook'}, {'title': 'notebook'}),
    ]
)
def test_fetch_notebook_json(nsx, json, expected):
    with patch('zip_file_reader.read_json_data', autospec=True, return_value=json):
        notebook = sn_notebook.Notebook(nsx, 'id-1234')
        result = notebook.fetch_notebook_json('id-1234')

    assert result == expected


@pytest.mark.parametrize(
    'json, expected', [
        ({'title': 'notebook'}, 'notebook'),
        ({'title': ''}, 'My Notebook'),
        ({'tag': 'tag1'}, 'Unknown Notebook'),
    ]
)
def test_fetch_notebook_title(nsx, json, expected):
    with patch('zip_file_reader.read_json_data', autospec=True, return_value=json):
        notebook = sn_notebook.Notebook(nsx, 'id-1234')
        notebook._notebook_json = json
        result = notebook.fetch_notebook_title()

    assert result == expected


def test_init_notebook_for_recycle_bin(nsx):
    notebook = sn_notebook.Notebook(nsx, 'recycle-bin')

    assert notebook.title == 'recycle-bin'
