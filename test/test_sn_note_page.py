import logging
from packaging import version
from pathlib import Path

from mock import patch
import pytest

import config
import nsx_pre_processing
import pandoc_converter
import sn_notebook
import sn_note_page
import zip_file_reader


@pytest.fixture
def notebook(nsx, monkeypatch):
    def fake_json_data(_ignored, _ignored2):
        return None

    monkeypatch.setattr(zip_file_reader, 'read_json_data', fake_json_data)
    # patch will cause notebook name to be "Unknown Notebook' with no json data
    notebook = sn_notebook.Notebook(nsx, 'note_book2')
    return notebook


@pytest.fixture
def note_page(nsx, notebook):
    note_jason = {'parent_id': 'note_book2', 'title': 'Page 8 title',
                  'mtime': 1619298640, 'ctime': 1619298559, 'attachment': {'test': 'test_value'}, 'content': 'content',
                  'tag': [9]}
    np = sn_note_page.NotePage(nsx, '1234', note_jason)
    np.parent_notebook = notebook
    return np


@pytest.fixture
def note_page_1(nsx, notebook):
    note_page_1_json = {
        'parent_id': 'note_book1',
        'title': 'Page 1 title',
        'mtime': 1619298559,
        'ctime': 1619298539,
        'content': 'content',
        'tag': ['1'],
        'attachment': {
            "_-m4Hhgmp34U85IwTdWfbWw": {
                "md5": "e79072f793f22434740e64e93cfe5926",
                "name": "ns_attach_image_787491613404344687.png",
                "size": 186875,
                "width": 1848,
                "height": 1306,
                "type": "image/png",
                "ctime": 1616084097,
                "ref": "MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n"
            },
            "_YOgkfaY7aeHcezS-jgGSmA": {
                "md5": "6c4b828f227a096d3374599cae3f94ec",
                "name": "Record 2021-02-15 16:00:13.webm",
                "size": 9627,
                "width": 0,
                "height": 0,
                "type": "video/webm",
                "ctime": 1616084097,
            },
            "_yITQrdarvsdg3CkL-ifh4Q": {
                "md5": "c4ee8b831ad1188509c0f33f0c072af5",
                "name": "example-attachment.pdf",
                "size": 14481,
                "width": 0,
                "height": 0,
                "type": "application/pdf",
                "ctime": 1616084097,
            },
            "file_dGVzdCBwYWdlLnBkZjE2MTkyOTg3MjQ2OTE=": {
                "md5": "27a9aadc878b718331794c8bc50a1b8c",
                "name": "test page.pdf",
                "size": 320357,
                "width": 0,
                "height": 0,
                "type": "application/pdf",
                "ctime": 1619295124,
            },
        },
        }
    note_page_1 = sn_note_page.NotePage(nsx, 1, note_page_1_json)
    note_page_1.notebook_folder_name = 'note_book1'
    note_page_1._file_name = 'page-1-title.md'
    note_page_1._raw_content = """<div>Below is a hyperlink to the internet</div><div><a href=\"https://github.com/kevindurston21/YANOM-Note-O-Matic\">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></div>"""
    note_page_1.parent_notebook = notebook

    return note_page_1


@pytest.mark.parametrize(
    'front_matter_format, creation_time_in_exported_file_name, expected_ctime, expected_mtime', [
        ('none', False, 1619298559, 1619298640),
        ('none', True, '202104242209', '202104242210'),
        ('yaml', True, '202104242209', '202104242210'),
        ('yaml', False, '202104242209', '202104242210'),
    ]
)
def test_init_note_page(nsx, front_matter_format, creation_time_in_exported_file_name, expected_ctime, expected_mtime):
    nsx.conversion_settings.front_matter_format = front_matter_format
    nsx.conversion_settings._creation_time_in_exported_file_name = creation_time_in_exported_file_name
    note_jason = {'parent_id': 'note_book2', 'title': 'Page 8 title',
                  'mtime': 1619298640, 'ctime': 1619298559, 'attachment': {'test': 'test_value'}, 'content': 'content',
                  'tag': [9]}
    note_page = sn_note_page.NotePage(nsx, '1234', note_jason)

    assert note_page.note_json['ctime'] == expected_ctime
    assert note_page.note_json['mtime'] == expected_mtime

    assert note_page.title == 'Page 8 title'
    assert note_page.original_title == 'Page 8 title'
    assert note_page.raw_content == 'content'
    assert note_page.parent_notebook_id == 'note_book2'
    assert note_page._attachments_json == {'test': 'test_value'}


@pytest.mark.parametrize(
    'export_format, extension, time, optional_dash,  ctime', [
        ('html', 'html', '20210815', '-', True),
        ('html', 'html', '', '', False),
        ('gfm', 'md', '', '', False),
    ]
)
def test_generate_filenames_and_paths(export_format, extension, time, optional_dash,  ctime, note_page):
    note_page.conversion_settings.export_format = export_format
    note_page.notebook_folder_name = 'note_book2'
    note_page._note_json['ctime'] = time
    note_page.conversion_settings.creation_time_in_exported_file_name = ctime

    note_page.generate_filenames_and_paths([''])

    assert note_page.file_name == Path(f"{time}{optional_dash}{note_page.title}.{extension}")
    assert note_page.full_path == Path(note_page.conversion_settings.working_directory, config.yanom_globals.data_dir,
                                       note_page.conversion_settings.export_folder, note_page.notebook_folder_name,
                                       note_page.file_name)


def test_create_attachments(note_page_1):
    with patch('sn_attachment.ImageNSAttachment', spec=True):
        with patch('sn_attachment.FileNSAttachment', spec=True):
            image_count, file_count = note_page_1.create_attachments()

    assert image_count == 1
    assert file_count == 3


def test_create_attachments_no_note_json_for_attachments(note_page_1):
    note_page_1._attachments_json = None
    with patch('sn_attachment.ImageNSAttachment', spec=True):
        with patch('sn_attachment.FileNSAttachment', spec=True):
            image_count, file_count = note_page_1.create_attachments()

    assert image_count == 0
    assert file_count == 0


def test_process_attachments(note_page_1):
    with patch('sn_attachment.ImageNSAttachment', spec=True) as mock_image_attachment:
        with patch('sn_attachment.FileNSAttachment', spec=True) as mock_file_attachment:
            _ignored_1, _ignored_2 = note_page_1.create_attachments()

            note_page_1.process_attachments()

            mock_image_attachment.assert_called_once()
            assert mock_file_attachment.call_count == 3


def test_pre_process_content(note_page):
    note_page.conversion_settings.metadata_schema = ['title']
    note_page.conversion_settings.export_format = 'html'
    note_page.pre_process_content()

    assert note_page.pre_processed_content == '<head><title>Page 8 title</title><meta title="Page 8 title"/></head>content'


def test_convert_data_markdown_export(note_page):
    note_page.conversion_settings.export_format = 'gfm'
    note_page._pre_processed_content = '<head><title> </title></head>content'
    note_page._pandoc_converter = pandoc_converter.PandocConverter(note_page.conversion_settings)
    note_page.convert_data()

    if version.parse(note_page._pandoc_converter._pandoc_version) < version.parse('2.13'):
        assert note_page._converted_content == 'content\n'
    else:
        assert note_page._converted_content == '---\n---\n\ncontent\n'


def test_convert_data_html_export(note_page):
    note_page.conversion_settings.export_format = 'html'
    note_page._pre_processed_content = '<head><title> </title></head>content'
    note_page._pandoc_converter = pandoc_converter.PandocConverter(note_page.conversion_settings)
    note_page.convert_data()

    assert note_page._converted_content == '<head><title> </title></head>content'


def test_post_process_content(note_page):
    note_page._pre_processed_content = '<head><title> </title></head>content'
    note_page._pandoc_converter = pandoc_converter.PandocConverter(note_page.conversion_settings)
    note_page._converted_content = 'content\n'
    note_page._pre_processor = nsx_pre_processing.NoteStationPreProcessing(note_page)
    note_page._pre_processor.pre_process_note_page()
    note_page.conversion_settings.front_matter_format = 'none'
    note_page.post_process_content()

    assert note_page._converted_content == 'content\n\n'


@pytest.mark.parametrize(
    'title_list, expected_new_title', [
        (['no_match', 'no_match2'], 'Page 8 title'),
        (['no_match', 'no_match2', 'Page 8 title'], 'Page 8 title-1'),
    ]
)
def test_increment_duplicated_title(note_page, title_list, expected_new_title):
    note_page.increment_duplicated_title(title_list)

    assert note_page.title == expected_new_title


@pytest.mark.parametrize(
    'export_format, expected', [
        ('gfm',
         """Below is a hyperlink to the internet\n\n<https://github.com/kevindurston21/YANOM-Note-O-Matic>\n\n###### Attachments\n\n[Record 2021-02-15 16-00-13.webm](attachments/Record%202021-02-15%2016-00-13.webm)\n\n[example-attachment.pdf](attachments/example-attachment.pdf)\n\n[test page.pdf](attachments/test%20page.pdf)\n\n"""),
        ('html',
         """<p>Below is a hyperlink to the internet</p><p><a href="https://github.com/kevindurston21/YANOM-Note-O-Matic">https://github.com/kevindurston21/YANOM-Note-O-Matic</a></p><h6>Attachments</h6><p><a href="attachments/Record 2021-02-15 16-00-13.webm">Record 2021-02-15 16-00-13.webm</a></p><p><a href="attachments/example-attachment.pdf">example-attachment.pdf</a></p><p><a href="attachments/test page.pdf">test page.pdf</a></p>"""),
    ]
)
def test_process_note(note_page_1, export_format, expected, monkeypatch):
    note_page_1.conversion_settings.export_format = export_format
    note_page_1._pandoc_converter = pandoc_converter.PandocConverter(note_page_1.conversion_settings)
    note_page_1.conversion_settings.front_matter_format = 'none'

    # NOTE  THIS IS CRAZY.  Depending on the day one of these money patches works.

    # If the test fails swap to the other and it wil probably work until tomorrow!
    # def fake_store_file(_ignored):
    #     pass
    # monkeypatch.setattr(sn_attachment.NSAttachment, 'store_file', fake_store_file)

    monkeypatch.delattr('sn_attachment.FileNSAttachment.store_file')
    note_page_1.process_note()

    assert note_page_1.converted_content == expected


def test_get_json_note_title(note_page_1, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    note_page_1.logger.setLevel(config.yanom_globals.logger_level)
    note_page_1._note_json = {'title': 'Note Title Testing Get'}
    expected = 'Note Title Testing Get'
    note_page_1.get_json_note_title()
    assert note_page_1.title == expected
    assert f"Note title from json is '{expected}'" in caplog.messages


def test_get_json_note_title_key_missing_in_json(note_page_1, caplog):
    config.yanom_globals.logger_level = logging.DEBUG
    note_page_1.logger.setLevel(config.yanom_globals.logger_level)
    note_page_1._note_json = {'tag': 'tag1'}
    note_page_1.get_json_note_title()

    expected_caplog_msg = f"no title was found in note id '{note_page_1._note_id}'.  Using random string for title '{note_page_1._title}'"
    assert len(note_page_1.title) == 8
    assert expected_caplog_msg in caplog.messages


def test_get_json_note_content(note_page_1):
    note_page_1._note_json = {'content': 'Note Content Testing Get'}
    expected = 'Note Content Testing Get'
    note_page_1.get_json_note_content()
    assert note_page_1._raw_content == expected


def test_get_json_note_content_key_missing_in_json(note_page_1, caplog):
    note_page_1._note_json = {'tag': 'tag1'}
    note_page_1.get_json_note_content()
    expected_caplog_msg = f"No content was found in note id '{note_page_1._note_id}'."

    assert note_page_1._raw_content == ''
    assert expected_caplog_msg in caplog.messages


def test_get_json_attachment_data(note_page_1):
    expected = 'Note Attachment Testing Get'
    note_page_1._note_json = {'attachment': expected}
    note_page_1.get_json_attachment_data()
    assert note_page_1._attachments_json == expected


def test_get_json_attachment_data_key_missing_in_json(note_page_1, caplog):
    note_page_1._note_json = {'tag': 'tag1'}
    note_page_1.get_json_attachment_data()
    expected_caplog_msg = f"No attachments were found in note id '{note_page_1._note_id}'."

    assert note_page_1._attachments_json == {}
    assert expected_caplog_msg in caplog.messages


def test_get_json_parent_notebook(note_page_1):
    expected = 'Note Parent ID Testing Get'
    note_page_1._note_json = {'parent_id': expected}
    note_page_1.get_json_parent_notebook()
    assert note_page_1._parent_notebook_id == expected


@pytest.mark.parametrize(
    'silent, expected_out', [
        (True, ''),
        (False, "Note will be in the Recycle Bin notebook"),
    ]
)
def test_get_json_parent_notebook_key_missing_in_json(note_page_1, silent, expected_out, caplog, capsys):
    config.yanom_globals.is_silent = silent
    note_page_1._note_json = {'tag': 'tag1'}
    note_page_1.get_json_parent_notebook()
    expected_caplog_msg = f"No parent notebook ID was found in note id '{note_page_1._note_id}'.  Using a placeholder id of '{note_page_1._parent_notebook_id}'.  Notes will be in the Recycle bin notebook"

    assert note_page_1._parent_notebook_id == 'Parent Notebook ID missing from nsx file note data'
    assert expected_caplog_msg in caplog.messages

    captured = capsys.readouterr()
    assert expected_out in captured.out


def test_get_json_attachment_data_key_is_null(note_page_1, caplog):
    note_page_1._note_json['attachment'] = None
    note_page_1.get_json_attachment_data()
    expected_caplog_msg1 = f"Note - '{note_page_1._title}' - Has Null set for attachments. There may be a sync issues between desktop and web version of Note Station."

    assert note_page_1._attachments_json is None
    assert expected_caplog_msg1 in caplog.messages


@pytest.mark.parametrize(
    'ctime, mtime, expected_ctime, expected_mtime, format_time', [
        (1594591675, 1594591737, 1594591675, 1594591737, False),
        (1594591675, 1594591737, '202007122307', '202007122308', True),
    ]
)
def test_format_ctime_and_mtime_if_required(note_page_1, ctime, mtime, expected_ctime, expected_mtime, format_time):
    note_page_1._note_json['ctime'] = ctime
    note_page_1._note_json['mtime'] = mtime
    note_page_1.conversion_settings.creation_time_in_exported_file_name = format_time
    note_page_1.conversion_settings.front_matter_format = 'none'
    note_page_1.format_ctime_and_mtime_if_required()

    assert note_page_1._note_json['ctime'] == expected_ctime
    assert note_page_1._note_json['mtime'] == expected_mtime


@pytest.mark.parametrize(
    'ctime, mtime, expected_ctime, expected_mtime, format_time', [
        (1594591675, 1594591737, 1594591675, 1594591737, False),
        (1594591675, 1594591737, '202007122307', '202007122308', True),
    ]
)
def test_format_ctime_and_mtime_if_required_no_time_data_in_note_json(note_page_1, ctime, mtime, expected_ctime, expected_mtime, format_time):
    note_page_1._note_json = {}
    note_page_1.conversion_settings.creation_time_in_exported_file_name = format_time
    note_page_1.conversion_settings.front_matter_format = 'none'
    note_page_1.format_ctime_and_mtime_if_required()

    assert note_page_1._note_json == {}
