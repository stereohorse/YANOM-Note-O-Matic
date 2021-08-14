import json
import logging
import sys
import zipfile

import config
import helper_functions

logger = logging.getLogger(f'{config.yanom_globals.app_name}.{__name__}')
logger.setLevel(config.yanom_globals.logger_level)


def read_json_data(zip_filename, target_filename, message=''):
    """
    Read a text file containing json from a zip archive and return a dictionary of the files json content

    Json data is read from a file in the zip archive and returned as a dictionary.

    Parameters
    ----------
    zip_filename : Path
        Path object to the zipfile
    target_filename : str
        name of the file in the zip archive to be read from
    message : str
        Optional string to include in error messages, default is empty string

    Returns
    -------
    dict:
        dictionary of the json data OR None is an error is encountered

    """
    try:
        with zipfile.ZipFile(str(zip_filename), 'r') as zip_file:
            return json.loads(zip_file.read(target_filename).decode('utf-8'))
    except Exception as e:
        _error_handling(e, target_filename, zip_filename, message)


def read_binary_file(zip_filename, target_filename, message=''):
    """
    Read and return binary content from a file stored in a zip archive.

    Parameters
    ----------
    zip_filename : Path
        Path object to the zipfile
    target_filename : str
        name of the file in the zip archive to be read from
    message : str
        Optional string to include in error messages, default is empty string

    Returns
    -------
    bytes

    """
    try:
        with zipfile.ZipFile(str(zip_filename), 'r') as zip_file:
            return zip_file.read(target_filename)

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
        sys.exit(1)

    if isinstance(e, KeyError):
        msg = f'Warning - For the note "{message}" - unable to find the file "{target_filename}" in the zip file "{zip_filename}"'

    logger.warning(msg)
    logger.warning(traceback_text)
    if not config.yanom_globals.is_silent:
        print(msg)


