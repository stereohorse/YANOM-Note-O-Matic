from io import BytesIO
import logging
from pathlib import Path

import config
import helper_functions

logger = logging.getLogger(f'{config.APP_NAME}.{__name__}')
logger.setLevel(config.logger_level)


def store_file(absolute_path, content_to_save):

    logger.debug(f"Storing attachment {absolute_path}")
    if isinstance(content_to_save, str):
        write_text(absolute_path, content_to_save)
        return

    if isinstance(content_to_save, bytes):
        write_bytes(absolute_path, content_to_save)
        return

    if isinstance(content_to_save, BytesIO):
        write_bytes_io(absolute_path, content_to_save)
        return

    logger.warning(f"content type {type(content_to_save)} was not recognised for path {absolute_path}")


def write_text(absolute_path, content_to_save):
    try:
        Path(absolute_path).write_text(content_to_save, encoding="utf-8")
    except Exception as e:
        error_handling(e, 'text file')


def write_bytes(absolute_path, content_to_save):
    try:
        Path(absolute_path).write_bytes(content_to_save)
    except Exception as e:
        error_handling(e, 'bytes file')


def write_bytes_io(absolute_path, content_to_save):
    try:
        Path(absolute_path).write_bytes(content_to_save.getbuffer())
    except Exception as e:
        error_handling(e, 'bytes IO buffer')


def error_handling(e, write_type):
    if isinstance(e, FileNotFoundError):
        logger.error(f"Attempting to write {write_type} to invalid path - {e}")
        if helper_functions.are_windows_long_paths_disabled():
            logger.error("Windows long file paths are not enabled check path length is not too long.")
        logger.error(helper_functions.log_traceback(e))
        return

    if isinstance(e, IsADirectoryError):
        logger.error(f"Attempting to write {write_type} to an existing directory name not a file - {e}")
        logger.error(helper_functions.log_traceback(e))
        return

    if isinstance(e, IOError):
        logger.error(f"Attempting to write {write_type} failed - {e}")
        logger.error(helper_functions.log_traceback(e))
