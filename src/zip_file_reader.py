import json
import logging
import sys
import zipfile
from pathlib import Path
from typing import List, Optional, Set

import config
import helper_functions

logger = logging.getLogger(f'{config.yanom_globals.app_name}.{__name__}')
logger.setLevel(config.yanom_globals.logger_level)


def list_files_in_zip_file_from_a_directory(zip_file_path: str,
                                            path_inside_of_zipfile: str = '',
                                            filenames_to_ignore: Optional[List[str]] = None
                                            ) -> Set[Path]:
    """
    Return a list of files from a directory within a zipfile.

    The list of files returned is for a single directory within the zipfile.
    An empty string for path_inside_of_zipfile represents the root of the zip file.  Sub directories are access by
    passing a string of the path inside the the zip file.  'sub_folder' will return files in a directory called
    sub_folder that is in the root of the zip file.  'sub_folder/sub_sub_folder' would return the files with in the
    sub_sub_folder directory of the zip file.  If the directory does not exist an empty set is returned.
    The list of files paths returned can be further filtered by passing a list strings of names to ignore.  Only exact
    matches are ignored.  Passing ['file1.txt, 'file2.txt'] will exclude those files form the returned list if
    they exist.

    Parameters
    ----------
    zip_file_path : str
        Path to a zip file.
    path_inside_of_zipfile : str
        default is empty string which returns files in the root of the zip file.  if a non-empty string representing
        a path in the zip file is provided files in a directory matching that string will be returned.  String must be
        posix format.
    filenames_to_ignore : Optional list[str]
        Optional list of stings of file names that can be ignored.

    Returns
    -------
    list[Path]
        list containing paths to files in the zip file
    """

    if not filenames_to_ignore:
        filenames_to_ignore = []

    files_in_zip = set()

    try:
        zip_root_path = zipfile.Path(zip_file_path)
        folder_to_search = zip_root_path

        if path_inside_of_zipfile:
            folder_to_search = zip_root_path.joinpath(path_inside_of_zipfile)
            if not folder_to_search.exists():
                logger.warning(f'Directory "{folder_to_search}" does not exist in zip file "{zip_file_path}"')
                return set()

        for item in folder_to_search.iterdir():
            if item.is_file() and item.name not in filenames_to_ignore:
                files_in_zip.add(item)

        return files_in_zip

    except Exception as e:
        _error_handling(e, '', zip_file_path, '')


def read_text(zip_filename, target_filename, message=''):
    """
    Read a text file from a zip archive and return string of that content

    Parameters
    ----------
    zip_filename : Path
        Path object to the zipfile
    target_filename : Path
        name of the file in the zip archive to be read from
    message : str
        Optional string to include in error messages, default is empty string

    Returns
    -------
    str:
        string of the text files content

    """
    try:
        with zipfile.ZipFile(str(zip_filename), 'r') as zip_file:
            # str(WindowsPath) gives a folder\\filename but zip files must have a posix formatted string
            # do use Path.as_posix to get correct format for accessing zip file
            return zip_file.read(target_filename.as_posix()).decode('utf-8')
    except Exception as e:
        _error_handling(e, target_filename, zip_filename, message)


def read_json_data(zip_filename, target_filename, message=''):
    """
    Read a text file containing json from a zip archive and return a dictionary of the files json content

    Json data is read from a file in the zip archive and returned as a dictionary.

    Parameters
    ----------
    zip_filename : Path
        Path object to the zipfile
    target_filename : Path
        path inside the zipfile and name of the file in the zip archive to be read from
    message : str
        Optional string to include in error messages, default is empty string

    Returns
    -------
    dict:
        dictionary of the json data OR None is an error is encountered

    """
    try:
        return json.loads(read_text(zip_filename, target_filename, message))
    except Exception as e:
        _error_handling(e, target_filename, zip_filename, message)


def read_binary_file(zip_filename, target_filename, message=''):
    """
    Read and return binary content from a file stored in a zip archive.

    Parameters
    ----------
    zip_filename : Path
        Path object to the zipfile
    target_filename : Path
        name of the file in the zip archive to be read from
    message : str
        Optional string to include in error messages, default is empty string

    Returns
    -------
    bytes

    """
    try:
        with zipfile.ZipFile(str(zip_filename), 'r') as zip_file:
            # str(WindowsPath) gives a folder\\filename but zip files must have a posix formatted string
            # do use Path.as_posix to get correct format for accessing zip file
            return zip_file.read(target_filename.as_posix())

    except Exception as e:
        _error_handling(e, target_filename, zip_filename, message)


def _error_handling(e, target_filename, zip_filename, message=''):
    """Error handling for errors encountered reading form zip files"""

    traceback_text = helper_functions.log_traceback(e)
    msg = f'Error - {e}'

    if isinstance(e, FileNotFoundError):
        msg = f'Error - unable to read zip file "{zip_filename}"'
        logger.error(msg)
        logger.error(traceback_text)
        if not config.yanom_globals.is_silent:
            print(msg)
        sys.exit(1)  # TODO need a more graceful handling than this

    if isinstance(e, KeyError):
        msg = f'Warning - For the note "{message}" ' \
              f'- unable to find the file "{target_filename}" in the zip file "{zip_filename}"'

    if isinstance(e, ValueError):
        msg = "Warning Value Error accessing zip file contents, possibly treating file as directory or vice versa."

    logger.warning(msg)
    logger.warning(traceback_text)
    if not config.yanom_globals.is_silent:
        print(msg)
