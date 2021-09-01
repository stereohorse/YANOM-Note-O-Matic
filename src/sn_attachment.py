from abc import ABC, abstractmethod
import logging
from pathlib import Path

import config
import helper_functions
import file_writer
import zip_file_reader


def what_module_is_this():
    return __name__


class NSAttachment(ABC):
    def __init__(self, note, attachment_id):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._attachment_id = attachment_id
        self._nsx_file = note.nsx_file
        self._json = note.note_json
        self._notebook_folder_name = note.notebook_folder_name
        self._conversion_settings = note.conversion_settings
        self._note_title = note.title
        self._parent_notebook = note.parent_notebook
        self._file_name = None
        self._path_relative_to_notebook = None
        self._full_path = None
        self._filename_inside_nsx = ''
        self._html_link = ''
        self._attachment_folder_name = self._conversion_settings.attachment_folder_name

    @abstractmethod
    def create_html_link(self):  # pragma: no cover
        pass

    @abstractmethod
    def create_file_name(self):  # pragma: no cover
        pass

    def process_attachment(self):
        self.create_file_name()
        self.generate_relative_path_to_notebook()
        self.generate_absolute_path()
        self.store_file()
        self.create_html_link()

    @abstractmethod
    def get_content_to_save(self):  # pragma: no cover
        pass

    def generate_relative_path_to_notebook(self):
        self._path_relative_to_notebook = Path(self._conversion_settings.attachment_folder_name, self._file_name)

    def generate_absolute_path(self):
        self._full_path = Path(self._conversion_settings.working_directory, config.yanom_globals.data_dir,
                               self._conversion_settings.export_folder,
                               self._notebook_folder_name,
                               self._path_relative_to_notebook)

    def is_duplicate_file(self):
        """Compare md5 and file name to see if current attachment is a duplicate of an existing attachment"""
        return (self._json['attachment'][self._attachment_id]['md5']
                in self._parent_notebook.attachment_md5_file_name_dict
                and self._json['attachment'][self._attachment_id]['name']
                == self._parent_notebook.attachment_md5_file_name_dict[
                    self._json['attachment'][self._attachment_id]['md5']])

    @abstractmethod
    def store_file(self):  # pragma: no cover
        pass

    @property
    def notebook_folder_name(self):
        return self._notebook_folder_name

    @property
    def file_name(self):
        return self._file_name

    @property
    def path_relative_to_notebook(self):
        return self._path_relative_to_notebook

    @property
    def full_path(self):
        return self._full_path

    @property
    def filename_inside_nsx(self):
        return self._filename_inside_nsx

    @property
    def html_link(self):
        return self._html_link

    @html_link.setter
    def html_link(self, value):
        self._html_link = value


class FileNSAttachment(NSAttachment):
    def __init__(self, note, attachment_id):
        super().__init__(note, attachment_id)
        self._name = self._json['attachment'][attachment_id]['name']
        self._filename_inside_nsx = f"file_{self._json['attachment'][attachment_id]['md5']}"
        self.logger.debug(f'Attachment name is "{self._name}"')
        self.logger.debug(f'Attachment md5 is "{self._filename_inside_nsx}"')

    def create_html_link(self):
        self._html_link = f'<a href="{helper_functions.path_to_uri(self._path_relative_to_notebook)}">{self.file_name}</a>'

    def create_file_name(self):
        self._file_name = Path(helper_functions.generate_clean_filename(self._name,
                                                                        self._conversion_settings.filename_options))
        if not Path(self._name).suffix:
            self.logger.warning(f'Original attachment name  "{self._name}" has no file extension')
            self.add_suffix_if_possible()

        if not self._name == str(self._file_name):
            self.logger.info(
                f'Original attachment name was "{self._name}" the cleaned name used is "{self._file_name}"')

    def add_suffix_if_possible(self):
        suffix = helper_functions.file_extension_from_bytes(
            zip_file_reader.read_binary_file(self._nsx_file.nsx_file_name, self.filename_inside_nsx, self._note_title))
        if suffix:
            self._file_name = self._file_name.with_suffix(suffix)

            self.logger.warning(f'From reading file header the extension "{suffix}" '
                                f'has been added to file name "{self._file_name}.  '
                                f'NSX json data reports file type '
                                f'of "{self._json["attachment"][self._attachment_id]["type"]}".')
        else:
            self.logger.warning(f'Unable to match file content to a file type. '
                                f'NSX json data reports file type '
                                f'of "{self._json["attachment"][self._attachment_id]["type"]}".')

    def get_content_to_save(self):
        return self._nsx_file.fetch_attachment_file(self.filename_inside_nsx, self._note_title)

    def change_file_name_if_already_exists(self):
        new_full_path = Path(self._full_path)
        while new_full_path.is_file():
            new_full_path = helper_functions.add_random_string_to_file_name(self._full_path, 4)

        self._full_path = new_full_path
        self._file_name = self._full_path.name
        self.generate_relative_path_to_notebook()

    def store_file(self):
        if not self.is_duplicate_file():  # skip exact duplicates
            self.change_file_name_if_already_exists()
            file_writer.store_file(self._full_path, self.get_content_to_save())
            md5 = self._json['attachment'][self._attachment_id]['md5']
            name = self._json['attachment'][self._attachment_id]['name']
            self._parent_notebook.attachment_md5_file_name_dict[md5] = name


class ImageNSAttachment(FileNSAttachment):

    def __init__(self, note, attachment_id):
        super().__init__(note, attachment_id)
        self._image_ref = self._json['attachment'][attachment_id]['ref']
        self.logger.debug(f'Image reference is "{self._image_ref}"')

    @property
    def image_ref(self):
        return self._image_ref

    def create_html_link(self):
        self._html_link = f'<img src="{helper_functions.path_to_uri(Path(self._file_name))}" >'

    def create_file_name(self):
        self._name = self._name.replace('ns_attach_image_', '')
        self._file_name = Path(helper_functions.generate_clean_filename(self._name,
                                                                        self._conversion_settings.filename_options))

        if not Path(self._name).suffix:
            self.logger.warning(f'Original attachment name  "{self._name}" has no file extension')
            self.add_suffix_if_possible()

        if self._name != str(self._file_name):
            self.logger.info(
                f'Original attachment name was "{self._name}" the cleaned name used is "{self._file_name}"')


class ChartNSAttachment(NSAttachment):

    def __init__(self, note, attachment_id, chart_file_like_object):
        super().__init__(note, attachment_id)
        self._chart_file_like_object = chart_file_like_object
        self._file_name = attachment_id

    def get_content_to_save(self):
        return self.chart_file_like_object

    @abstractmethod
    def create_html_link(self):  # pragma: no cover
        pass

    def create_file_name(self):
        self._file_name = Path(helper_functions.generate_clean_filename(self._attachment_id,
                                                                        self._conversion_settings.filename_options))

    @property
    def chart_file_like_object(self):
        return self._chart_file_like_object

    def store_file(self):
        file_writer.store_file(self._full_path, self.get_content_to_save())


class ChartImageNSAttachment(ChartNSAttachment):
    def create_html_link(self):
        self.html_link = f'<img src="{helper_functions.path_to_uri(self.path_relative_to_notebook)}">'


class ChartStringNSAttachment(ChartNSAttachment):
    def create_html_link(self):
        self.html_link = f'<a href="{helper_functions.path_to_uri(self.path_relative_to_notebook)}">Chart data file</a>'
