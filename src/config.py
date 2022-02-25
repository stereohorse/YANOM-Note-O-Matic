import logging

import helper_functions


class YanomGlobals:
    def __init__(self):
        self._windows_path_part_max_length = 64
        self._posix_path_part_max_length = 255
        self._default_attachment_folder = 'attachments'
        self._default_export_folder = 'notes'
        self._logger_level = logging.INFO
        self._is_silent = False
        self._data_dir = 'data'
        self._version = '1.7.0-beta1'
        self._app_sub_name = 'Note-O-Matic'
        self._app_name = 'YANOM'

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

    @property
    def is_silent(self):
        return self._is_silent

    @is_silent.setter
    def is_silent(self, value: bool):
        self._is_silent = value

    @property
    def data_dir(self):
        return self._data_dir

    @property
    def version(self):
        return self._version

    @property
    def app_sub_name(self):
        return self._app_sub_name

    @property
    def app_name(self):
        return self._app_name


yanom_globals = YanomGlobals()
