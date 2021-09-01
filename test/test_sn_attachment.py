from pathlib import Path

import file_writer
import pytest

import sn_attachment
import conversion_settings


class NSXFile:
    nsx_file_name = 'nsx_file_name'
    conversion_settings = 'conversion_settings'

    @staticmethod
    def fetch_attachment_file(_ignored, _ignored2):
        return 'file name in nsx'


class Notebook:
    def __init__(self):
        self.attachment_md5_file_name_dict = {'qwerty': 'not_matched'}


class Note:
    def __init__(self):
        self.nsx_file = NSXFile()
        self.conversion_settings = conversion_settings.ConversionSettings()
        self.note_json = {
            'attachment': {
                '1234':
                    {'ref': '54321',
                     'md5': 'qwerty',
                     'name': 'my_name.png',
                     'type': 'image/png',
                     }
            }
        }
        self.notebook_folder_name = 'notebook_folder'
        self.title = 'note_title'
        self.parent_notebook = Notebook()


def test_notebook_folder_name():
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    assert image_attachment.notebook_folder_name == 'notebook_folder'


def test_FileNSAttachment_create_html_link():
    note = Note()
    attachment_id = '1234'
    file_attachment = sn_attachment.FileNSAttachment(note, attachment_id)

    file_attachment._file_name = Path('my_file.png')
    file_attachment._path_relative_to_notebook = Path('attachments/my_file.png')
    file_attachment.create_html_link()

    assert file_attachment.html_link == '<a href="attachments/my_file.png">my_file.png</a>'


@pytest.mark.parametrize(
    'raw_name, expected', [
        ('my_file.png', 'my_file.png'),
        ('my file.png', 'my file.png'),
    ],
    ids=['clean-file-name', 'file-name-to-clean']
)
def test_FileNSAttachment_create_file_name(raw_name, expected):
    note = Note()
    attachment_id = '1234'
    file_attachment = sn_attachment.FileNSAttachment(note, attachment_id)

    file_attachment._name = raw_name
    file_attachment.create_file_name()

    assert file_attachment.file_name == Path(expected)


def test_FileNSAttachment_get_content_to_save():
    note = Note()
    attachment_id = '1234'
    file_attachment = sn_attachment.FileNSAttachment(note, attachment_id)
    result = file_attachment.get_content_to_save()

    assert result == 'file name in nsx'


def test_ImageNSAttachment_create_html_link():
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    image_attachment._file_name = Path('my_file.png')
    image_attachment.create_html_link()

    assert image_attachment.html_link == f'<img src="my_file.png" >'


@pytest.mark.parametrize(
    'raw_name, expected', [
        ('ns_attach_image_my_file.png', 'my_file.png'),
        ('ns_attach_image_my file.png', 'my file.png'),
    ],
    ids=['clean-file-name', 'file-name-to-clean']
)
def test_ImageNSAttachment_create_file_name(raw_name, expected):
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    image_attachment._name = raw_name
    image_attachment.create_file_name()

    assert image_attachment.file_name == Path(expected)


def test_ImageNSAttachment_image_ref():
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    assert image_attachment.image_ref == '54321'


def test_change_file_name_image_attachment_file_does_not_already_exist(tmp_path):
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    image_attachment._full_path = Path(tmp_path, 'my_file.png')

    image_attachment.change_file_name_if_already_exists()

    assert len(str(image_attachment.full_path)) == len(
        str(Path(tmp_path, 'my_file.png')))

    assert image_attachment.full_path == Path(tmp_path, 'my_file.png')


def test_change_file_name_image_attachment_if_already_exists(tmp_path):
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    image_attachment._full_path = Path(tmp_path, 'my_file.png')

    image_attachment._full_path.write_text('hello world')

    image_attachment.change_file_name_if_already_exists()

    assert len(str(image_attachment.full_path)) == len(
        str(Path(tmp_path, 'my_file.png'))) + 5  # 4 random chars and a dash


def test_test_change_file_name_image_attachment_no_extension_on_file_name(mocker):
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    image_attachment._name = 'ns_attach_image_my_file'
    mocker.patch('zip_file_reader.read_binary_file', return_value=b'1234')
    mocker.patch('helper_functions.file_extension_from_bytes', return_value='.png')
    image_attachment.create_file_name()

    assert image_attachment.file_name == Path('my_file.png')


def test_test_change_file_name_image_attachment_no_extension_on_file_name_and_not_recognised(mocker):
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    image_attachment._name = 'ns_attach_image_my_file'
    mocker.patch('zip_file_reader.read_binary_file', return_value=b'1234')
    mocker.patch('helper_functions.file_extension_from_bytes', return_value=None)
    image_attachment.create_file_name()

    assert image_attachment.file_name == Path('my_file')


def test_test_change_file_name_file_attachment_no_extension_on_file_name(mocker):
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.FileNSAttachment(note, attachment_id)

    image_attachment._name = 'my_file'
    mocker.patch('zip_file_reader.read_binary_file', return_value=b'1234')
    mocker.patch('helper_functions.file_extension_from_bytes', return_value='.pdf')
    image_attachment.create_file_name()

    assert image_attachment.file_name == Path('my_file.pdf')


def test_test_change_file_name_file_attachment_no_extension_on_file_name_and_not_recognised(mocker):
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.FileNSAttachment(note, attachment_id)

    image_attachment._name = 'my_file'
    mocker.patch('zip_file_reader.read_binary_file', return_value=b'1234')
    mocker.patch('helper_functions.file_extension_from_bytes', return_value=None)
    image_attachment.create_file_name()

    assert image_attachment.file_name == Path('my_file')


def test_test_change_file_name_file_attachment_good_file_name():
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.FileNSAttachment(note, attachment_id)

    image_attachment._name = 'my_file.pdf'
    image_attachment.create_file_name()

    assert image_attachment.file_name == Path('my_file.pdf')


def test_get_content_to_save_chart_attachment():
    note = Note()
    attachment_id = '1234'
    data_string = 'hello world'
    chart_attachment = sn_attachment.ChartStringNSAttachment(note, attachment_id, data_string)

    result = chart_attachment.get_content_to_save()
    assert result == data_string


def test_is_duplicate_file_not_a_duplicate():
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.FileNSAttachment(note, attachment_id)

    image_attachment._name = 'my_file.pdf'
    note.parent_notebook.attachment_md5_file_name_dict = {'abcd': "zxyz"}

    assert image_attachment.is_duplicate_file() is False


def test_is_duplicate_file_is_a_duplicate():
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.FileNSAttachment(note, attachment_id)
    image_attachment._json = {
        'attachment':
            {
                '1234':
                    {'md5': '0987', 'name': 'my_file.pdf'}
            }
    }

    note.parent_notebook.attachment_md5_file_name_dict = {'0987': "my_file.pdf"}

    assert image_attachment.is_duplicate_file() is True


def test_store_file(monkeypatch, tmp_path):
    def fake_store_file(_ignored, _ignored2):
        pass

    note = Note()
    note.conversion_settings.export_folder = tmp_path
    attachment_id = '1234'
    image_attachment = sn_attachment.FileNSAttachment(note, attachment_id)
    image_attachment._json = {
        'attachment':
            {
                '1234':
                    {'md5': 'abcd', 'name': 'not_my_file.pdf'}
            }
    }

    note.parent_notebook.attachment_md5_file_name_dict = {'0987': "my_file.pdf"}

    monkeypatch.setattr(file_writer, 'store_file', fake_store_file)
    image_attachment.create_file_name()
    image_attachment.generate_relative_path_to_notebook()
    image_attachment.generate_absolute_path()
    assert image_attachment.file_name == Path('my_name.png')
    assert image_attachment._full_path == Path(tmp_path, 'notebook_folder', 'attachments', 'my_name.png')

    image_attachment.store_file()

    assert len(note.parent_notebook.attachment_md5_file_name_dict) == 2


def test_store_file_will_not_store_as_duplicate_md5_and_name(monkeypatch):
    def fake_store_file(_ignored, _ignored2):
        pass

    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.FileNSAttachment(note, attachment_id)
    image_attachment._json = {
        'attachment':
            {
                '1234':
                    {'md5': '0987', 'name': 'my_file.pdf'}
            }
    }

    note.parent_notebook.attachment_md5_file_name_dict = {'0987': "my_file.pdf"}
    monkeypatch.setattr(file_writer, 'store_file', fake_store_file)
    image_attachment.store_file()

    assert len(note.parent_notebook.attachment_md5_file_name_dict) == 1
