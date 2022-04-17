from configparser import ConfigParser
import logging
from pathlib import Path
import sys

import config
import helper_functions
from interactive_cli import InvalidConfigFileCommandLineInterface
from conversion_settings import ConversionSettings


def what_module_is_this():
    return __name__


class ConfigData(ConfigParser):
    """
    Read, verify, update and write config.ini files

    Attributes
    ----------
    logger : logging object
        used for program logging
    config_file : str
        name of the configuration file to be parsed and to use for storing config data
    default_quick_setting :  str
        setting to be used if the config.ini is found to be invalid and uses chooses to use the default
    conversion_settings :  Child of ConversionSettings, holds config data in a format to be used outside of the class
    validation_values :  dict
        holds the values required to validate a config file read from disk

    """

    def __init__(self, config_file, default_quick_setting, **kwargs):
        super().__init__(**kwargs)
        # Note: allow_no_value=True  allows for #comments in the ini file
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._config_file = config_file
        self._default_quick_setting = default_quick_setting
        self._conversion_settings = ConversionSettings()
        self._conversion_settings.set_quick_setting('manual')
        self._validation_values = self._conversion_settings.validation_values

    def parse_config_file(self):
        self.read_config_file()
        valid_config = self.validate_config_file()
        if not valid_config:
            self.ask_user_to_choose_new_default_config_file()
        self.generate_conversion_settings_from_parsed_config_file_data()
        self.logger.info(f"Settings from config.ini are {self._conversion_settings}")

    def generate_conversion_settings_using_quick_settings_string(self, value):
        if value in self._conversion_settings.valid_quick_settings:
            self._conversion_settings.set_quick_setting(value)
            self._load_and_save_settings()
            return

        self.logger.error(f"Passed invalid value - {value} - is not a recognised quick setting string")
        raise ValueError(f"Conversion setting parameter must be a valid quick setting string "
                         f"{self._conversion_settings.valid_quick_settings} received '{value}'")

    def generate_conversion_settings_using_quick_settings_object(self, value):
        if isinstance(value, ConversionSettings):
            self._conversion_settings = value
            self._load_and_save_settings()
            return

        self.logger.error(f"Passed invalid value - {value}")
        raise TypeError(f"Conversion setting parameter must be a valid quick setting "
                        f"{self._conversion_settings.valid_quick_settings} string or a ConversionSettings object")

    def validate_config_file(self) -> bool:
        """
        Validate config data read from config.ini.  Errors in the data will trigger a prompt user
        asking to create a new default configuration or exit the program.

        """
        self.logger.debug("attempting to validate config file")

        try:
            self._validate_config()
            self.logger.debug("config file validated")
            return True

        except ValueError as e:
            self.logger.warning(f"Config file invalid \n{e}")
            return False

    def ask_user_to_choose_new_default_config_file(self):
        ask_what_to_do = InvalidConfigFileCommandLineInterface()
        what_to_do = ask_what_to_do.run_cli()
        if what_to_do == 'exit':
            sys.exit(0)
        self.logger.info("User chose to create a default file")
        self._conversion_settings.set_quick_setting(self._default_quick_setting)
        self._load_and_save_settings()

    def _validate_config(self):
        """
        Validate the current Config Data for any errors by comparing to a set of validation values.

        Errors will raise a ValueError

        """
        for section, keys in self._validation_values.items():
            if section not in self:
                raise ValueError(f'Missing section {section} in the config ini file')

            for key, values in keys.items():
                if key not in self[section]:
                    raise ValueError(f'Missing entry for {key} under section {section} in the config ini file')

                if values:
                    if self[section][key] not in values:
                        raise ValueError(f'Invalid value of "{self[section][key]}" for {key} under section {section} '
                                         f'in the config file')

    def generate_conversion_settings_from_parsed_config_file_data(self):
        """
        Transcribe the values in a ConversionSettings object into the ConfigParser format used by this class

        """
        self._conversion_settings.conversion_input = self['conversion_inputs']['conversion_input']
        self._conversion_settings.markdown_conversion_input = \
            self['markdown_conversion_inputs']['markdown_conversion_input']
        self._conversion_settings.quick_setting = self['quick_settings']['quick_setting']
        self._conversion_settings.export_format = self['export_formats']['export_format']
        self._conversion_settings.front_matter_format = self['meta_data_options']['front_matter_format']
        if self._conversion_settings.export_format == 'pandoc_markdown':
            self._conversion_settings.front_matter_format = 'yaml'
        self._conversion_settings.metadata_schema = self['meta_data_options']['metadata_schema']
        self._conversion_settings.tag_prefix = self['meta_data_options']['tag_prefix']
        self._conversion_settings.spaces_in_tags = self.getboolean('meta_data_options', 'spaces_in_tags')
        self._conversion_settings.split_tags = self.getboolean('meta_data_options', 'split_tags')
        self._conversion_settings.tag_prefix = self['meta_data_options']['tag_prefix']
        if self['meta_data_options']['metadata_time_format'] != '':
            self._conversion_settings.metadata_time_format = self['meta_data_options']['metadata_time_format']
        if self['meta_data_options']['file_created_text'] != '':
            self._conversion_settings.file_created_text = self['meta_data_options']['file_created_text']
        if self['meta_data_options']['file_modified_text'] != '':
            self._conversion_settings.file_modified_text = self['meta_data_options']['file_modified_text']
        self._conversion_settings.first_row_as_header = self.getboolean('table_options', 'first_row_as_header')
        self._conversion_settings.first_column_as_header = self.getboolean('table_options', 'first_column_as_header')
        self._conversion_settings.chart_image = self.getboolean('chart_options', 'chart_image')
        self._conversion_settings.chart_csv = self.getboolean('chart_options', 'chart_csv')
        self._conversion_settings.chart_data_table = self.getboolean('chart_options', 'chart_data_table')
        self._conversion_settings.source = self['file_options']['source']
        if self['file_options']['export_folder'] == '':
            self['file_options']['export_folder'] = 'notes'
        self._conversion_settings.export_folder = self['file_options']['export_folder']
        if self['file_options']['attachment_folder_name'] == '':
            self['file_options']['attachment_folder_name'] = 'attachments'
        self._conversion_settings.attachment_folder_name = self['file_options']['attachment_folder_name']
        self._conversion_settings._creation_time_in_exported_file_name = \
            self.getboolean('file_options', 'creation_time_in_exported_file_name')
        self._conversion_settings.allow_spaces_in_filenames = \
            self.getboolean('file_options', 'allow_spaces_in_filenames')
        self._conversion_settings.allow_unicode_in_filenames = \
            self.getboolean('file_options', 'allow_unicode_in_filenames')
        self._conversion_settings.allow_uppercase_in_filenames = \
            self.getboolean('file_options', 'allow_uppercase_in_filenames')
        self._conversion_settings.allow_non_alphanumeric_in_filenames = \
            self.getboolean('file_options', 'allow_non_alphanumeric_in_filenames')
        self._conversion_settings.filename_spaces_replaced_by = self['file_options']['filename_spaces_replaced_by']
        self._conversion_settings.max_file_or_directory_name_length = self['file_options']['max_file_or_directory_name_length']
        self._conversion_settings.orphans = self['file_options']['orphans']
        self._conversion_settings.make_absolute = self.getboolean('file_options', 'make_absolute')
        self._conversion_settings.embed_these_document_types = self['nimbus_options']['embed_these_document_types']
        self._conversion_settings.embed_these_image_types = self['nimbus_options']['embed_these_image_types']
        self._conversion_settings.embed_these_audio_types = self['nimbus_options']['embed_these_audio_types']
        self._conversion_settings.embed_these_video_types = self['nimbus_options']['embed_these_video_types']
        self._conversion_settings.keep_nimbus_row_and_column_headers = \
            self.getboolean('nimbus_options', 'keep_nimbus_row_and_column_headers')
        self._conversion_settings.unrecognised_tag_format = self['nimbus_options']['unrecognised_tag_format']

    def _write_config_file(self):
        ini_path = Path(self.conversion_settings.working_directory, 'data', self._config_file)
        try:
            with open(ini_path, 'w') as config_file:
                self.write(config_file)
                self.logger.info("Saving configuration file")
        except FileNotFoundError as e:
            if not Path(ini_path.parent).is_dir():
                message = f"Unable to save config.ini file '{ini_path.parent}' " \
                          f"is not a directory. {e.strerror}"
                self.logger.error(message)
                self.logger.error(helper_functions.log_traceback(e))
                if not config.yanom_globals.is_silent:
                    print(message)
            else:
                message = f"Unable to save config.ini file " \
                          f"- '{ini_path}' " \
                          f"- {e.strerror}"
                self.logger.error(message)
                self.logger.error(helper_functions.log_traceback(e))
                if not config.yanom_globals.is_silent:
                    print(message)
        except IOError as e:
            message = f"Unable to save config.ini file `{ini_path.parent}`.\n{e}"
            self.logger.error(message)
            self.logger.error(helper_functions.log_traceback(e))
            if not config.yanom_globals.is_silent:
                print(message)

    def read_config_file(self):
        """
        Read config file. If file is missing generate a new one using default quick setting.

        If config file is missing set the conversion_settings to the default quick setting values
        and use that to generate a config data set.

        """
        self.logger.debug('reading config file')
        path = Path(self.conversion_settings.working_directory, 'data', self._config_file)

        if path.is_file():
            self.read(path)
            self.logger.info(f'Data read from INI file is {self.__repr__()}')
        else:
            self.logger.warning(f'config.ini missing at {path}, generating new file and settings set to default.')
            if not config.yanom_globals.is_silent:
                print("config.ini missing, generating new file.")
            self.conversion_settings = self._default_quick_setting

    def _load_and_save_settings(self):
        """
        Read a dictionary of config data, formatted for config file generation and store the new config file.

        """
        self._wipe_current_config()
        self.read_dict(self._generate_conversion_dict())
        self.logger.info(f"Quick setting {self['quick_settings']['quick_setting']} loaded")
        self._write_config_file()

    def _wipe_current_config(self):
        """
        Wipe the current config sections.

        When using read_dict new sections are added to the end of the current config. so when written to file they
        are out of place compared to the validation data.  This method is here to save having to manually delete the
        ini file when coding changes to the conversion dict.  That means it is here to save me having to remember to
        delete the ini file :-)
        """
        for section, keys in self._validation_values.items():
            self.remove_section(section)
        pass

    def _generate_conversion_dict(self):
        """
        Generate a dictionary of the current conversion settings.

        Returns
        -------
        Dict
            Dictionary, formatted for config file creation, using values from a ConversionSettings object

        """
        # comments are treated as 'values' with no value (value is set to None) i.e. they are dict entries
        # where the key is the #comment string and the value is None
        return {
            'conversion_inputs': {
                f'    # Valid entries are {", ".join(self._conversion_settings.valid_conversion_inputs)}': None,
                '    #  nsx = synology Note Station Export file': None,
                '    #  html = simple html based notes pages, no complex CSS or javascript': None,
                '    #  markdown =  text files in markdown format': None,
                'conversion_input': self._conversion_settings.conversion_input
            },
            'markdown_conversion_inputs': {
                f'    # Valid entries are {", ".join(self._conversion_settings.valid_markdown_conversion_inputs)}': None,
                'markdown_conversion_input': self._conversion_settings.markdown_conversion_input
            },
            'quick_settings': {
                f'    # Valid entries are {", ".join(self._conversion_settings.valid_export_formats)}': None,
                '    # use manual to use the manual settings in the sections below': None,
                '    # NOTE if an option other than - manual - is used the rest of the ': None,
                '    # settings in this file will be set automatically': None,
                '    #': None,
                "quick_setting": self._conversion_settings.quick_setting,
                '    # ': None,
                '    # The following sections only apply if the above is set to manual': None,
                '    #  ': None
            },
            'export_formats': {
                f'    # Valid entries are {", ".join(self._conversion_settings.valid_export_formats)}': None,
                "export_format": self._conversion_settings.export_format
            },
            'meta_data_options': {
                '    # Note: front_matter_format sets the presence and type of the section with metadata ': None,
                '    # retrieved from the source': None,
                f'    # Valid entries are {", ".join(self._conversion_settings.valid_front_matter_formats)}': None,
                '    # no entry will result in no front matter section': None,
                'front_matter_format': self._conversion_settings.front_matter_format,
                '    # metadata schema is a comma separated list of metadata keys that you wish to ': None,
                '    # restrict the retrieved metadata keys. for example ': None,
                '    # title, tags    will return those two if they are found': None,
                '    # If left blank any meta data found will be used': None,
                '    # The useful available keys in an nsx file are title, ctime, mtime, tag': None,
                'metadata_schema': ",".join(self._conversion_settings.metadata_schema),
                '    # tag prefix is a character you wish to be added to the front of any tag values ': None,
                '    # retrieved from metadata.  NOTE Use this if using front matter format "text" ': None,
                '    # or use is your markdown system uses a prefix in a front matter section (most wil not use a prefix) ': None,
                'tag_prefix': self._conversion_settings.tag_prefix,
                '    # spaces_in_tags if True will maintain spaces in tag words, if False spaces are replaced by a dash -': None,
                'spaces_in_tags': self._conversion_settings.spaces_in_tags,
                '    # split tags will split grouped tags into individual tags if True': None,
                '    # "Tag1", "Tag1/Sub Tag2"  will become "Tag1", "Sub Tag2"': None,
                '    # grouped tags are only split where a "/" character is found': None,
                'split_tags': self._conversion_settings.split_tags,
                '    # Meta data time format USED FOR NSX ONLY - enter a valid strftime date and time format with ': None,
                '    # additional % signs to escape the first % sign': None,
                '    # 3 examples are %%Y-%%m-%%d %%H:%%M:%%S%%Z    %%Y-%%m-%%d %%H:%%M:%%S   %%Y%%m%%d%%H%%M': None,
                '    # for formats see https://strftime.org/': None,
                '    # If left blank will default to %%Y-%%m-%%d %%H:%%M:%%S%%Z': None,
                'metadata_time_format': self._conversion_settings.metadata_time_format.replace('%', '%%'),
                # have to escape % signs for configparser as single % tells it to treat as string formatting
                # is written to file as %% and when read config parser will strip the extra % so what is used is correct
                '    # Replacement names for nsx creation time (ctime) and modified date (mtime) ': None,
                '    # If left blank will default to created and updated': None,
                'file_created_text': self._conversion_settings.file_created_text,
                'file_modified_text': self._conversion_settings.file_modified_text,
            },
            'table_options': {
                '  #  These two table options apply to NSX files ONLY': None,
                'first_row_as_header': self._conversion_settings.first_row_as_header,
                'first_column_as_header': self._conversion_settings.first_column_as_header
            },
            'chart_options': {
                '  #  These three chart options apply to NSX files ONLY': None,
                'chart_image': self._conversion_settings.chart_image,
                'chart_csv': self._conversion_settings.chart_csv,
                'chart_data_table': self._conversion_settings.chart_data_table
            },
            'file_options': {
                'source': self._conversion_settings.source,
                'export_folder': self._conversion_settings.export_folder,
                'attachment_folder_name': self._conversion_settings.attachment_folder_name,
                '    # The following options apply to directory names, and currently only apply filenames in NSX conversions.': None,
                'allow_spaces_in_filenames': self._conversion_settings.allow_spaces_in_filenames,
                'filename_spaces_replaced_by': self._conversion_settings.filename_spaces_replaced_by,
                'allow_unicode_in_filenames': self._conversion_settings.allow_unicode_in_filenames,
                'allow_uppercase_in_filenames': self._conversion_settings.allow_uppercase_in_filenames,
                'allow_non_alphanumeric_in_filenames': self._conversion_settings.allow_non_alphanumeric_in_filenames,
                'creation_time_in_exported_file_name': self._conversion_settings.allow_uppercase_in_filenames,
                '    # If True creation time as `yyyymmddhhmm-` will be added as prefix to file name': None,
                'max_file_or_directory_name_length': self._conversion_settings.max_file_or_directory_name_length,
                '    # The following options apply to directory names, and currently only apply to html and markdown conversions.': None,
                'orphans': self._conversion_settings.orphans,
                '    # orphans are files that are not linked to any notes.  Valid Values are': None,
                '    # ignore - orphan files are left where they are and are not moved to an export folder.': None,
                '    # copy - orphan files are coppied to the export folder in the same relative locations as the source.': None,
                '    # orphan - orphan files are moved to a directory named orphan in the export folder.': None,
                'make_absolute': self._conversion_settings.make_absolute,
                '    # Links to files that are not in the path forwards of the source directory will be ': None,
                '    # changed to absolute links if set to True.  For example "../../someplace/some_file.pdf"': None,
                '    # becomes /root/path/to/someplace/some_file.pdf"': None,
                '    # False will leave these links unchanged as relative links': None,
            },
            'nimbus_options': {
                '    # The following options apply to nimbus notes conversions': None,
                'embed_these_document_types': ",".join(self._conversion_settings.embed_these_document_types),
                'embed_these_image_types': ",".join(self._conversion_settings.embed_these_image_types),
                'embed_these_audio_types': ",".join(self._conversion_settings.embed_these_audio_types),
                'embed_these_video_types': ",".join(self._conversion_settings.embed_these_video_types),
                'keep_nimbus_row_and_column_headers': self._conversion_settings.keep_nimbus_row_and_column_headers,
                '    # For unrecognised html tags use either html or plain text': None,
                '    # html = inline html in markdown and html in html files': None,
                '    # text = extract any text and display as plain text in markdown and html': None,
                'unrecognised_tag_format': self._conversion_settings.unrecognised_tag_format,

            },
        }

    @property
    def conversion_settings(self):
        return self._conversion_settings

    @conversion_settings.setter
    def conversion_settings(self, value):
        """
        Receive a conversion setting as a quick setting string or a ConversionSettings object,
        set the _conversion_setting, generate and save config ini file for the setting received.

        Parameters
        ----------
        value : str or ConversionSettings
            If str must be a valid quick_setting string value.

        """
        if type(value) is str:
            self.generate_conversion_settings_using_quick_settings_string(value)
            return

        self.generate_conversion_settings_using_quick_settings_object(value)

    def __str__(self):
        display_dict = str({section: dict(self[section]) for section in self.sections()})
        return str(f'{self.__class__.__name__}{display_dict}')

    def __repr__(self):
        display_dict = str({section: dict(self[section]) for section in self.sections()})
        return str(f'{self.__class__.__name__}{display_dict}')
