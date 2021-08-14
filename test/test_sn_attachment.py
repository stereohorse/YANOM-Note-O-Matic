from pathlib import Path

import pytest

import sn_attachment
import conversion_settings


class NSXFile:
    nsx_file_name = 'nsx_file_name'
    @staticmethod
    def fetch_attachment_file(ignored, title):
        return 'file name in nsx'


class Note:
    def __init__(self):
        self.nsx_file = NSXFile()
        self.conversion_settings = conversion_settings.ConversionSettings()
        self.note_json = {'attachment':
                              {'1234':
                                   {'ref': '54321',
                                    'md5': 'qwerty',
                                    'name': 'my_name',
                                    'type': 'image/png',
                                    }
                               }
                          }
        self.notebook_folder_name = 'notebook_folder'
        self.title = 'note_title'

def test_notebook_folder_name():
    note = Note()
    attachment_id = '1234'
    image_attachment = sn_attachment.ImageNSAttachment(note, attachment_id)

    assert image_attachment.notebook_folder_name == 'notebook_folder'


def test_FileNSAttachment_create_html_link():
    note = Note()
    attachment_id = '1234'
    file_attachment = sn_attachment.FileNSAttachment(note, attachment_id)

    file_attachment._file_name = 'my_file.png'
    file_attachment._path_relative_to_notebook = 'attachments/my_file.png'
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

    image_attachment._file_name = 'my_file.png'
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