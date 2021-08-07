import logging

import helper_functions

APP_NAME = 'YANOM'
APP_SUB_NAME = 'Note-O-Matic'
VERSION = '1.3.3'
DATA_DIR = 'data'


class YanomGlobals:
    def __init__(self):
        self._windows_path_part_max_length = 64
        self._posix_path_part_max_length = 255
        self._default_attachment_folder = 'attachments'
        self._default_export_folder = 'notes'
        self._logger_level = logging.INFO

    @property
    def path_part_max_length(self):
        if helper_functions.are_windows_long_paths_disabled():
            return self._windows_path_part_max_length

        return self._posix_path_part_max_length

    @property
    def default_attachment_folder(self):
        return self._default_attachment_folder

    @property
    def default_export_folder(self):
        return self._default_export_folder

    @property
    def logger_level(self):
        return self._logger_level

    @logger_level.setter
    def logger_level(self, value: int):
        self._logger_level = value


yanom_globals = YanomGlobals()

global logger_level
logger_level = 20  # INFO

global silent
silent = False


def set_logger_level(level: int):
    global logger_level
    logger_level = level


def set_silent(silent_mode: bool):
    global silent
    silent = silent_mode
