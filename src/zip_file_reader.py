import json
import logging
import traceback
import zipfile

import config
# import yanom
import helper_functions

logger = logging.getLogger(f'{config.APP_NAME}.{__name__}')
logger.setLevel(config.logger_level)


def read_json_data(zip_filename, target_filename):
    """
    Read a text file containing json from a zip archive and return a dictionary of the files json content

    Json data is read from a file in the zip archive and returned as a dictionary.

    Parameters
    ----------
    zip_filename : Path
        Path object to the zipfile
    target_filename : str
        name of the file in the zip archive to be read from

    Returns
    -------
    dict:
        dictionary of the json data OR None is an error is encountered

    """
    try:
        with zipfile.ZipFile(str(zip_filename), 'r') as zip_file:
            return json.loads(zip_file.read(target_filename).decode('utf-8'))
    except Exception as e:
        _error_handling(e, target_filename, zip_filename)


def read_binary_file(zip_filename, target_filename):
    """
    Read and return binary content from a file stored in a zip archive.

    Parameters
    ----------
    zip_filename : Path
        Path object to the zipfile
    target_filename : str
        name of the file in the zip archive to be read from

    Returns
    -------
    binary str

    """
    try:
        with zipfile.ZipFile(str(zip_filename), 'r') as zip_file:
            return zip_file.read(target_filename)
    except Exception as e:
        _error_handling(e, target_filename, zip_filename)


def _error_handling(e, target_filename, zip_filename):
    """Error handling for errors encountered reading form zip files"""

    traceback_text = helper_functions.log_traceback(e)
    msg = f'Error - {e}'

    if isinstance(e, FileNotFoundError):
        msg = f'Error - unable to read zip file "{zip_filename}"'

    if isinstance(e, KeyError):
        msg = f'Error - unable to find the file "{target_filename}" in the zip file "{zip_filename}"'

    logger.error(msg)
    logger.error(traceback_text)
    if not config.silent:
        print(msg)

