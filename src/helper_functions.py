import os
from pathlib import Path, PurePath
import random
import re
import string
import sys
import traceback
from typing import Tuple
import unicodedata
from urllib.parse import unquote_plus


def find_working_directory(is_frozen=getattr(sys, 'frozen', False)) -> Tuple[Path, str]:
    """
    This function helps fetch the current working directory when a program may be run in a frozen pyinstaller bundle or
    in a python environment.

    Returns
    -------
    current_directory_path
        Path object of the absolute path for the current working directory
    message
        Str that describes if the program is run as a bundle or in python and the current working directory path
    """
    if is_frozen:
        # we are running in a bundle
        current_directory_path = Path(sys.executable).parent.absolute()
        message = f"Running in a application bundle, current path is {current_directory_path}"
    else:
        # we are running in a normal Python environment
        current_directory_path = Path(__file__).parent.absolute()
        message = f"Running in a python environment, current path is {current_directory_path}"

    return current_directory_path, message


def generate_clean_filename(filename, max_length, allow_unicode=False, path_class=PurePath) -> str:
    """
    Clean a file name.

    If the string is empty return a 6 letter lower case random string.
    Convert to ASCII if 'allow_unicode' is False.
    Replace forward and backslash with dash.
    Remove any reserved windows characters.
    Convert spaces or repeated dashes to single dashes.
    Strip leading and trailing whitespace, dashes, underscores and dots.
    If the name is a reserved windows name prepend with an underscore.
    If resulting sting is empty generates a 6 letter lower case random string.
    If final string exceeds the provided max length the file extension is trimmed to max 8 chars
    and the main name (stem) to what ever length is left after removing length of extension from the max length
    There is no consideration of the total length exceeding the OS max length for a path.

    Parameters
    ==========
    filename: str
        A file name.
    max_length: int
        Maximum string length to return.
    allow_unicode: bool
        If True unicode characters are maintained.  Default = False.
    path_class: PurePath class PurePath or PureWindowsPath, or PurePosixPath.

    Returns
    =======
    str

    """

    filename = str(filename)

    if not filename:  # empty string
        return get_random_string(6)

    filename = filename.lstrip('.')
    filename = unquote_plus(filename)
    filename = replace_slashes(filename)
    parts = split_string_to_file_parts(path_class, filename)
    parts = clean_path_parts(allow_unicode, parts)
    parts = prepend_reserved_windows_names(parts)
    parts = add_random_string_to_any_empty_path_parts(parts)
    parts = shorten_filename(parts, max_length)
    clean_filename = join_name_parts(parts)

    return clean_filename


def generate_clean_directory_name(directory_name, max_length, allow_unicode=False, path_class=PurePath) -> str:
    """
    Clean a directory name.

    If the string is empty return a 6 letter lower case random string.
    Convert to ASCII if 'allow_unicode' is False.
    Remove any reserved windows characters.
    Convert spaces or repeated dashes to single dashes.
    Strip leading and trailing whitespace, dashes, and underscores.
    If the name is a reserved windows name prepend with an underscore.
    If resulting sting is empty generates a 6 letter lower case random string.
    If any directory exceeds the provided max length it is trimmed to max_length
    There is no consideration of the total length exceeding the OS max length for a path.
    If more than one directory is provided /dir1/dir2/dir3 only dir1-dir2-dir3 will be cleaned and returned.

    Parameters
    ==========
    directory_name: str
        A single directory name.
    max_length: int
        Maximum string length to return.
    allow_unicode: bool
        If True unicode characters are maintained.  Default = False.
    path_class: PurePath class PurePath or PureWindowsPath, or PurePosixPath.

    Returns
    =======
    str

    """
    if not directory_name or directory_name == '.' or directory_name == '..':
        return get_random_string(6)

    directory_name = unquote_plus(directory_name)
    directory_name = replace_slashes(directory_name)
    parts = [path_class(directory_name).parts[-1]]
    parts = clean_path_parts(allow_unicode, parts)
    parts = add_random_string_to_any_empty_path_parts(parts)
    parts = shorten_directory_name(parts, max_length)
    parts = prepend_reserved_windows_names(split_string_to_file_parts(path_class, parts[0]))
    clean_directory_name = join_name_parts(parts)

    return clean_directory_name


def join_name_parts(parts):

    if len(parts) > 1:
        parts[1] = parts[1].lstrip('.')
        new_path_part_name = f"{parts[0]}.{parts[1]}"
    else:
        new_path_part_name = f"{parts[0]}"

    return new_path_part_name


def clean_path_parts(allow_unicode, parts):
    for i in range(len(parts)):
        if not len(parts[i]):
            continue

        parts[i] = process_path_part_for_unicode(allow_unicode, parts[i])

        parts[i] = strip_unwanted_chars_from_path_part(parts[i])

    return parts


def prepend_reserved_windows_names(parts: list):
    """
    Prepend the first part of a file or directory name with underscore if that name part is a reserved windows name.

    The prepend is applied in all operating systems.

    Parameters
    ==========
    parts : list
        list of parts making up the name.  parts in the list are in order i.e. part[0] is the first part

    Returns
    =======
    list:
        list of parts modified if required

    """

    reserved_names = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8',
                      'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}

    if parts[0].lower() in reserved_names:
        parts[0] = f'_{parts[0]}'

    return parts


def add_random_string_to_any_empty_path_parts(parts):
    for i in range(len(parts)):
        if not len(parts[i]):
            parts[i] = get_random_string(6)

    return parts


def strip_unwanted_chars_from_path_part(raw_part):
    # Remove any non a-z 0-9 or dash
    # raw_part = re.sub(r'[^\w\s-]', '', raw_part.lower())

    cleaned_part = "".join(character for character in raw_part if character not in r'<>:"/\|?*')

    # Remove spaces and multiple dashes and replace with single dash then srtrip leading and trialing chars and make all lower
    cleaned_part = re.sub(r'[-\s]+', '-', cleaned_part).strip('-_.')

    return cleaned_part


def process_path_part_for_unicode(allow_unicode, raw_part):
    if allow_unicode:
        cleaned_part = unicodedata.normalize('NFKC', raw_part)
    else:
        cleaned_part = unicodedata.normalize('NFKD', raw_part)
        cleaned_part = cleaned_part.encode('ascii', 'ignore')
        cleaned_part = cleaned_part.decode('ascii')

    return cleaned_part


def split_string_to_file_parts(path_class, path_to_clean):
    parts = []
    if path_class(path_to_clean).stem:
        parts.append(str(path_class(path_to_clean).stem))
    if path_class(path_to_clean).suffix:
        parts.append(str(path_class(path_to_clean).suffix))

    if not parts:
        parts.append(get_random_string(6))

    return parts


def replace_slashes(path_to_clean):
    path_to_clean = path_to_clean.replace('\\', '-')
    path_to_clean = path_to_clean.replace('/', '-')

    return path_to_clean


def shorten_filename(parts, max_length):
    length = 0

    if len(parts) == 1:
        parts[0] = parts[0][:max_length]
        return parts

    for part in parts:
        length += len(part)

    if length <= max_length:
        return parts

    if len(parts[1]) > 8:
        parts[1] = parts[1][:8]
        length = len(parts[0]) + len(parts[1])

    if length > max_length:
        length_allowed_for_first_part = max_length - len(parts[1])
        parts[0] = parts[0][:length_allowed_for_first_part]

    return parts


def shorten_directory_name(parts, max_length):
    return [part[:max_length] for part in parts]


def find_valid_full_file_path(path_to_file: Path) -> Path:
    """
    Test if file exists and add an incrementing number to the file name until a valid file name is found.

    Parameters
    ----------
    path_to_file:
        PAth object of the absolute path to a file

    Returns
    -------
    path_to_file
        Path object of the absolute path for the new incremented file name
    """
    n = 0
    path_to_folder = path_to_file.parent
    stem = path_to_file.stem
    while path_to_file.exists():
        n += 1
        path_to_file = Path(path_to_folder, f"{stem}-{n}{path_to_file.suffix}")

    return path_to_file


def add_random_string_to_file_name(path, length: int):
    """
    Add a random character sting to a file name.

    The path can be the file name or a path including the file name.
    For example '/something/file.txt' becomes '/something/file-kjgd.txt' if length is 4

    Parameters
    ----------
    path : string or pathlib.Path object
        filename or full path to file
    length : int
        length of random character strong to be added to end of file name.
    Returns
    -------
    Path:
        pathlib.Path object of the new path/filename
    """
    stem = Path(path).stem
    stem = f"{stem}-{get_random_string(length)}"
    new_filename = f"{stem}{Path(path).suffix}"
    path = Path(Path(path).parent, new_filename)
    return path


def get_random_string(length: int):
    """Return a string of length random characters.  If length is zero or negative value empty string is returned."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def add_strong_between_tags(front_tag, rear_tag, old_html):
    """
    Add <strong> tags inside of the provided front and rear tag throughout the entire html content provided.

    If the tags provided are not found no replacement is made.  There is no validation of tag validity.

    Parameters
    ----------
    front_tag : str
        String representing the front tag to be replaced for example '<p>'.
    rear_tag : str
        String representing the rear tag to be replaced for example '</p>'.
    old_html : str
        String containing the html content to be searched for tags that will be replaced.

    Returns
    -------
    str:
        html content with additional strong tags.

    """
    old_values = _find_tags(front_tag, rear_tag, old_html)
    new_values = [f'<strong>{item}</strong>' for item in old_values]
    return _update_html_with_changed_tags(front_tag, rear_tag, front_tag, rear_tag,
                                           old_html, old_values, new_values)


def change_html_tags(front_tag, rear_tag, new_front_tag, new_rear_tag, old_html):
    """
    Replace a given pair of tags with a new set of tags throughout the entire html content provided.

    If the tags provided are not found no replacement is made.  There is no validation of tag validity.

    Parameters
    ----------
    front_tag : str
        String representing the front tag to be replaced for example '<p>'.
    rear_tag : str
        String representing the rear tag to be replaced for example '</p>'.
    new_front_tag : str
        String representing the new front tag to be replaced for example '<div>'.
    new_rear_tag : str
        String representing the rear tag to be replaced for example '</div>'.
    old_html : str
        String containing the html content to be searched for tags that will be replaced.

    Returns
    -------
    str:
        html content with replaced tags.

    """
    values = _find_tags(front_tag, rear_tag, old_html)
    return _update_html_with_changed_tags(front_tag, rear_tag, new_front_tag, new_rear_tag,
                                           old_html, values)


def _update_html_with_changed_tags(front_tag, rear_tag, new_front_tag, new_rear_tag,
                                    html, old_values, new_values=None):
    if new_values is None:
        new_values = old_values
    for i in range(len(old_values)):
        html = html.replace(f'{front_tag}{old_values[i]}{rear_tag}',
                            f'{new_front_tag}{new_values[i]}{new_rear_tag}')
    return html


def _find_tags(front_tag, rear_tag, html):
    return re.findall(f'{front_tag}([^<]*){rear_tag}', html)


def log_traceback(e):
    traceback_lines = traceback.format_exception(e.__class__, e, e.__traceback__)
    traceback_text = ''.join(traceback_lines)

    return traceback_text
