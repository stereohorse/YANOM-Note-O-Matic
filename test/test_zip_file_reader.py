import json
from pathlib import Path
import zipfile

import config
import pytest

import zip_file_reader


def test_read_text(tmp_path):
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = "hello world"
    target_filename = 'file.txt'

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.writestr(target_filename, expected)

    result = zip_file_reader.read_text(zip_filename, target_filename)

    assert result == expected


def test_read_json_data(tmp_path):
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = {'key': 'value'}
    target_filename = 'file.txt'

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.writestr(target_filename, json.dumps(expected))

    result = zip_file_reader.read_json_data(zip_filename, target_filename)

    assert result == expected


def test_read_binary_file(tmp_path):
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = b'Hello World'
    target_filename = 'file.bin'

    with open(Path(tmp_path, target_filename), "wb") as file:
        file.write(expected)

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.write(Path(tmp_path, target_filename), target_filename)

    result = zip_file_reader.read_binary_file(zip_filename, target_filename)

    assert result == expected


def test_read_binary_file_bad_file_name(tmp_path, caplog, capfd):
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = b'Hello World'
    target_filename = 'file.bin'

    with open(Path(tmp_path, target_filename), "wb") as file:
        file.write(expected)

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.write(Path(tmp_path, target_filename), target_filename)

    _ = zip_file_reader.read_binary_file(zip_filename, 'bad_file_name', 'note title')

    assert f'Warning - For the note "note title" - unable to find the file "bad_file_name" in the zip file "{zip_filename}"' in caplog.messages

    out, err = capfd.readouterr()
    assert 'Warning - For the note "note title" - unable to find the file "bad_file_name" in the zip file ' in out
    assert err == ''


def test_read_binary_file_bad_zip_file_name(tmp_path, caplog, capfd):
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = b'Hello World'
    target_filename = 'file.bin'

    with open(Path(tmp_path, target_filename), "wb") as file:
        file.write(expected)

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.write(Path(tmp_path, target_filename), target_filename)

    with pytest.raises(SystemExit):
        _ = zip_file_reader.read_binary_file('bad_file_name', target_filename, 'note title')

    assert f'Error - unable to read zip file "bad_file_name"' in caplog.messages

    out, err = capfd.readouterr()
    assert 'Error - unable to read zip file ' in out
    assert err == ''


def test_read_json_data_bad_zip_file_name(tmp_path, caplog, capfd):
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = {'key': 'value'}
    target_filename = 'file.txt'

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.writestr(target_filename, json.dumps(expected))

    with pytest.raises(SystemExit):
        _ = zip_file_reader.read_json_data('bad_file_name', target_filename)

    assert f'Error - unable to read zip file "bad_file_name"' in caplog.messages

    out, err = capfd.readouterr()
    assert 'Error - unable to read zip file ' in out
    assert err == ''


def test_read_json_data_bad_file_name(tmp_path, caplog, capfd):
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = {'key': 'value'}
    target_filename = 'file.txt'

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.writestr(target_filename, json.dumps(expected))


    _ = zip_file_reader.read_json_data(zip_filename, 'bad_file_name', 'note title')

    assert f'Warning - For the note "note title" - unable to find the file "bad_file_name" in the zip file "{zip_filename}"' in caplog.messages

    out, err = capfd.readouterr()
    assert 'Warning - For the note "note title" - unable to find the file "bad_file_name" in the zip file ' in out
    assert err == ''


def test_read_json_data_bad_zip_file_name_in_silent_mode(tmp_path, caplog, capfd):
    config.yanom_globals.is_silent = True
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = {'key': 'value'}
    target_filename = 'file.txt'

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.writestr(target_filename, json.dumps(expected))

    with pytest.raises(SystemExit):
        _ = zip_file_reader.read_json_data('bad_file_name', target_filename)

    assert f'Error - unable to read zip file "bad_file_name"' in caplog.messages

    out, err = capfd.readouterr()
    assert '' in out
    assert err == ''


def test_read_json_data_bad_file_name_in_silent_mode(tmp_path, caplog, capfd):
    config.yanom_globals.is_silent = True
    zip_filename = Path(tmp_path, 'test_zip.zip')
    expected = {'key': 'value'}
    target_filename = 'file.txt'

    with zipfile.ZipFile(str(zip_filename), 'w') as zip_file:
        zip_file.writestr(target_filename, json.dumps(expected))

    _ = zip_file_reader.read_json_data(zip_filename, 'bad_file_name', 'note title')

    assert f'Warning - For the note "note title" - unable to find the file "bad_file_name" in the zip file "{zip_filename}"' in caplog.messages

    out, err = capfd.readouterr()
    assert '' in out
    assert err == ''


class TestListFilesInZipFile:

    @pytest.fixture
    def zip_file_path(self, tmp_path):
        import shutil
        Path(tmp_path, 'zip_folder', 'zip_sub_folder', 'zip_sub_sub_folder', 'zip_sub_folder').mkdir(parents=True)
        Path(tmp_path, 'zip_folder', 'file1.txt').touch()
        Path(tmp_path, 'zip_folder', 'file1b.txt').touch()
        Path(tmp_path, 'zip_folder', 'file1c.txt').touch()
        Path(tmp_path, 'zip_folder', 'zip_sub_folder', 'file2.txt').touch()
        Path(tmp_path, 'zip_folder', 'zip_sub_folder', 'file2b.txt').touch()
        Path(tmp_path, 'zip_folder', 'zip_sub_folder', 'zip_sub_sub_folder', 'file3.txt').touch()
        Path(tmp_path, 'zip_folder', 'zip_sub_folder', 'zip_sub_sub_folder', 'zip_sub_folder', 'file4.txt').touch()

        zip_file_name = 'test'
        archive_type = 'zip'
        shutil.make_archive(str(Path(tmp_path, zip_file_name)), archive_type, Path(tmp_path, 'zip_folder'))

        assert Path(tmp_path, f'{zip_file_name}.{archive_type}').exists()

        return Path(tmp_path, f'{zip_file_name}.{archive_type}'), tmp_path

    def test_list_files_in_zip_file_get_all_files_in_zip_root(self, zip_file_path):
        root_path = zip_file_path[1]
        zip_file = str(zip_file_path[0])

        expected = {
            str(Path(root_path, 'test.zip', 'file1.txt')),
            str(Path(root_path, 'test.zip', 'file1b.txt')),
            str(Path(root_path, 'test.zip', 'file1c.txt')),
        }
        set_of_paths = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file, '')
        result = {str(path) for path in set_of_paths}

        assert result == expected

    def test_list_files_in_zip_file_get_root_files_with_ignore_file_list(self, zip_file_path):
        root_path = zip_file_path[1]
        zip_file = str(zip_file_path[0])

        expected = {
            str(Path(root_path, 'test.zip', 'file1.txt')),
        }
        set_of_paths = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file, '', ['file1b.txt', 'file1c.txt'])
        result = {str(path) for path in set_of_paths}

        assert result == expected

    def test_list_files_in_zip_file_get_files_from_a_directory(self, zip_file_path):
        root_path = zip_file_path[1]
        zip_file = str(zip_file_path[0])

        expected = {
            str(Path(root_path, 'test.zip', 'zip_sub_folder', 'file2.txt')),
            str(Path(root_path, 'test.zip', 'zip_sub_folder', 'file2b.txt')),
        }
        set_of_paths = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file, 'zip_sub_folder')
        result = {str(path) for path in set_of_paths}

        assert result == expected

    def test_list_files_in_zip_file_get_files_from_a_directory_ignore_single_file(self, zip_file_path):
        root_path = zip_file_path[1]
        zip_file = str(zip_file_path[0])

        expected = {
            str(Path(root_path, 'test.zip', 'zip_sub_folder', 'file2.txt')),
        }
        set_of_paths = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file, 'zip_sub_folder', ['file2b.txt'])
        result = {str(path) for path in set_of_paths}

        assert result == expected

    def test_list_files_in_zip_file_get_files_from_a_sub_sub_directory(self, zip_file_path):
        root_path = zip_file_path[1]
        zip_file = str(zip_file_path[0])

        expected = {
            str(Path(root_path, 'test.zip', 'zip_sub_folder', 'zip_sub_sub_folder', 'zip_sub_folder', 'file4.txt')),
        }
        set_of_paths = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file, 'zip_sub_folder/zip_sub_sub_folder/zip_sub_folder',)
        result = {str(path) for path in set_of_paths}

        assert result == expected

    def test_list_files_in_zip_file_get_files_bad_zip_file_name(self, zip_file_path):
        zip_file = 'hello-dlfjhsafl.zip'

        with pytest.raises(SystemExit):
            set_of_paths = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file, 'zip_sub_folder/zip_sub_sub_folder/zip_sub_folder',)

    def test_list_files_in_zip_file_get_files_from_non_existing_directory(self, zip_file_path, caplog):
        zip_file = str(zip_file_path[0])

        expected = set()
        result = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file, 'hello')

        assert result == expected
        assert f'Directory ' in caplog.messages[0]
        assert caplog.records[0].levelname == 'WARNING'
