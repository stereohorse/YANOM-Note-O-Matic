import logging
import time
from pathlib import Path

import config
from config import yanom_globals
import helper_functions
from nsx_post_processing import NoteStationPostProcessing
from nsx_pre_processing import NoteStationPreProcessing
import sn_attachment


def what_module_is_this():
    return __name__


class NotePage:
    def __init__(self, nsx_file, note_id, note_json):
        self.logger = logging.getLogger(f'{config.APP_NAME}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.logger_level)
        self._title = None
        self._raw_content = None
        self._attachments_json = None
        self._parent_notebook_id = None
        self._nsx_file = nsx_file
        self._pandoc_converter = nsx_file.pandoc_converter
        self._conversion_settings = nsx_file.conversion_settings
        self._note_id = note_id
        self._note_json = note_json
        self.get_json_note_title()
        self._original_title = self._title
        self._format_ctime_and_mtime_if_required()
        self.get_json_note_content()
        self.get_json_parent_notebook()
        self.get_json_attachment_data()
        self._attachments = {}
        self._pre_processed_content = ''
        self._converted_content = ''
        self._notebook_folder_name = ''
        self._file_name = ''
        self._full_path = ''
        self._image_count = 0
        self._attachment_count = 0
        self._pre_processor = None
        self._post_processor = None

    def get_json_note_title(self):
        self._title = self._note_json.get('title', None)
        self.logger.debug(f"Note title from json is '{self._title}'")
        if not self.title:
            self._title = helper_functions.get_random_string(8)
            self.logger.info(f"no title was found in note id '{self._note_id}'.  "
                             f"Using random string for title '{self._title}'")

    def get_json_note_content(self):
        self._raw_content = self._note_json.get('content', None)
        if self._raw_content is None:
            self._raw_content = ''
            self.logger.info(f"No content was found in note id '{self._note_id}'.")

    def get_json_attachment_data(self):
        self._attachments_json = self._note_json.get('attachment', {})
        if self._attachments_json is None:
            self.logger.warning(
                f"Note - '{self._title}' - Has Null set for attachments. "
                f"There may be a sync issues between desktop and web version of Note Station.")
        if not self._attachments_json:
            self._attachments_json = {}
            self.logger.info(f"No attachments were found in note id '{self._note_id}'.")

    def get_json_parent_notebook(self):
        self._parent_notebook_id = self._note_json.get('parent_id', None)
        if not self._parent_notebook_id:
            self._parent_notebook_id = 'Parent Notebook ID missing from nsx file note data'
            self.logger.info(f"No parent notebook ID was found in note id '{self._note_id}'.  "
                             f"Using a placeholder id of '{self._parent_notebook_id}'.  "
                             f"Notes will be in the Recycle bin notebook")
            if not config.silent:
                print(f"No parent notebook ID was found in '{self._note_id}'.  Note will be in the Recycle Bin notebook")

    def _format_ctime_and_mtime_if_required(self):
        if self._conversion_settings.front_matter_format != 'none' \
                or self._conversion_settings.creation_time_in_exported_file_name is True:
            if 'ctime' in self._note_json:
                self._note_json['ctime'] = time.strftime('%Y%m%d%H%M', time.localtime(self._note_json['ctime']))
            if 'mtime' in self._note_json:
                self._note_json['mtime'] = time.strftime('%Y%m%d%H%M', time.localtime(self._note_json['mtime']))

    def process_note(self):
        self.logger.info(f"Processing note page '{self._title}' - {self._note_id}")
        self.create_attachments()
        self.process_attachments()
        self.pre_process_content()
        self.convert_data()
        if not self.conversion_settings.export_format == 'html':
            self.post_process_content()
        self.logger.debug(f"Processing of note page '{self._title}' - {self._note_id}  completed.")

    def _create_file_name(self, used_filenames):
        dirty_filename = self._append_file_extension()
        cleaned_filename = Path(helper_functions.generate_clean_filename(dirty_filename,
                                                                         yanom_globals.path_part_max_length,
                                                                         allow_unicode=True))

        new_filename = cleaned_filename
        n = 0
        while new_filename in used_filenames:
            n += 1
            new_filename = Path(f'{Path(cleaned_filename).stem}-{n}{Path(cleaned_filename).suffix}')

        self._file_name = new_filename
        self.logger.info(f'For the note "{self._title}" the file name used is "{self._file_name}"')

    def _append_file_extension(self):
        if self._conversion_settings.export_format == 'html':
            return f"{self._title}.html"

        return f"{self._title}.md"

    def _generate_absolute_path(self):
        path_to_file = Path(self._conversion_settings.working_directory, config.DATA_DIR,
                            self._conversion_settings.export_folder, self._notebook_folder_name, self._file_name)

        absolute_file_path = helper_functions.find_valid_full_file_path(path_to_file)

        return absolute_file_path

    def generate_filenames_and_paths(self, used_filenames):
        self._create_file_name(used_filenames)
        self._full_path = self._generate_absolute_path()
        return self._file_name

    def create_attachments(self):
        for attachment_id in self._attachments_json:
            if self._attachments_json[attachment_id]['type'].startswith('image'):
                self._attachments[attachment_id] = sn_attachment.ImageNSAttachment(self, attachment_id)
                self._image_count += 1
            else:
                self._attachments[attachment_id] = sn_attachment.FileNSAttachment(self, attachment_id)
                self._attachment_count += 1

        return self._image_count, self._attachment_count

    def process_attachments(self):
        self.logger.debug('Process attachments')
        for attachment_id in self._attachments:
            self._attachments[attachment_id].process_attachment()

    def pre_process_content(self):
        self._pre_processor = NoteStationPreProcessing(self)
        self._pre_processed_content = self._pre_processor.pre_processed_content

    def convert_data(self):
        if self.conversion_settings.export_format == 'html':
            self._converted_content = self._pre_processed_content
            return

        self.logger.debug(f"Converting content of '{self._title}' - {self._note_id}")
        self._converted_content = self._pandoc_converter.convert_using_strings(self._pre_processed_content, self._title)

    def post_process_content(self):
        self._post_processor = NoteStationPostProcessing(self)
        self._converted_content = self._post_processor.post_processed_content

    def increment_duplicated_title(self, list_of_existing_titles):
        """
        Add incrementing number to title for duplicates notes in a notebook.

        When a note title is found to already exist in a notebook add a number to the end of the title, incrementing
        if required when there are multiple duplicates
        """
        this_title = self._title
        n = 0

        while this_title in list_of_existing_titles:
            n += 1
            this_title = f'{self._title}-{n}'

        self._title = this_title

    @property
    def title(self):
        return self._title

    @property
    def original_title(self):
        return self._original_title

    @property
    def note_id(self):
        return self._note_id

    @property
    def notebook_folder_name(self):
        return self._notebook_folder_name

    @notebook_folder_name.setter
    def notebook_folder_name(self, valid_folder: Path):
        self._notebook_folder_name = valid_folder

    @property
    def file_name(self):
        return self._file_name

    @property
    def full_path(self):
        return self._full_path

    @property
    def converted_content(self):
        return self._converted_content

    @property
    def note_json(self):
        return self._note_json

    @property
    def pre_processed_content(self):
        return self._pre_processed_content

    @property
    def nsx_file(self):
        return self._nsx_file

    @property
    def raw_content(self):
        return self._raw_content

    @property
    def attachments(self):
        return self._attachments

    @property
    def image_count(self):
        return self._image_count

    @image_count.setter
    def image_count(self, value):
        self._image_count = value

    @property
    def attachment_count(self):
        return self._attachment_count

    @attachment_count.setter
    def attachment_count(self, value):
        self._attachment_count = value

    @property
    def conversion_settings(self):
        return self._conversion_settings

    @property
    def parent_notebook_id(self):
        return self._parent_notebook_id

    @parent_notebook_id.setter
    def parent_notebook_id(self, value):
        self._parent_notebook_id = value

    @property
    def pre_processor(self):
        return self._pre_processor
