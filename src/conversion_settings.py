"""
A class for provision of conversion settings for manual or specific pre configured sets of conversion settings

Quick set Functions to set the conversion settings values to values for common or typical conversion jobs.
"""
import logging
from pathlib import Path
import sys
from typing import Literal

import config
import helper_functions
from config import yanom_globals
from helper_functions import generate_clean_directory_name, find_working_directory


def what_module_is_this():
    return __name__


class ConversionSettings:
    """
    Conversion settings required to convert input formats to export formats.

    Attributes
    ----------
    logger : logger object
        used for program logging
    _valid_conversion_inputs : list of strings
        List of file formats that can be converted
    _valid_markdown_conversion_inputs : list of strings
        List of markdown formats that can be converted
    _valid_quick_settings : list of strings
        Quick settings strings that are used to create 'default' conversions for various program and file types.
        Also are the values used in an object generator to create child classes
    _valid_export_formats : list of strings
        Export format names used to trigger specific conversion behaviour in style of file type
    _source : pathlib.Path
        Directory to search for nsx files or path to specific nsx file
    _conversion_input : str
        The type of file to be converted
    _markdown_conversion_input : str
        The markdown format for the markdown files if they are the file type to be converted
    _quick_setting: str
        A trigger string used for a default set for some of the following filed values
    _export_format: str
        The export format to be used
    _front_matter_format: str
        Meta data to be placed in a yaml/json/toml front matter section above the body of the main text
    _tag_prefix: str
        Prefix to place on tags
    spaces_in_tags: bool
        Allow spaces in tag names
    split_tags: bool
        Split tags into separate tags where the input was a grouped tag format e.g. /coding/python -> coding python
    _export_folder: pathlib.Path
        Path object for the relative or absolute path to place exported notes into
    _export_folder_absolute: pathlib.Path
        Path object for the absolute path to place exported notes into
    _attachment_folder_name: pathlib.Path
        Path object for the sub-directory name within the export folder to place images and attachments
    _creation_time_in_exported_file_name: bool
        Include the note creation time on the end of the file name
    _allow_spaces_in_file_names: bool
        Allow spaces in file and directory names
    _allow_unicode_in_file_names: bool
        Allow unicode characters in file and directory names
    _allow_uppercase_in_file_names: bool
        Allow uppercase characters in file and directory names
    _allow_non_alphanumeric_in_file_names: bool
        Allow characters other than a-z, A-Z,0-9 characters in file and directory names.  Windows reserved
        characters will not be allowed.
    _filename_spaces_replaced_by: str
        String containing the replacement for any spaces in file and directory names.  Empty string is allowed
     _maximum_file_or_directory_name_length: int
        Integer of maximum length for a directory or file name.  Maximums are set as global variable Windows 32,
        everything else 64. Can be set to maximum or smaller value
    _working_directory: Path
        The base working directory for the program execution. This is not stored in ini files it is used for program
        execution only
    _source_absolute_root: Path
        An absolute path to the source files

    Methods
    -------
    set_from_dictionary
        Change conversion settings from a provided dictionary of settings.
    set_quick_setting
        Set conversion settings to predefined template when provided a valid string representing a quick setting
        key word.

    """

    validation_values = {
        'conversion_inputs': {
            'conversion_input': ('nsx', 'html', 'markdown')
        },
        'markdown_conversion_inputs': {
            'markdown_conversion_input': (
                'obsidian', 'gfm', 'commonmark', 'q_own_notes', 'pandoc_markdown_strict', 'pandoc_markdown',
                'multimarkdown')
        },
        'quick_settings': {
            'quick_setting': (
                'manual', 'q_own_notes', 'obsidian', 'gfm', 'commonmark', 'pandoc_markdown', 'pandoc_markdown_strict',
                'multimarkdown', 'html')
        },
        'export_formats': {
            'export_format': (
                'q_own_notes', 'obsidian', 'gfm', 'pandoc_markdown', 'commonmark', 'pandoc_markdown_strict',
                'multimarkdown', 'html')
        },
        'meta_data_options': {
            'front_matter_format': ('yaml', 'toml', 'json', 'text', 'none'),
            'metadata_schema': '',
            'tag_prefix': '',
            'spaces_in_tags': ('True', 'False'),
            'split_tags': ('True', 'False')
        },
        'table_options': {
            'first_row_as_header': ('True', 'False'),
            'first_column_as_header': ('True', 'False')
        },
        'chart_options': {
            'chart_image': ('True', 'False'),
            'chart_csv': ('True', 'False'),
            'chart_data_table': ('True', 'False')
        },
        'file_options': {
            'source': '',
            'export_folder': '',
            'attachment_folder_name': '',
            'allow_spaces_in_filenames': ('True', 'False'),
            'filename_spaces_replaced_by': '',
            'allow_unicode_in_filenames': ('True', 'False'),
            'allow_uppercase_in_filenames': ('True', 'False'),
            'allow_non_alphanumeric_in_filenames': ('True', 'False'),
            'creation_time_in_exported_file_name': ('True', 'False'),
            'maximum_file_or_directory_name_length': '',
        }
    }

    def __init__(self):
        # if you change any of the following values changes are likely to affect the quick settings method
        # and the validation_values class variable
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._valid_conversion_inputs = list(self.validation_values['conversion_inputs']['conversion_input'])
        self._valid_markdown_conversion_inputs = list(
            self.validation_values['markdown_conversion_inputs']['markdown_conversion_input'])
        self._valid_quick_settings = list(self.validation_values['quick_settings']['quick_setting'])
        self._valid_export_formats = list(self.validation_values['export_formats']['export_format'])
        self._valid_front_matter_formats = list(
            self.validation_values['meta_data_options']['front_matter_format'])
        self._source = ''
        self._conversion_input = 'nsx'
        self._markdown_conversion_input = 'gfm'
        self._quick_setting = 'gfm'
        self._export_format = 'gfm'
        self._front_matter_format = 'yaml'
        self._metadata_schema = ['']
        self._tag_prefix = '#'
        self.spaces_in_tags = False
        self.split_tags = False
        self.first_row_as_header = True
        self.first_column_as_header = True
        self.chart_image = True
        self.chart_csv = True
        self.chart_data_table = True
        self._export_folder = 'notes'
        self._attachment_folder_name = 'attachments'
        self._allow_spaces_in_file_names = True
        self._filename_spaces_replaced_by = '-'
        self._allow_unicode_in_file_names = True
        self._allow_uppercase_in_file_names = True
        self._allow_non_alphanumeric_in_file_names = True
        self._creation_time_in_exported_file_name = False
        self._maximum_file_or_directory_name_length = yanom_globals.path_part_max_length
        self._working_directory, environment_message = find_working_directory()
        self._export_folder_absolute = Path(self._working_directory, config.yanom_globals.data_dir, self._export_folder)
        self.logger.debug(environment_message)
        self._source_absolute_root = None

    def __str__(self):
        return f"{self.__class__.__name__}(valid_conversion_inputs={self.valid_conversion_inputs}, " \
               f"valid_markdown_conversion_inputs='{self.valid_markdown_conversion_inputs}', " \
               f"valid_quick_settings='{self.valid_quick_settings}', " \
               f"valid_export_formats='{self.valid_export_formats}', " \
               f"valid_front_matter_formats]'{self.valid_front_matter_formats}', " \
               f"markdown_conversion_input='{self._markdown_conversion_input}, quick_setting='{self.quick_setting}', " \
               f"export_format='{self.export_format}', " \
               f"yaml_front_matter={self.front_matter_format}, metadata_schema='{self.metadata_schema}', " \
               f"tag_prefix='{self.tag_prefix}', " \
               f"first_row_as_header={self.first_row_as_header}, " \
               f"first_column_as_header={self.first_column_as_header}" \
               f"spaces_in_tags={self.spaces_in_tags}, split_tags={self.split_tags}, " \
               f"export_folder='{self.export_folder}', " \
               f"attachment_folder_name='{self.attachment_folder_name}', " \
               f"creation_time_in_exported_file_name='{self._creation_time_in_exported_file_name})'"

    def __repr__(self):
        return repr(self.__dict__)

    def set_from_dictionary(self, settings):
        """Set conversion settings from a dictionary

        Parameters
        ----------
        settings dict:
            Dictionary of any conversion settings where key is a field of the class and value is the value to be used
            as the setting.  Values are assigned using parameters to allow data validation and any other processing
            required.  Invalid key values are ignored and a warning is output
        """
        for key, value in settings.items():
            if key in dir(self):
                setattr(self, key, value)
                continue
            msg = f'Invalid key value of {key} provided in dictionary of conversion settings'
            self.logger.warning(msg)
            if not config.yanom_globals.is_silent:
                print(msg)

    lit_valid_quick_setting = Literal['html', 'pandoc_markdown_strict', 'multimarkdown', 'pandoc_markdown',
                                      'commonmark', 'obsidian', 'gfm', 'q_own_notes', 'manual']

    def set_quick_setting(self, quick_setting: lit_valid_quick_setting):
        """

        Parameters
        ----------
        quick_setting str:
            String value of a valid quick_setting value.  This key is used to obtain a value representing a method name
            that is used to set a collection of settings that represent a quick setting

        """
        quick_settings = {
            'html': 'quick_set_html_conversion_settings',
            'pandoc_markdown_strict': 'quick_set_pandoc_markdown_strict_settings',
            'multimarkdown': 'quick_set_multimarkdown_settings',
            'pandoc_markdown': 'quick_set_pandoc_markdown_settings',
            'commonmark': 'quick_set_commonmark_settings',
            'obsidian': 'quick_set_obsidian_settings',
            'gfm': 'quick_set_gfm_settings',
            'q_own_notes': 'quick_set_qownnotes_settings',
            'manual': 'quick_set_manual_settings'
        }

        if quick_setting in quick_settings:
            getattr(self, quick_settings[quick_setting])()
            return

        msg = f"Invalid quick setting key '{quick_setting}' used"
        self.logger.error(msg)
        if not config.yanom_globals.is_silent:
            print(msg)
        sys.exit(1)

    def quick_set_manual_settings(self):
        """
        Manual conversion settings to convert input formats to export formats.

        Used for user configured selections and ConfigData Class to provide conversions read from ini files.
        """
        self.logger.debug("Manual conversion settings")
        self.quick_setting = 'manual'

    def quick_set_qownnotes_settings(self):
        """
        QOwnNotes conversion settings to convert input formats to format suitable for QOwnNotes users.
        """
        self.logger.debug("QOwnNotes Setting conversion settings")
        self.set_common_quick_settings_defaults()
        self.quick_setting = 'q_own_notes'
        self.export_format = 'q_own_notes'
        self.front_matter_format = 'yaml'

    def quick_set_gfm_settings(self):
        """
        Git-flavoured markdown conversion settings to convert input formats to gfm format.
        """
        self.logger.debug("GFM conversion settings")
        self.set_common_quick_settings_defaults()
        self.quick_setting = 'gfm'
        self.export_format = 'gfm'
        self.front_matter_format = 'yaml'

    def quick_set_obsidian_settings(self):
        """
        Obsidian conversion settings to convert input formats to format suitable for Obsidian users.
        """
        self.logger.debug("Obsidian conversion settings")
        self.set_common_quick_settings_defaults()
        self.quick_setting = 'obsidian'
        self.export_format = 'obsidian'
        self.front_matter_format = 'yaml'

    def quick_set_commonmark_settings(self):
        """
        Commonmark conversion settings
        """
        self.logger.debug("Commonmark conversion settings")
        self.set_common_quick_settings_defaults()
        self.quick_setting = 'commonmark'
        self.export_format = 'commonmark'
        self.front_matter_format = 'yaml'

    def quick_set_pandoc_markdown_settings(self):
        """
        Set Pandoc Markdown conversion settings.
        """
        self.logger.debug("Pandoc markdown conversion settings")
        self.set_common_quick_settings_defaults()
        self.quick_setting = 'pandoc_markdown'
        self.export_format = 'pandoc_markdown'
        self.front_matter_format = 'yaml'

    def quick_set_multimarkdown_settings(self):
        """
        MultiMarkdown conversion settings.
        """
        self.logger.debug("MultiMarkdown conversion settings")
        self.set_common_quick_settings_defaults()
        self.quick_setting = 'multimarkdown'
        self.export_format = 'multimarkdown'

    def quick_set_pandoc_markdown_strict_settings(self):
        """
        Set Pandoc Markdown-strict conversion settings.
        """
        self.logger.debug("Pandoc Markdown Strict Setting conversion settings")
        self.set_common_quick_settings_defaults()
        self.quick_setting = 'pandoc_markdown_strict'
        self.export_format = 'pandoc_markdown_strict'

    def quick_set_html_conversion_settings(self):
        """
        Set HTML conversion settings to convert input formats to HTML files plus attachments in a folder.
        """
        self.logger.debug("HTML conversion settings")
        self.set_common_quick_settings_defaults()
        self.export_format = 'html'
        self.quick_setting = 'html'
        self.front_matter_format = 'yaml'

    def set_common_quick_settings_defaults(self):
        self.export_folder = config.yanom_globals.default_export_folder
        self.attachment_folder_name = config.yanom_globals.default_attachment_folder
        self.metadata_schema = []
        if self.conversion_input == 'nsx':
            self.metadata_schema = ['title', 'ctime', 'mtime', 'tag']
        self.spaces_in_tags = False
        self.split_tags = False
        self.first_row_as_header = True
        self.first_column_as_header = True
        self.chart_image = True
        self.chart_csv = True
        self.chart_data_table = True
        self._allow_spaces_in_file_names = True
        self._allow_unicode_in_file_names = True
        self._allow_uppercase_in_file_names = True
        self._allow_non_alphanumeric_in_file_names = True
        self._filename_spaces_replaced_by = '-'
        self._creation_time_in_exported_file_name = False
        self._maximum_file_or_directory_name_length = yanom_globals.path_part_max_length
        self._source, self._source_absolute_root = self._set_folder_paths(Path(self._working_directory, config.yanom_globals.data_dir))

    def _set_folder_paths(self, provided_folder):
        if provided_folder == '':
            self.logger.debug(f"No provided source using relative path "
                              f"{config.yanom_globals.data_dir} as source directory")
            provided_folder = Path(self._working_directory, config.yanom_globals.data_dir)
            provided_folder_absolute = Path(self._working_directory, config.yanom_globals.data_dir)

            return provided_folder, provided_folder_absolute

        if Path(provided_folder).is_absolute():
            provided_folder_absolute = Path(provided_folder)

            if Path(provided_folder) == Path(self._working_directory, config.yanom_globals.data_dir):
                return Path(provided_folder), provided_folder_absolute

            if Path(provided_folder).is_relative_to(self._working_directory, config.yanom_globals.data_dir):
                provided_folder = Path(provided_folder).relative_to(Path(self._working_directory, config.yanom_globals.data_dir))
            else:
                provided_folder = Path(provided_folder)
            return provided_folder, provided_folder_absolute

        provided_folder = generate_clean_directory_name(provided_folder, self.filename_options)
        provided_folder = Path(provided_folder)
        provided_folder_absolute = Path(self._working_directory, config.yanom_globals.data_dir, provided_folder)
        return provided_folder, provided_folder_absolute

    @property
    def filename_options(self):

        return helper_functions.FileNameOptions(self.maximum_file_or_directory_name_length,
                                                self.allow_unicode_in_filenames,
                                                self.allow_uppercase_in_filenames,
                                                self.allow_non_alphanumeric_in_filenames,
                                                self.allow_spaces_in_filenames,
                                                self.filename_spaces_replaced_by)

    @property
    def valid_conversion_inputs(self):
        return self._valid_conversion_inputs

    @property
    def valid_markdown_conversion_inputs(self):
        return self._valid_markdown_conversion_inputs

    @property
    def valid_quick_settings(self):
        return self._valid_quick_settings

    @property
    def valid_export_formats(self):
        return self._valid_export_formats

    @property
    def valid_front_matter_formats(self):
        return self._valid_front_matter_formats

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, provided_source):
        if isinstance(provided_source, str):
            provided_source = provided_source.strip()

        self._source, self._source_absolute_root = self._set_folder_paths(provided_source)

        if self._source_absolute_root.exists():
            self.logger.info(f'Using {self._source_absolute_root} as source path')
            return

        msg = f"Invalid source location - {provided_source} - Check command line argument OR config.ini entry - Exiting program"
        if not config.yanom_globals.is_silent:
            print(msg)
        self.logger.error(msg)
        sys.exit(1)

    @property
    def conversion_input(self):
        return self._conversion_input

    @conversion_input.setter
    def conversion_input(self, value):
        value = value.strip()
        if value in self._valid_conversion_inputs:
            self._conversion_input = value
            return

        raise ValueError(f"Invalid value provided for for conversion input. "
                         f"Attempted to use {value}, valid values are {self._valid_conversion_inputs}")

    @property
    def markdown_conversion_input(self):
        return self._markdown_conversion_input

    @markdown_conversion_input.setter
    def markdown_conversion_input(self, value):
        value = value.strip()
        if value in self._valid_markdown_conversion_inputs:
            self._markdown_conversion_input = value
            return

        raise ValueError(f"Invalid value provided for for markdown conversion input. "
                         f"Attempted to use {value}, valid values are {self._valid_markdown_conversion_inputs}")

    @property
    def quick_setting(self):
        return self._quick_setting

    @quick_setting.setter
    def quick_setting(self, value):
        value = value.strip()
        if value in self.valid_quick_settings:
            self._quick_setting = value
            return

        raise ValueError(f"Invalid value provided for for quick setting. "
                         f"Attempted to use {value}, valid values are {self.valid_quick_settings}")

    @property
    def export_format(self):
        return self._export_format

    @export_format.setter
    def export_format(self, value):
        value = value.strip()
        if value in self.valid_export_formats:
            self._export_format = value
            return

        raise ValueError(f"Invalid value provided for for export format. "
                         f"Attempted to use {value}, valid values are {self.valid_export_formats}")

    @property
    def metadata_schema(self):
        return self._metadata_schema

    @metadata_schema.setter
    def metadata_schema(self, value):
        if isinstance(value, str):
            values = value.split(",")
            self._metadata_schema = [value.strip() for value in values]
            return

        if isinstance(value, list):
            if len(value) == 0:
                self._metadata_schema = ['']
                return

            self._metadata_schema = value
            return

        self.logger.warning(f'Invalid metadata schema provided {value} of type {type(value)}')

    @property
    def front_matter_format(self):
        return self._front_matter_format

    @front_matter_format.setter
    def front_matter_format(self, value: str):
        value = value.strip()
        if value in self._valid_front_matter_formats:
            self._front_matter_format = value
            return

        raise ValueError(f"Invalid value provided for for front matter format. "
                         f"Attempted to use {value}, valid values are {self._valid_front_matter_formats}")

    @property
    def tag_prefix(self):
        return self._tag_prefix

    @tag_prefix.setter
    def tag_prefix(self, value: str):
        value = value.strip()
        self._tag_prefix = value

    @property
    def export_folder(self):
        return self._export_folder

    @export_folder.setter
    def export_folder(self, provided_export_folder):
        provided_export_folder = str(provided_export_folder).strip()
        if provided_export_folder == '':
            provided_export_folder = yanom_globals.default_export_folder

        if Path(provided_export_folder).is_file():
            msg = f"Invalid path provided. Path is to existing file not a directory '{provided_export_folder}'"
            self.logger.error(msg)
            if not config.yanom_globals.is_silent:
                print(msg)
            sys.exit(1)

        self._export_folder, self._export_folder_absolute = self._set_folder_paths(provided_export_folder)

        # self._export_folder = Path(generate_clean_directory_name(value,
        #                                                          self.filename_options))

        self.logger.info(
            f'For the provided attachment folder name of "{provided_export_folder}" the cleaned name used is {self._export_folder}')
        self.logger.info(f'Using {self._export_folder_absolute} as export path')

    @property
    def export_folder_absolute(self):
        return self._export_folder_absolute

    @property
    def attachment_folder_name(self):
        return self._attachment_folder_name

    @attachment_folder_name.setter
    def attachment_folder_name(self, value):
        if value == '':
            value = yanom_globals.default_attachment_folder
        self._attachment_folder_name = Path(generate_clean_directory_name(value, self.filename_options))
        self.logger.info(
            f'For the provided attachment folder name of "{value}" the cleaned name used is {self._attachment_folder_name}')

    @property
    def working_directory(self):
        return self._working_directory

    @working_directory.setter
    def working_directory(self, path):
        self._working_directory = Path(path)

    @property
    def source_absolute_root(self):
        return self._source_absolute_root

    @property
    def allow_spaces_in_filenames(self):
        return self._allow_spaces_in_file_names

    @allow_spaces_in_filenames.setter
    def allow_spaces_in_filenames(self, value: bool):
        self._allow_spaces_in_file_names = value

    @property
    def allow_unicode_in_filenames(self):
        return self._allow_unicode_in_file_names

    @allow_unicode_in_filenames.setter
    def allow_unicode_in_filenames(self, value: bool):
        self._allow_unicode_in_file_names = value

    @property
    def allow_uppercase_in_filenames(self):
        return self._allow_uppercase_in_file_names

    @allow_uppercase_in_filenames.setter
    def allow_uppercase_in_filenames(self, value: bool):
        self._allow_uppercase_in_file_names = value

    @property
    def allow_non_alphanumeric_in_filenames(self):
        return self._allow_non_alphanumeric_in_file_names

    @allow_non_alphanumeric_in_filenames.setter
    def allow_non_alphanumeric_in_filenames(self, value: bool):
        self._allow_non_alphanumeric_in_file_names = value

    @property
    def filename_spaces_replaced_by(self):
        return self._filename_spaces_replaced_by

    @filename_spaces_replaced_by.setter
    def filename_spaces_replaced_by(self, value: str):
        self._filename_spaces_replaced_by = value

    @property
    def creation_time_in_exported_file_name(self):
        return self._creation_time_in_exported_file_name

    @creation_time_in_exported_file_name.setter
    def creation_time_in_exported_file_name(self, value: bool):
        self._creation_time_in_exported_file_name = value

    @property
    def maximum_file_or_directory_name_length(self):
        return self._maximum_file_or_directory_name_length

    @maximum_file_or_directory_name_length.setter
    def maximum_file_or_directory_name_length(self, value: int):
        value = min(int(value), yanom_globals.path_part_max_length)
        self._maximum_file_or_directory_name_length = value
