from collections import namedtuple
import ctypes
import errno
import os
from pathlib import Path, PureWindowsPath, PurePath
import random
import re
import string
import sys
import traceback
from typing import Optional, Tuple, Union
import unicodedata
from urllib import parse
from urllib.parse import unquote_plus

import filetype

FileNameOptions = namedtuple('FileNameOptions',
                             'max_length allow_unicode allow_uppercase allow_non_alphanumeric allow_spaces '
                             'space_replacement',
                             )


def file_uri_to_path(file_uri: str, path_class=PurePath):
    """
    This function returns a pathlib.PurePath object for the supplied file URI.

    Parameters
    ==========
    file_uri : str
        The file URI
    path_class : The type of path in the file_uri. By default it uses
        the system specific path pathlib.PurePath, to force a specific type of path
        pass pathlib.PureWindowsPath or pathlib.PurePosixPath

    Returns
    =======
    pathlib.PurePath object

    """
    windows_path = isinstance(path_class(), PureWindowsPath)
    file_uri_parsed = parse.urlparse(file_uri)
    file_uri_path_unquoted = parse.unquote(file_uri_parsed.path)

    if windows_path and file_uri_path_unquoted.startswith("/"):  # absolute windows path
        return path_class(file_uri_parsed.netloc, file_uri_path_unquoted)

    return path_class(file_uri_path_unquoted)  # absolute linux and relative windows and linux paths


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


def generate_clean_filename(filename: str, name_options: FileNameOptions) -> str:
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
    name_options: FileNameOptions
        FileNameOptions namedtuple containing the options to apply to the name cleaning process

    Returns
    =======
    str

    """
    return _clean_file_or_directory_name(filename, name_options, is_file=True)


def generate_clean_directory_name(directory_name: str, name_options: FileNameOptions) -> str:
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
    name_options: FileNameOptions
        FileNameOptions namedtuple containing the options to apply to the name cleaning process

    Returns
    =======
    str

    """
    return _clean_file_or_directory_name(directory_name, name_options, is_file=False)


def generate_clean_directory_path(directory_name: str, name_options: FileNameOptions) -> str:
    """
    Clean a directory path.

    Test each path part and if it exists there is no cleaning. Only non existing parts of the path are cleaned.
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
    name_options: FileNameOptions
        FileNameOptions namedtuple containing the options to apply to the name cleaning process

    Returns
    =======
    str

    """
    cleaned_path = ''
    directory_name = directory_name.strip()
    for path_part in Path(directory_name).parts:
        testing_path = Path(cleaned_path, path_part)
        try:
            if testing_path.exists():
                cleaned_path = testing_path
                continue
        except OSError:
            pass
        clean_part = _clean_file_or_directory_name(path_part, name_options, is_file=False)
        cleaned_path = Path(cleaned_path, clean_part)

    return str(cleaned_path.as_posix())


def _clean_file_or_directory_name(dirty_name: str, name_options: FileNameOptions, is_file=True) -> str:
    if not dirty_name or dirty_name == '.' or dirty_name == '..':
        return get_random_string(6)

    dirty_name = dirty_name.strip(' ')  # strip leading and trailing spaces
    dirty_name = dirty_name.lstrip('.')
    dirty_name = unquote_plus(dirty_name)
    dirty_name = replace_slashes(dirty_name)
    parts = dirty_name.split('.')
    parts = clean_path_parts(name_options, parts)
    parts = prepend_reserved_windows_names(parts)
    parts = add_random_string_to_any_empty_path_parts(parts)

    if is_file:
        parts = shorten_filename(parts, name_options.max_length)
        clean_filename = join_name_parts(parts)

        return clean_filename

    dirty_name = join_name_parts(parts)
    clean_directory_name = shorten_directory_name(dirty_name, name_options.max_length)

    return clean_directory_name


def join_name_parts(parts):
    if len(parts) > 1:
        parts[-1] = parts[-1].lstrip('.')
        new_path_part_name = '.'.join(parts)
    else:
        new_path_part_name = f"{parts[0]}"

    return new_path_part_name


def clean_path_parts(name_options: FileNameOptions, parts: list):
    for i in range(len(parts)):
        if not len(parts[i]):
            continue

        parts[i] = process_path_part_for_unicode(name_options.allow_unicode, parts[i])

        parts[i] = strip_unwanted_chars_from_path_part(name_options, parts[i])

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


def strip_unwanted_chars_from_path_part(name_options: FileNameOptions, raw_part):
    # Always clean windows reserved characters and characters not allowed in markdown links - #^[]|()
    raw_part = re.sub(r'[<>:"/\\|?*#^\[\]()]', '-', raw_part)

    if not name_options.allow_non_alphanumeric:
        # remove anything not a alpha numeric, white, space or dash
        raw_part = re.sub(r'[^\w\s-]', '', raw_part)

    if not name_options.allow_spaces:
        # replace spaces
        raw_part = re.sub(r'[\s]+', name_options.space_replacement, raw_part)

    # replace multiple dashes
    raw_part = re.sub(r'[-]+', '-', raw_part)

    # strip leading and trailing dash or underscore
    cleaned_part = raw_part.strip('-_.')

    if not name_options.allow_uppercase:
        cleaned_part = cleaned_part.lower()

    return cleaned_part


def process_path_part_for_unicode(allow_unicode, raw_part):
    if allow_unicode:
        cleaned_part = unicodedata.normalize('NFKC', raw_part)
    else:
        cleaned_part = unicodedata.normalize('NFKD', raw_part)
        cleaned_part = cleaned_part.encode('ascii', 'ignore')
        cleaned_part = cleaned_part.decode('ascii')

    return cleaned_part


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


def shorten_directory_name(name, max_length):
    return name[:max_length]


def find_valid_full_file_path(path_to_file: Path) -> Path:
    """
    Test if file exists and add an incrementing number to the file name until a valid file name is found.

    Parameters
    ----------
    path_to_file:
        Path object of the absolute path to a file

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


def are_windows_long_paths_disabled():
    """
    On a windows system check registry to see if long file names are enabled or disabled

    Returns
    =======
    None: if not a windows system
    Bool: False if long names ARE enabled. True if not enabled i.e. disabled
    """

    if os.name != 'nt':
        return

    ntdll = ctypes.WinDLL('ntdll')

    if hasattr(ntdll, 'RtlAreLongPathsEnabled'):
        ntdll.RtlAreLongPathsEnabled.restype = ctypes.c_ubyte
        ntdll.RtlAreLongPathsEnabled.argtypes = ()

        return not bool(ntdll.RtlAreLongPathsEnabled())

    return True


def file_extension_from_bytes(file_bytes: bytes) -> Optional[str]:
    """
    From file byte content identify the type of file, if recognised return the suffix extension, else returns None

    Parameters
    ==========
    file_bytes : bytes

    Returns
    =======
    str or None
        Str - suffix including dot is file is recognised, e.g. '.jpg'
        None - File type was not recognised

    """
    kind_of_file = filetype.guess(file_bytes)
    if kind_of_file:
        return f".{kind_of_file.extension}"
    # Note file type supports other inputs -
    # Str of path to a file, bytes, bytearray, readable file like object, PurePath, memoryview


def is_available_to_use(path_to_dir: Union[str, Path]) -> bool:
    """Test if a directory is empty or does not exist.

     A directory is considered available if it contains no files or directories other than hidden
     files beginning with dot '.'.  If the directory does not exist it is also available.

     Parameters
     ----------
     path_to_dir : str or pathlib.Path
        The path to be tested
     """
    if not Path(path_to_dir).exists():
        return True

    if not [file for file in os.listdir(path_to_dir) if not file.startswith('.')]:
        return True

    return False


def next_available_directory_name(path_to_dir: Union[str, Path]) -> Union[str, Path]:
    """
    Return the name of the next available empty or unused directory name available by incrementing the name if required.

    A directory is considered empty if it contains no files or directories other than hidden files i.e. ".files".
    If the directory provided is not empty increment the directory name by adding "-number" e.g. directory-1
    If the directory is empty it is returned unchanged.
    If the directory ends in a number the number will be incremented so "directory1" becomes "directory2",
    "directory-1" becomes "directory-2"

    Parameters
    ----------
    path_to_dir : str or pathlib.Path
        The path to be tested

    Returns
    -------
    str or pathlib.Path
        returns the same type as path_to_dir

    """

    if Path(path_to_dir).is_file():
        raise ValueError(f'Path "{path_to_dir}" is to a file not a directory')

    provided_type = type(path_to_dir)
    n = get_trailing_number(str(path_to_dir))
    if n is None:
        n = 0
        new_path = path_to_dir
        while not is_available_to_use(new_path):
            n += 1
            new_path = Path(f'{path_to_dir}-{n}')
    else:
        new_path = path_to_dir
        numberless_path = str(path_to_dir).strip(str(n))
        while not is_available_to_use(new_path):
            n += 1
            new_path = Path(f'{numberless_path}{n}')

    return provided_type(new_path)


def get_trailing_number(string_to_search: str):
    match = re.search(r'\d+$', string_to_search)
    return int(match.group()) if match else None


ERROR_INVALID_NAME = 123
# Windows-specific error code indicating an invalid pathname. used in is_pathname_valid
# See Also
# ----------
# https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
#     Official listing of all such codes.


def is_pathname_valid(pathname: str) -> bool:
    """
    `True` if the passed pathname is a valid pathname for the current OS;
    `False` otherwise.
    """

    # If this pathname is either not a string or is but is empty, this pathname
    # is invalid.
    try:
        if not isinstance(pathname, str) or not pathname:
            return False

        # Strip this pathname's Windows-specific drive specifier (e.g., `C:\`)
        # if any. Since Windows prohibits path components from containing `:`
        # characters, failing to strip this `:`-suffixed prefix would
        # erroneously invalidate all valid absolute Windows pathnames.
        _, pathname = os.path.splitdrive(pathname)

        # Directory guaranteed to exist. If the current OS is Windows, this is
        # the drive to which Windows was installed (e.g., the "%HOMEDRIVE%"
        # environment variable); else, the typical root directory.
        root_dirname = os.environ.get('HOMEDRIVE', 'C:') if os.name == 'nt' else os.path.sep
        assert os.path.isdir(root_dirname)   # ...Murphy and her ironclad Law

        # Append a path separator to this directory if needed.
        root_dirname = root_dirname.rstrip(os.path.sep) + os.path.sep

        # Test whether each path component split from this pathname is valid or
        # not, ignoring non-existent and non-readable path components.
        for pathname_part in pathname.split(os.path.sep):
            try:
                os.lstat(root_dirname + pathname_part)
            # If an OS-specific exception is raised, its error code
            # indicates whether this pathname is valid or not. Unless this
            # is the case, this exception implies an ignorable kernel or
            # filesystem complaint (e.g., path not found or inaccessible).
            #
            # Only the following exceptions indicate invalid pathnames:
            #
            # * Instances of the Windows-specific "WindowsError" class
            #   defining the "winerror" attribute whose value is
            #   "ERROR_INVALID_NAME". Under Windows, "winerror" is more
            #   fine-grained and hence useful than the generic "errno"
            #   attribute. When a too-long pathname is passed, for example,
            #   "errno" is "ENOENT" (i.e., no such file or directory) rather
            #   than "ENAMETOOLONG" (i.e., file name too long).
            # * Instances of the cross-platform "OSError" class defining the
            #   generic "errno" attribute whose value is either:
            #   * Under most POSIX-compatible OSes, "ENAMETOOLONG".
            #   * Under some edge-case OSes (e.g., SunOS, *BSD), "ERANGE".
            except OSError as exc:
                if hasattr(exc, 'winerror'):
                    if exc.winerror == ERROR_INVALID_NAME:
                        return False
                elif exc.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
    # If a "ValueError" exception was raised, it almost certainly has the
    # error message "embedded NUL character" indicating an invalid pathname.
    except ValueError:
        return False
    # If no exception was raised, all path components and hence this
    # pathname itself are valid. (Praise be to the curmudgeonly python.)
    else:
        return True
    # If any other exception was raised, this is an unrelated fatal issue
    # (e.g., a bug). Permit this exception to unwind the call stack.


def absolute_path_for(provided_path: Path, root_path: Path) -> Path:
    """
    Return an absolute path including root_path if provided path is a relative path, else return provided_path

    Parameters
    ----------
    provided_path : Path
        absolute or relative path
    root_path : Path
        absolute path a provided relative path will be added to

    Returns
    -------
    Path
        Absolute path if provided_path is relative and root_path is absolute.  Else will return
        the provided_path which is an absolute path not on root_path.


    """
    if provided_path.is_absolute():
        return provided_path

    return Path(root_path, provided_path)


def relative_path_for(provided_path: Path, root_path: Path) -> Path:
    """
    Return relative path to root is provided path is on root_path, If not return the provided path

    Parameters
    ----------
    provided_path : Path
        absolute or relative path
    root_path : Path
        absolute path the relative path will stem from

    Returns
    -------
    Path
        relative path if provided_path is relative or provided_path is on root_path.  Else will return
        the provided_path which will be an absolute path.

    """
    if provided_path.is_absolute():
        if provided_path == root_path:
            return provided_path

        if provided_path.is_relative_to(root_path):
            return provided_path.relative_to(root_path)

    return provided_path


def is_path_valid(path: str) -> bool:
    # Modified from
    # https://gist.github.com/mo-han/240b3ef008d96215e352203b88be40db
    # whixh itself was modified from an answer by Cecil Curry at:
    # https://stackoverflow.com/questions/9532499/check-whether-a-path-is-valid-in-python-without-creating-a-file-at-the-paths-ta/34102855#34102855
    try:
        if not isinstance(path, str) or not path:
            return False
        if os.name == 'nt':
            drive, path = os.path.splitdrive(path)
            if not os.path.isdir(drive):
                drive = os.environ.get('SystemDrive', 'C:')
            # if not os.path.isdir(drive):
            #     drive = ''
        else:
            drive = ''
        parts = Path(path).parts
        check_list = [os.path.join(*parts), *parts]
        for x in check_list:
            try:
                os.lstat(drive + x)
            except OSError as e:
                if hasattr(e, 'winerror') and e.winerror == 123:
                    return False
                elif e.errno in {errno.ENAMETOOLONG, errno.ERANGE}:
                    return False
            except ValueError:
                return False
                # If a "ValueError" exception was raised, it almost certainly has the
                # error message "embedded NUL character" indicating an invalid pathname
    except TypeError:
        return False
    else:
        return True


def path_to_uri(path: Path) -> str:
    if path.is_absolute() and os.name == 'nt':
        return path.as_uri()

    return path.as_posix()


def path_to_posix_str(path: Union[Path, str]) -> str:
    if isinstance(path, str):
        path_as_posix_str = Path(path).as_posix()
    else:
        path_as_posix_str = path.as_posix()

    if path_as_posix_str == '.':
        return ""

    return path_as_posix_str


def replace_markdown_pseudo_html_href_tag_with_markdown_links(content: str) -> str:
    """
    Reformat markdown pseudo html href tag to markdown formatted links in the provided content

    <https://github.com/kevindurston21/YANOM-Note-O-Matic>
    becomes
    [github.com/kevindurston21/YANOM-Note-O-Matic](https://github.com/kevindurston21/YANOM-Note-O-Matic)

    The "pseudo" html tag is generated by pandoc when converting an 'a' tag where the text is the same as the
    actual href link itself like this:
    <a href="http://github.com/kevindurston21">http://github.com/kevindurston21</a>


    Parameters
    ==========
    content :  str
        Markdown content

    Returns
    =======
    str
        Updated content with replaced image links

    """
    regex = r"(<(https?://(.*?))>)"
    # three groups whole thing, the link and the link minus http

    matches = re.finditer(regex, content, re.MULTILINE)

    for match in matches:
        new_link_tag = f"[{match.group(3)}]({match.group(2)})"
        content = content.replace(f'{match.group(1)}', new_link_tag)

    return content


def unescape(text):
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&amp;", "&")
    return text
