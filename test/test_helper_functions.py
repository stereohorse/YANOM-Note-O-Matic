import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys

import pytest

import helper_functions


def test_find_valid_full_file_path_rename_expected(tmp_path):
    folder_name = "my-folder"
    Path(tmp_path, folder_name, 'file_name.txt').mkdir(parents=True, exist_ok=False)
    Path(tmp_path, folder_name, 'file_name-1.txt').mkdir(parents=True, exist_ok=False)
    path_to_test = Path(tmp_path, folder_name, 'file_name.txt')
    full_path = helper_functions.find_valid_full_file_path(path_to_test)
    assert full_path == Path(tmp_path, folder_name, 'file_name-2.txt')


def test_find_valid_full_file_path_no_rename_expected(tmp_path):
    folder_name = "my-folder"
    path_to_test = Path(tmp_path, folder_name, 'file_name.txt')
    full_path = helper_functions.find_valid_full_file_path(path_to_test)
    assert full_path == Path(tmp_path, folder_name, 'file_name.txt')


@pytest.mark.parametrize(
    'length, expected_length_or_random_string', [
        (0, 0),
        (-1, 0),
        (1, 1),
        (4, 4),
    ]
)
def test_add_random_string_to_file_name(length, expected_length_or_random_string):
    old_path = 'dir/file.txt'
    new_path = helper_functions.add_random_string_to_file_name(old_path, length)

    assert len(new_path.name) == len(Path(old_path).name) + expected_length_or_random_string + 1


def test_add_strong_between_tags():
    result = helper_functions.add_strong_between_tags('<p>', '</p>', '<p>hello world</p>')

    assert result == '<p><strong>hello world</strong></p>'


def test_add_strong_between_tags_invalid_tags():
    result = helper_functions.add_strong_between_tags('<x>', '</x>', '<p>hello world</p>')

    assert result == '<p>hello world</p>'


def test_change_html_tags():
    result = helper_functions.change_html_tags('<p>', '</p>', '<div>', '</div>', '<div><p>hello world</p></div>')

    assert result == '<div><div>hello world</div></div>'


def test_change_html_tags_invalid_old_tags():
    result = helper_functions.change_html_tags('<g>', '</g>', '<div>', '</div>', '<div><p>hello world</p></div>')

    assert result == '<div><p>hello world</p></div>'


def test_find_working_directory_when_frozen():
    current_dir, message = helper_functions.find_working_directory(True)

    assert 'Running in a application bundle' in message


@pytest.mark.parametrize(
    'value, filename_options, expected', [
        ("file",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "file"),
        ("file.txt",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "file.txt"),
        ("_file.txt-",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "file.txt"),
        ("-file.txt_",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "file.txt"),
        (" file.txt ",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "file.txt"),
        ("f¥le.txt",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "fle.txt"),
        ("file",
         helper_functions.FileNameOptions(64, True, True, True, True, '-'),
         "file"),
        ("file.txt",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "file.txt"),
        ("_file.txt-",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "file.txt"),
        ("-file.txt_",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "file.txt"),
        (" file.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "file.txt"),
        (" file.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "file.txt"),
        (" f¥le.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "f¥le.txt"),
        (" part1.part2.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "part1.part2.txt"),
        (" part1 part2.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "part1-part2.txt"),
        (" 漢語.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "漢語.txt"),
        (" 漢語%20file.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "漢語-file.txt"),
        (" 漢語+file.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "漢語-file.txt"),
        (" 漢語-should ignore the two leading chars.txt ",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "should-ignore-the-two-leading-chars.txt"),
        (" dir1/dir2/file.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "dir1-dir2-file.txt"),
        (" .file.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "file.txt"),
        (" COM1.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "_COM1.txt"),
        (" com1.txt ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "_com1.txt"),
        ("com1",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "_com1"),
        ("a-file-with-dot.in_it",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "a-file-with-dot.in_it"),
        ("a-file-with.three.dots.in_it",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "a-file-with.three.dots.in_it"),
        ("1234567890123456789012345678901234567890",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "1234567890123456789012345678901234567890"),
        ("!!!file.!!!txt",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         '!!!file.!!!txt'),
        ("!!?file.!!?txt",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         '!!-file.!!-txt'),
        ("???file.???txt",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         'file.txt'),
        ("123.45 - Probeer : dit eens",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         '123.45-Probeer-dit-eens'),
        ("123.45 - Probeer : dit eens.html",
         helper_functions.FileNameOptions(64, True, True, False, False, '-'),
         '123.45-Probeer-dit-eens.html'),
        ("123.45 - Probeer : dit eens.html",
         helper_functions.FileNameOptions(64, True, True, True, False, ''),
         '123.45-Probeer-diteens.html'),
        ("123.45 - Probeer : dit eens.html",
         helper_functions.FileNameOptions(64, True, True, True, True, '-'),
         '123.45 - Probeer - dit eens.html'),
        ("123.45 - Probeer : dit eens.html",
         helper_functions.FileNameOptions(64, True, False, True, True, '-'),
         '123.45 - probeer - dit eens.html'),
    ]
)
def test_generate_clean_filename(value, filename_options, expected, tmp_path):
    result = helper_functions.generate_clean_filename(value, filename_options)

    assert result == expected

    Path(tmp_path, result).touch()

    assert Path(tmp_path, result).exists()


def test_clean_path_parts():
    filename_options = helper_functions.FileNameOptions(max_length=64,
                                                        allow_unicode=True,
                                                        allow_uppercase=True,
                                                        allow_non_alphanumeric=True,
                                                        allow_spaces=False, space_replacement='-')
    result = helper_functions.clean_path_parts(filename_options, ['hello hello', ''])

    assert result == ['hello-hello', '']

@pytest.mark.parametrize(
    'parts, expected, max_length', [
        (['123456789', '123456789'],
         ['1', '12345678'],
         9,
         ),
        (['123', '123'],
         ['123', '123'],
         64,
         ),
        (['1234', '1234567890'],
         ['1234', '12345678'],
         13,
         ),
    ]
)
def test_shorten_filename(parts, expected, max_length):
    result = helper_functions.shorten_filename(parts, max_length)
    assert result == expected


@pytest.mark.parametrize(
    'string_to_test, filename_options, expected', [
        ("123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
         helper_functions.FileNameOptions(32, False, True, True, False, '-'),
         '12345678901234567890123456789012'),
        ("123456789012345678901234567890123456789012345678901234567890123456789.012345678901234567890",
         helper_functions.FileNameOptions(32, False, True, True, False, '-'),
         '123456789012345678901234.01234567'),
        ("123456789012345678901234567890123456789012345678901234567890123456789.0123",
         helper_functions.FileNameOptions(32, False, True, True, False, '-'),
         '1234567890123456789012345678.0123'),
    ]
)
def test_generate_clean_filename_force_windows_long_name(string_to_test, filename_options, expected):
    result = helper_functions.generate_clean_filename(string_to_test, filename_options)

    assert result == expected


@pytest.mark.parametrize(
    'string_to_test, filename_options, expected', [
        ("123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
         helper_functions.FileNameOptions(32, False, True, True, False, '-'),
         '12345678901234567890123456789012'),
        ("12345678901234567890.1234567890123456789012345678901234567890123456789.012345678901234567890",
         helper_functions.FileNameOptions(32, False, True, True, False, '-'),
         '12345678901234567890.12345678901'),
        ("123456789012345678901234567890123456789012345678901234567890123456789.0123",
         helper_functions.FileNameOptions(32, False, True, True, False, '-'),
         '12345678901234567890123456789012'),
    ]
)
def test_generate_clean_directory_name_force_windows_long_name(string_to_test, filename_options, expected):
    result = helper_functions.generate_clean_directory_name(string_to_test, filename_options)

    assert result == expected


@pytest.mark.parametrize(
    'string_to_test, filename_options, expected', [
        ("", helper_functions.FileNameOptions(32, False, True, True, False, '-'), '6-chars-replaced'),
        (".", helper_functions.FileNameOptions(32, False, True, True, False, '-'), '6-chars-replaced'),
        ("..", helper_functions.FileNameOptions(32, False, True, True, False, '-'), '6-chars-replaced'),
        (".txt", helper_functions.FileNameOptions(32, False, True, True, False, '-'), 'txt'),
        ("file.???", helper_functions.FileNameOptions(32, False, True, True, False, '-'), 'file.6-chars-replaced'),
        ("???.???", helper_functions.FileNameOptions(32, False, True, True, False, '-'), '6-chars-replaced.6-chars-replaced'),
    ]
)
def test_generate_clean_filename_empty_strings(string_to_test, filename_options, expected):
    result = helper_functions.generate_clean_directory_name(string_to_test, filename_options)

    # replace the generated 6 char value with placeholder text to allow comparison
    regex = r"[a-zA-Z]{6}"
    substitute_text = '6-chars-replaced'
    result = re.sub(regex, substitute_text, result, 0, re.MULTILINE)

    assert result == expected


@pytest.mark.parametrize(
    'string_to_test, filename_options, expected', [
        ("123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         '1234567890123456789012345678901234567890123456789012345678901234'),
        ("1234567890123456789012345678901234567890123456789012345678901234567890",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         '1234567890123456789012345678901234567890123456789012345678901234'),
        ("123456789012345678901234567890123456789012345678901234567890.12345678901234",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         '123456789012345678901234567890123456789012345678901234567890.123'),
        (" 漢語-unicode-dir.dir ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "漢語-unicode-dir.dir"),
        (" 漢語%20unicode+dir.dir ",
         helper_functions.FileNameOptions(64, True, True, True, False, '-'),
         "漢語-unicode-dir.dir"),
        (" /dir 1/dir 2/dir 3 ",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "dir-1-dir-2-dir-3"),
        ("COM1.txt",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "_COM1.txt"),
    ]
)
def test_generate_clean_directory_name(string_to_test, filename_options, expected, tmp_path):
    result = helper_functions.generate_clean_directory_name(string_to_test, filename_options)

    assert result == expected

    Path(tmp_path, result).mkdir()

    assert Path(tmp_path, result).exists()


@pytest.mark.parametrize(
    'string_to_test, filename_options, expected', [
        ("", helper_functions.FileNameOptions(64, False, True, True, False, '-'), '6-chars-replaced'),
        ("???", helper_functions.FileNameOptions(64, False, True, True, False, '-'), '6-chars-replaced'),
        (".", helper_functions.FileNameOptions(64, False, True, True, False, '-'), '6-chars-replaced'),
        ("..", helper_functions.FileNameOptions(64, False, True, True, False, '-'), '6-chars-replaced'),
        (".hello", helper_functions.FileNameOptions(64, False, True, True, False, '-'), 'hello'),
    ]
)
def test_generate_clean_directory_name_empty_string(string_to_test, filename_options, expected):
    result = helper_functions.generate_clean_directory_name(string_to_test, filename_options)

    # replace the generated 6 char value with placeholder text to allow comparison
    regex = r"[a-zA-Z]{6}"
    substitute_text = '6-chars-replaced'
    result = re.sub(regex, substitute_text, result, 0, re.MULTILINE)

    assert result == expected


@pytest.mark.parametrize(
    'string_to_test, filename_options, expected', [
        (" /dir 1/dir 2/dir 3 ",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "/dir-1/dir-2/dir-3"),
        (" /dir 1/dir 2/dir 3 ",
         helper_functions.FileNameOptions(64, False, True, True, True, '-'),
         "/dir 1/dir 2/dir 3"),
        ("dir1/dir2/dir3",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "dir1/dir2/dir3"),
        ("dir1",
         helper_functions.FileNameOptions(64, False, True, True, False, '-'),
         "dir1"),
    ]
)
def test_generate_clean_directory_name(string_to_test, filename_options, expected):
    result = helper_functions.generate_clean_directory_path(string_to_test, filename_options)

    assert result == expected


@pytest.mark.parametrize(
    'is_frozen, expected', [
        (True, Path(sys.executable).parent.absolute()),
        (False, Path(Path(__file__).parent.absolute().parent.absolute(), 'src'))
    ]
)
def test_find_working_directory(is_frozen, expected):
    result, message = helper_functions.find_working_directory(is_frozen=is_frozen)

    assert result == expected


def test_are_windows_long_paths_enabled():
    result = helper_functions.are_windows_long_paths_disabled()

    if os.name == 'nt':
        assert isinstance(result, bool)
    else:
        assert result is None


def test_file_extension_from_bytes():
    with open('test/fixtures/png_with_no_extension', "rb") as file:
        file_bytes = file.read(261)

        result = helper_functions.file_extension_from_bytes(file_bytes)

        assert result == '.png'


def test_file_extension_from_bytes_file_not_recognised():
    result = helper_functions.file_extension_from_bytes(b'1234')

    assert result is None


@pytest.mark.parametrize(
    'uri, path_type, expected', [
        ('some_folder/some%20space/file%20space.pdf', PurePosixPath, Path('some_folder/some space/file space.pdf')),
        ('some_folder/some_space/file_space.pdf', PurePosixPath, Path('some_folder/some_space/file_space.pdf')),
        ('file:///Users/user/folder/attachments/example attachment.pdf', PurePosixPath, Path('/Users/user/folder/attachments/example attachment.pdf')),
        ('file:///Users/user/folder/attachments/example%20attachment.pdf', PurePosixPath, Path('/Users/user/folder/attachments/example attachment.pdf')),
        ('file://c:/users/files/a file.pdf', PurePosixPath, Path('/users/files/a file.pdf')),
        ('some_folder/some%20space/file%20space.pdf', PureWindowsPath, PureWindowsPath('some_folder/some space/file space.pdf')),
        ('some_folder/some_space/file_space.pdf', PureWindowsPath, PureWindowsPath('some_folder/some_space/file_space.pdf')),
        ('file:///Users/user/folder/attachments/example attachment.pdf', PureWindowsPath,
         PureWindowsPath('/Users/user/folder/attachments/example attachment.pdf')),
        ('file:///Users/user/folder/attachments/example%20attachment.pdf', PureWindowsPath,
         PureWindowsPath('/Users/user/folder/attachments/example attachment.pdf')),
        ('file://c:/users/files/a file.pdf', PureWindowsPath, PureWindowsPath('c:/users/files/a file.pdf')),
        ]
)
def test_file_uri_to_path(uri, path_type, expected):
    result = helper_functions.file_uri_to_path(uri, path_type)

    assert result == expected


def test_is_available_to_use(tmp_path):
    Path(tmp_path, 'empty').mkdir()
    Path(tmp_path, 'not_empty').mkdir()
    Path(tmp_path, 'empty', '.hidden_file').touch()
    Path(tmp_path, 'not_empty', '.hidden_file').touch()
    Path(tmp_path, 'not_empty', 'a_file').touch()

    assert helper_functions.is_available_to_use(Path(tmp_path, 'empty'))
    assert not helper_functions.is_available_to_use(Path(tmp_path, 'not_empty'))
    assert helper_functions.is_available_to_use(str(Path(tmp_path, 'empty')))
    assert not helper_functions.is_available_to_use(str(Path(tmp_path, 'not_empty')))


def test_next_available_directory_name_not_empty_dir_use_next_empty_dir(tmp_path):
    empty = Path(tmp_path, 'folder-1')
    empty.mkdir()
    Path(empty, '.hidden_file').touch()

    not_empty = Path(tmp_path, 'folder')
    not_empty.mkdir()
    Path(not_empty, '.hidden_file').touch()
    Path(not_empty, 'a_file').touch()

    result = helper_functions.next_available_directory_name(not_empty)

    assert result == Path(tmp_path, 'folder-1')


def test_next_available_directory_name_not_empty_dir_use_next_available_name(tmp_path):
    not_empty2 = Path(tmp_path, 'folder-1')
    not_empty2.mkdir()
    Path(not_empty2, '.hidden_file').touch()
    Path(not_empty2, 'a_file').touch()

    not_empty = Path(tmp_path, 'folder')
    not_empty.mkdir()
    Path(not_empty, '.hidden_file').touch()
    Path(not_empty, 'a_file').touch()

    result = helper_functions.next_available_directory_name(not_empty)

    assert result == Path(tmp_path, 'folder-2')


def test_next_available_directory_name_not_empty_dir_use_next_available_name_provided_folder_has_a_number(tmp_path):
    not_empty2 = Path(tmp_path, 'folder-2')
    not_empty2.mkdir()
    Path(not_empty2, '.hidden_file').touch()
    Path(not_empty2, 'a_file').touch()

    not_empty = Path(tmp_path, 'folder-1')
    not_empty.mkdir()
    Path(not_empty, '.hidden_file').touch()
    Path(not_empty, 'a_file').touch()

    result = helper_functions.next_available_directory_name(not_empty)

    assert result == Path(tmp_path, 'folder-3')


def test_next_available_directory_name_empty_dir(tmp_path):
    empty = Path(tmp_path, 'empty')
    empty.mkdir()
    Path(empty, '.hidden_file').touch()

    result = helper_functions.next_available_directory_name(empty)

    assert result == Path(tmp_path, 'empty')


def test_next_available_directory_name_existing_file(tmp_path):
    file = Path(tmp_path, 'existing_file')
    file.touch()

    with pytest.raises(ValueError):
        result = helper_functions.next_available_directory_name(file)


def test_next_available_directory_name_check_casting(tmp_path):
    empty = Path(tmp_path, 'empty')
    empty.mkdir()
    Path(empty, '.hidden_file').touch()

    result = helper_functions.next_available_directory_name(str(empty))

    assert result == str(Path(tmp_path, 'empty'))


@pytest.mark.parametrize(
    'string_to_search, expected', [
        ('hello-1234', 1234),
        ('hello-', None),
        ]
)
def test_get_trailing_number(string_to_search, expected):
    result = helper_functions.get_trailing_number(string_to_search)
    assert result == expected


def test_is_pathname_valid_posix():
    if os.name == 'posix':
        assert not helper_functions.is_pathname_valid('\0hello')
        assert helper_functions.is_pathname_valid('hello')
        assert not helper_functions.is_pathname_valid('')


def test_is_pathname_valid_windows():
    if os.name == 'nt':
        result = helper_functions.is_pathname_valid(r'c:\hello')
        assert result
        result = helper_functions.is_pathname_valid(r'c:\K<>hello')
        assert not result


@pytest.mark.parametrize(
    'path_to_test, expected', [
        ('/hello/dog\0/cat', False),
        ('file:///K:/SPSS%20info/', False),
        ('file://K://SPSS%20info//', False),
        ('c:/SPSS%20info', True),
        ('c:\\windows', True),
        ('attachments\example_file.pdf', True),
        ('c:/SPSS%20info', True),
        ('SPSS info', True),
    ]
)
def test_is_path_valid_windows(path_to_test, expected):
    if not os.name == 'nt':
        return

    result = helper_functions.is_path_valid(path_to_test)

    assert result == expected


@pytest.mark.parametrize(
    'path_to_test, expected', [
        ('/hello/dog\0/cat', False),
        ('file:///K:/SPSS%20info/', True),
        ('file://K://SPSS%20info//', True),
        ('c:/SPSS%20info', True),
        ('c:\\windows', True),
        ('attachments\example_file.pdf', True),
        ('c:/SPSS%20info', True),
        ('SPSS info', True),
        (None, False),
        (['hello'], False),
    ]
)
def test_is_path_valid_unix_like(path_to_test, expected):
    if os.name == 'nt':
        return

    result = helper_functions.is_path_valid(path_to_test)

    assert result == expected


@pytest.mark.parametrize(
    'path_to_test, expected', [
        ('/hello/dog\0/cat', False),
        ('file:///K:/SPSS%20info/', False),
        ('file://K://SPSS%20info//', False),
        ('c:/SPSS%20info', True),
        ('c:\\windows', True),
        ('attachments\example_file.pdf', True),
        ('c:/SPSS%20info', True),
        ('SPSS info', True),
    ]
)
def test_is_path_valid_windows(path_to_test, expected):
    if not os.name == 'nt':
        return

    result = helper_functions.is_path_valid(path_to_test)

    assert result == expected


@pytest.mark.parametrize(
    'path_to_test, expected', [
        ('/hello/dog\0/cat', False),
        ('file:///K:/SPSS%20info/', True),
        ('file://K://SPSS%20info//', True),
        ('c:/SPSS%20info', True),
        ('c:\\windows', True),
        ('attachments\example_file.pdf', True),
        ('c:/SPSS%20info', True),
        ('SPSS info', True),
        (None, False),
        (['hello'], False),
    ]
)
def test_is_path_valid_unix_like(path_to_test, expected):
    if os.name == 'nt':
        return

    result = helper_functions.is_path_valid(path_to_test)

    assert result == expected
