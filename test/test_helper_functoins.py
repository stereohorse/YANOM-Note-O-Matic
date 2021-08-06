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
    'value, allow_unicode, expected', [
        ("file", False, "file"),
        ("file.txt", False, "file.txt"),
        ("_file.txt-", False, "file.txt"),
        ("-file.txt_", False, "file.txt"),
        (" file.txt ", False, "file.txt"),
        ("f¥le.txt", False, "fle.txt"),
        ("file", True, "file"),
        ("file.txt", True, "file.txt"),
        ("_file.txt-", True, "file.txt"),
        ("-file.txt_", True, "file.txt"),
        (" file.txt ", True, "file.txt"),
        (" file.txt ", True, "file.txt"),
        (" f¥le.txt ", True, "fle.txt"),
        (" part1.part2.txt ", True, "part1part2.txt"),
        (" part1 part2.txt ", True, "part1-part2.txt"),
        (" 漢語.txt ", True, "漢語.txt"),
        (" 漢語%20file.txt ", True, "漢語-file.txt"),
        (" 漢語+file.txt ", True, "漢語-file.txt"),
        (" 漢語-should ignore the two leading chars.txt ", False, "should-ignore-the-two-leading-chars.txt"),
        (" dir1/dir2/file.txt ", True, "dir1-dir2-file.txt"),
        (" .file.txt ", True, "file.txt"),
        (" COM1.txt ", True, "com1.txt"),
        ("a-file-with-dot.in_it", True, "a-file-with-dot.in_it"),
        ("a-file-with.three.dots.in_it", True, "a-file-withthreedots.in_it"),
        ("1234567890123456789012345678901234567890", True, "1234567890123456789012345678901234567890"),
        ("!!!file.!!!txt", False,'file.txt'),
        ("123.45 - Probeer : dit eens", False,'123.45-probeer-dit-eens'),
        ("123.45 - Probeer : dit eens.html", False,'12345-probeer-dit-eens.html'),
    ]
)
def test_generate_clean_filename(value, allow_unicode, expected):

    result = helper_functions.generate_clean_filename(value, 64, allow_unicode=allow_unicode)

    assert result == expected

@pytest.mark.parametrize(
    'string_to_test, allow_unicode, expected', [
        ("123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
        False,
        '12345678901234567890123456789012'),
        ("123456789012345678901234567890123456789012345678901234567890123456789.012345678901234567890",
        False,
        '123456789012345678901234.01234567'),
        ("123456789012345678901234567890123456789012345678901234567890123456789.0123",
        False,
        '1234567890123456789012345678.0123'),
    ]
)
def test_generate_clean_filename_force_windows_long_name(string_to_test, allow_unicode, expected, monkeypatch):

    with monkeypatch.context() as m:
        m.setattr(os, 'name', 'nt')
        result = helper_functions.generate_clean_filename(string_to_test, 32, allow_unicode=allow_unicode, path_class=PureWindowsPath)

        assert result == expected

@pytest.mark.parametrize(
    'string_to_test, allow_unicode, expected', [
        ("123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
        False,
        '12345678901234567890123456789012'),
        ("12345678901234567890.1234567890123456789012345678901234567890123456789.012345678901234567890",
        False,
        '12345678901234567890-12345678901'),
        ("123456789012345678901234567890123456789012345678901234567890123456789.0123",
        False,
        '12345678901234567890123456789012'),
    ]
)
def test_generate_clean_directory_name_force_windows_long_name(string_to_test, allow_unicode, expected, monkeypatch):

    with monkeypatch.context() as m:
        m.setattr(os, 'name', 'nt')
        result = helper_functions.generate_clean_directory_name(string_to_test, 32, allow_unicode=allow_unicode, path_class=PureWindowsPath)

        assert result == expected


@pytest.mark.parametrize(
    'string_to_test, allow_unicode, expected', [
        ("", False, '6-chars-replaced'),
        (".txt", False, 'txt'),  # this is not an empty string as is read as a hidden file name (stem) and dot is stripped off
        ("file.!!!", False, 'file.6-chars-replaced'),
        ("!!!.!!!", False, '6-chars-replaced.6-chars-replaced'),
    ]
)
def test_generate_clean_filename_empty_strings(string_to_test, allow_unicode, expected, monkeypatch):

    result = helper_functions.generate_clean_filename(string_to_test, 64, allow_unicode=allow_unicode)

    # replace the generated 6 char value with placeholder text to allow comparison
    regex = r"[a-zA-Z]{6}"
    substitute_text = '6-chars-replaced'
    result = re.sub(regex, substitute_text, result, 0, re.MULTILINE)

    assert result == expected

@pytest.mark.parametrize(
    'string_to_test, allow_unicode, expected', [
        ("123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890",
        False,
        '1234567890123456789012345678901234567890123456789012345678901234'),
        ("1234567890123456789012345678901234567890123456789012345678901234567890",
        False,
        '1234567890123456789012345678901234567890123456789012345678901234'),
        ("123456789012345678901234567890123456789012345678901234567890.12345678901234",
        False,
        '123456789012345678901234567890123456789012345678901234567890-123'),
        (" 漢語-unicode-dir.dir ", True, "漢語-unicode-dir-dir"),
        (" 漢語%20unicode+dir.dir ", True, "漢語-unicode-dir-dir"),
        (" /dir 1/dir 2/dir 3 ", True, "dir-1-dir-2-dir-3"),
    ]
)
def test_generate_clean_directory_name(string_to_test, allow_unicode, expected, monkeypatch):
    monkeypatch.setattr(os, 'name', 'posix')
    result = helper_functions.generate_clean_directory_name(string_to_test, 64, allow_unicode=allow_unicode, path_class=PurePosixPath)

    assert result == expected


@pytest.mark.parametrize(
    'string_to_test, allow_unicode, expected', [
        ("", False, '6-chars-replaced'),
        ("!!!", False, '6-chars-replaced'),
    ]
)
def test_generate_clean_directory_name_empty_string(string_to_test, allow_unicode, expected, monkeypatch):
    monkeypatch.setattr(os, 'name', 'posix')
    result = helper_functions.generate_clean_directory_name(string_to_test, 64, allow_unicode=allow_unicode, path_class=PurePosixPath)

    # replace the generated 6 char value with placeholder text to allow comparison
    regex = r"[a-zA-Z]{6}"
    substitute_text = '6-chars-replaced'
    result = re.sub(regex, substitute_text, result, 0, re.MULTILINE)

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
