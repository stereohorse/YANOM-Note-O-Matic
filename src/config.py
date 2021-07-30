import os

APP_NAME = 'YANOM'
APP_SUB_NAME = 'Note-O-Matic'
VERSION = '1.3.3'
DATA_DIR = 'data'


class YanomGlobals:
    def __init__(self):
        self._windows_path_part_max_length = 32
        self._posix_path_part_max_length = 64

    @property
    def path_part_max_length(self):
        if os.name == 'nt':
            return self._windows_path_part_max_length

        return self._posix_path_part_max_length


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
