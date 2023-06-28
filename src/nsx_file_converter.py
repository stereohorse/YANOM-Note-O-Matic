from collections import namedtuple
import logging
from pathlib import Path
import sys

from alive_progress import alive_bar

import config
import file_writer
import helper_functions
from nsx_inter_note_link_processor import NSXInterNoteLinkProcessor
from sn_notebook import Notebook
from sn_note_page import NotePage
import zip_file_reader


def what_module_is_this():
    return __name__


Note = namedtuple("Note", "title, note")
Attachment = namedtuple('Attachment', 'attachment, note_title')


class NSXFile:

    def __init__(self, file, conversion_settings, pandoc_converter):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._conversion_settings = conversion_settings
        self._nsx_file_name = file
        self._nsx_json_data = {}
        self._notebook_ids = None
        self._note_page_ids = None
        self._notebooks = {}
        self._note_pages = {}
        self._all_note_pages = {}
        self._note_page_count = 0
        self._note_book_count = 0
        self._image_count = 0
        self._attachment_count = 0
        self._pandoc_converter = pandoc_converter
        self._inter_note_link_processor = NSXInterNoteLinkProcessor()
        self._null_attachments = {}
        self._encrypted_notes = []
        self._exported_notes = []

    def process_nsx_file(self):
        self.logger.info(f"Processing {self._nsx_file_name}")
        self._nsx_json_data = self.fetch_json_data('config.json')
        if not self._nsx_json_data:
            self.logger.warning(f"No config.json found in nsx file '{self._nsx_file_name}'. Skipping nsx file")
            return

        self.get_notebook_ids()
        if not self._notebook_ids:
            self.logger.warning(f"No notebook ids found in nsx file '{self._nsx_file_name}'. Skipping nsx file")
            return

        self.get_note_page_ids()
        if not self._note_page_ids:
            self.logger.warning(f"No note page ids found in nsx file '{self._nsx_file_name}'. Skipping nsx file")
            return

        self.add_notebooks()
        self.add_recycle_bin_notebook()
        self.create_export_folder_if_not_exist()
        notebooks_to_skip = self.create_notebook_and_attachment_folders()
        self.remove_notebooks_to_be_skipped(notebooks_to_skip)
        self.add_note_pages()
        self.add_note_pages_to_notebooks()
        self.generate_note_page_filename_and_path()
        self.build_dictionary_of_inter_note_links()
        self.process_notebooks()
        self.save_note_pages()
        self.logger.info(f"Processing of {self._nsx_file_name} complete.")

    def get_notebook_ids(self):
        self._notebook_ids = self._nsx_json_data.get('notebook', None)
        if not self._notebook_ids:
            msg = f"No notebook ID's were found in {self._nsx_file_name}. nsx file can not be processed"
            self.report_json_missing_ids(msg)

    def get_note_page_ids(self):
        self._note_page_ids = self._nsx_json_data.get('note', None)
        if not self._note_page_ids:
            msg = f"No note page ID's were found in {self._nsx_file_name}. nsx file can not be processed"
            self.report_json_missing_ids(msg)

    def report_json_missing_ids(self, msg):
        self.logger.warning(msg)
        if not config.yanom_globals.is_silent:
            print(msg)

    def build_dictionary_of_inter_note_links(self):
        all_note_pages = list(self._note_pages.values())
        self.inter_note_link_processor.make_list_of_links(all_note_pages)
        self.inter_note_link_processor.match_link_title_to_notes(all_note_pages)
        self.inter_note_link_processor.match_renamed_links_using_link_ref_id()

    def generate_note_page_filename_and_path(self):
        used_filenames = set()  # used_filenames is used to ensure no duplicate file names are generated
        for note_page in self.note_pages.values():
            # this has to happen before processing as the file name and path are needed for pre_processing content
            # and all notes have to have these set before any of them are processed to allow links between notes
            # to be created
            new_filename = note_page.generate_filenames_and_paths(used_filenames)
            used_filenames.add(new_filename)

    def fetch_json_data(self, data_id):
        self.logger.info(f"Fetching json data file {data_id} from {self._nsx_file_name}")
        return zip_file_reader.read_json_data(self._nsx_file_name, Path(data_id))

    def fetch_attachment_file(self, file_name, note_title):
        self.logger.info(f"Fetching binary attachment data from {self._nsx_file_name}")
        read_result = zip_file_reader.read_binary_file(self._nsx_file_name, Path(file_name), note_title)
        return None if not read_result else read_result[0]

    def add_notebooks(self):
        self.logger.info(f"Creating Notebooks")
        self._notebooks = {notebook_id: Notebook(self, notebook_id) for notebook_id in self._notebook_ids}

    def add_recycle_bin_notebook(self):
        self.logger.debug("Creating recycle bin notebook")
        self._notebooks['recycle-bin'] = Notebook(self, 'recycle-bin')
        self._notebooks['recycle-bin'].title = 'recycle-bin'  # set title as init will set to unknown notebook

    def create_export_folder_if_not_exist(self, parents=True):
        self.logger.debug("Creating export folder if it does not exist")

        target_path = Path(self.conversion_settings.working_directory, config.yanom_globals.data_dir,
                           self._conversion_settings.export_folder)

        try:
            target_path.mkdir(parents=parents, exist_ok=False)
        except FileExistsError as e:
            if not target_path.is_file():
                self.logger.debug(f"Export folder already exists - '{target_path}'")
            else:
                msg = f'Unable to create the export folder because path is to an existing file not a directory.\n{e}'
                self._report_create_export_folder_errors(msg, e)
                sys.exit(1)
        except FileNotFoundError as e:
            msg = f'Unable to create the export folder there is a problem with the path.\n{e}'
            if helper_functions.are_windows_long_paths_disabled():
                msg = f"{msg}\n Windows long path names are not enabled check path length"
            self._report_create_export_folder_errors(msg, e)
            sys.exit(1)
        except OSError as e:
            msg = f'Unable to create the export folder\n{e}'
            self._report_create_export_folder_errors(msg, e)
            sys.exit(1)

    def _report_create_export_folder_errors(self, msg, e):
        self.logger.error(f'{msg}')
        self.logger.error(helper_functions.log_traceback(e))
        if not config.yanom_globals.is_silent:
            print(f'{msg}')

    def create_notebook_and_attachment_folders(self) -> list:
        """Create notebook folders and return list of notebook ids for those where a notebook folder was  not created"""
        self.logger.debug(f"Creating folders for notebooks")
        notebooks_to_skip = []
        for notebooks_id in self._notebooks:
            self._notebooks[notebooks_id].create_notebook_folder()
            if not self._notebooks[notebooks_id].full_path_to_notebook:
                notebooks_to_skip.append(notebooks_id)
                continue

            self._notebooks[notebooks_id].create_attachment_folder()

        return notebooks_to_skip

    def remove_notebooks_to_be_skipped(self, notebooks_to_skip):
        for notebook_id in notebooks_to_skip:
            self.logger.warning(f"The notebook `{self._notebooks[notebook_id].title} is being skipped'")
            del self._notebooks[notebook_id]

    def add_note_pages(self):
        self.logger.debug(f"Creating note page objects")

        if not config.yanom_globals.is_silent:
            print(f"Finding note pages in {self._nsx_file_name.name}")
            with alive_bar(len(self._note_page_ids), bar='blocks') as bar:
                for note_id in self._note_page_ids:
                    self._add_note(note_id, bar)
                self._note_page_count += len(self._note_pages)

                self._warn_if_note_pages_missing()
            return

        for note_id in self._note_page_ids:
            self._add_note(note_id)

        self._note_page_count += len(self._note_pages)

        self._warn_if_note_pages_missing()

    def _add_note(self, note_id, bar=None):
        note_data = self.fetch_json_data(note_id)
        if not note_data:
            self.logger.warning(f"Unable to locate note data for note id '{note_id}' "
                                f"from nsx file'{self._nsx_file_name.name}'. No note data to process ")
            if bar:
                bar()
            return

        if self.is_note_encrypted(note_data):
            self._encrypted_notes.append(note_data['title'])
            if bar:
                bar()
            return

        note_page = NotePage(self, note_id, note_data)
        self._note_pages[note_id] = note_page
        if bar:
            bar()

    def _warn_if_note_pages_missing(self):
        if len(self._note_pages) < len(self._note_page_ids):
            msg = f"There are {len(self._note_page_ids) - len(self._note_pages)} less note pages to process " \
                  f"than note page id's in the nsx file.\nPlease review log file as there may be issues " \
                  f"with the nsx file."
            self.logger.warning(msg)
            if not config.yanom_globals.is_silent:
                print(msg)

    def is_note_encrypted(self, note_data):
        if 'encrypt' not in note_data:
            self.logger.warning(f"The Note - '{note_data['title']}' - has no encryption flag, it may or may not "
                                f"be encrypted. Assuming it is not.")
            return False

        if note_data['encrypt']:
            self.logger.warning(f"The Note - '{note_data['title']}' - is encrypted and has not been converted.")

        return note_data['encrypt']

    def add_note_pages_to_notebooks(self):
        self.logger.info("Add note pages to notebooks")

        for note_page_id in self._note_pages:
            current_parent_id = self._note_pages[note_page_id].parent_notebook_id
            if current_parent_id in self._notebooks:
                self._notebooks[current_parent_id].pair_up_note_pages_and_notebooks(self._note_pages[note_page_id])
            else:
                self._notebooks['recycle-bin'].pair_up_note_pages_and_notebooks(self._note_pages[note_page_id])

    def process_notebooks(self):
        self._note_book_count += len(self._notebooks)

        for notebooks_id in self._notebooks:
            self._notebooks[notebooks_id].process_notebook_pages()
            self._image_count += self._notebooks[notebooks_id].num_image_attachments
            self._attachment_count += self._notebooks[notebooks_id].num_file_attachments

            if self._notebooks[notebooks_id].null_attachment_list:
                self._null_attachments[self._notebooks[notebooks_id].title] \
                    = self._null_attachments.get(self._notebooks[notebooks_id].title, []) \
                      + self._notebooks[notebooks_id].null_attachment_list

    def save_note_pages(self):
        if not config.yanom_globals.is_silent:
            print("Saving note pages")
            with alive_bar(len(self._note_pages), bar='blocks') as bar:
                for note_page_id in self._note_pages:
                    self._store_file(self._note_pages[note_page_id], bar)
            return

        for note_page_id in self._note_pages:
            self._store_file(self._note_pages[note_page_id])

    @staticmethod
    def _store_file(note_page, bar=None):
        file_writer.store_file(note_page.full_path,
                               note_page.converted_content)

        if bar:
            bar()

    @property
    def notebooks(self):
        return self._notebooks

    @property
    def conversion_settings(self):
        return self._conversion_settings

    @property
    def pandoc_converter(self):
        return self._pandoc_converter

    @property
    def note_page_count(self):
        return self._note_page_count

    @property
    def note_book_count(self):
        return self._note_book_count

    @property
    def image_count(self):
        return self._image_count

    @property
    def attachment_count(self):
        return self._attachment_count

    @property
    def note_pages(self):
        return self._note_pages

    @property
    def inter_note_link_processor(self):
        return self._inter_note_link_processor

    @property
    def null_attachments(self):
        return self._null_attachments

    @property
    def encrypted_notes(self):
        return self._encrypted_notes

    @property
    def nsx_file_name(self):
        return self._nsx_file_name

    @property
    def exported_notes(self):
        return self._exported_notes
