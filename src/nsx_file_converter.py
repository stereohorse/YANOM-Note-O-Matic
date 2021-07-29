import sys
from collections import namedtuple
import logging
from pathlib import Path

from alive_progress import alive_bar

import config
import file_writer
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
        self.logger = logging.getLogger(f'{config.APP_NAME}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.logger_level)
        self._conversion_settings = conversion_settings
        self._nsx_file_name = file
        self._nsx_json_data = ''
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
        self._encrypted_notes = []

    def process_nsx_file(self):
        self.logger.info(f"Processing {self._nsx_file_name}")
        self._nsx_json_data = self.fetch_json_data('config.json')
        self._notebook_ids = self._nsx_json_data['notebook']
        self._note_page_ids = self._nsx_json_data['note']
        self.add_notebooks()
        self.add_recycle_bin_notebook()
        self.create_export_folder_if_not_exist()
        self.create_folders()
        self.add_note_pages()
        self.add_note_pages_to_notebooks()
        self.generate_note_page_filename_and_path()
        self.build_dictionary_of_inter_note_links()
        self.process_notebooks()
        attachments = self.build_list_of_attachments()
        self.store_attachments(attachments)
        self.save_note_pages()
        self.logger.info(f"Processing of {self._nsx_file_name} complete.")

    def build_list_of_attachments(self) -> list[Attachment]:
        """
        Generate and return a list of namedtuple of attachment details.

        Returns
        =======
        list[Attachment]
            list of Attachment named tuples that hold sn_attachment objects and the note title
            the attachment comes from.

        """

        return [Attachment(attachment, self._note_pages[note_page_id].title)
                for note_page_id in self._note_pages
                for attachment in self._note_pages[note_page_id].attachments.values()
                ]

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
        return zip_file_reader.read_json_data(self._nsx_file_name, data_id)

    def fetch_attachment_file(self, file_name):
        return zip_file_reader.read_binary_file(self._nsx_file_name, file_name)

    def add_notebooks(self):
        self.logger.info(f"Creating Notebooks")
        self._notebooks = {
            notebook_id: Notebook(self, notebook_id, self.fetch_notebook_title(notebook_id))
            for notebook_id in self._notebook_ids
        }

        self._note_book_count += len(self._notebooks)

    def fetch_notebook_title(self, notebook_id):
        notebook_title = zip_file_reader.read_json_data(self._nsx_file_name, notebook_id)['title']
        if notebook_title == "":  # The notebook with no title is called 'My Notes' in note station
            notebook_title = "My Notebook"

        return notebook_title

    def add_recycle_bin_notebook(self):
        self.logger.debug("Creating recycle bin notebook")
        self._notebooks['recycle-bin'] = Notebook(self, 'recycle-bin', 'recycle-bin')

    def create_export_folder_if_not_exist(self, parents=True):
        self.logger.debug("Creating export folder if it does not exist")

        target_path = Path(self.conversion_settings.working_directory, config.DATA_DIR,
                           self._conversion_settings.export_folder)

        try:
            target_path.mkdir(parents=parents, exist_ok=False)
        except FileExistsError as e:
            if not target_path.is_file():
                self.logger.debug(f"Export folder already exists - '{target_path}'")
            else:
                msg = f'Unable to create the export folder because path is to an existing file not a directory.\n{e}'
                self.logger.error(f'{msg}')
                if not config.silent:
                    print(f'{msg}')
                sys.exit(1)
        except FileNotFoundError as e:
            msg = f'Unable to create the export folder there is a problem with the path.\n{e}'
            self.logger.error(f'{msg}')
            if not config.silent:
                print(f'{msg}')
            sys.exit(1)
        except OSError as e:
            msg = f'Unable to create the export folder\n{e}'
            self.logger.error(f'{msg}')
            if not config.silent:
                print(f'{msg}')
            sys.exit(1)

    def create_folders(self):
        self.logger.debug(f"Creating folders for notebooks")
        for notebooks_id in self._notebooks:
            self._notebooks[notebooks_id].create_folders()

    def add_note_pages(self):
        self.logger.debug(f"Creating note page objects")

        if not config.silent:
            print(f"Finding note pages in {self._nsx_file_name.name}")
        with alive_bar(len(self._note_page_ids), bar='blocks') as bar:
            for note_id in self._note_page_ids:
                note_data = self.fetch_json_data(note_id)
                if self.is_note_encrypted(note_data):
                    self._encrypted_notes.append(note_data['title'])
                    self.logger.warning(f'The Note - "{note_data["title"]}" - is encrypted and has not been converted.')
                    continue

                note_page = NotePage(self, note_id, note_data)
                self._note_pages[note_id] = note_page
                if not config.silent:
                    bar()

            self._note_page_count += len(self._note_pages)

    @staticmethod
    def is_note_encrypted(note_data):
        return note_data['encrypt']

    def add_note_pages_to_notebooks(self):
        self.logger.info("Add note pages to notebooks")

        for note_page_id in self._note_pages:
            current_parent_id = self._note_pages[note_page_id].parent_notebook
            if current_parent_id in self._notebooks:
                self._notebooks[current_parent_id].pair_up_note_pages_and_notebooks(self._note_pages[note_page_id])
            else:
                self._notebooks['recycle-bin'].pair_up_note_pages_and_notebooks(self._note_pages[note_page_id])

    def store_attachments(self, attachments: list[Attachment]):
        if not config.silent:
            print("Saving attachments")

        with alive_bar(len(attachments), bar='blocks') as bar:
            for attachment in attachments:
                if attachment.attachment.full_path.is_dir():
                    message = f'Unable to save attachment for the note {attachment.note_title}.  ' \
                              f'Attachment path is to existing dir not file - {attachment.attachment.full_path}'
                    self.logger.warning(message)
                    if not config.silent:
                        print(message)
                        bar()
                    continue

                file_writer.store_file(attachment.attachment.full_path, attachment.attachment.get_content_to_save())
                if not config.silent:
                    bar()

    def process_notebooks(self):
        for notebooks_id in self._notebooks:
            self._notebooks[notebooks_id].process_notebook_pages()

    def save_note_pages(self):
        if not config.silent:
            print("Saving note pages")
        with alive_bar(len(self._note_pages), bar='blocks') as bar:
            for note_page_id in self._note_pages:
                file_writer.store_file(self._note_pages[note_page_id].full_path,
                                       self._note_pages[note_page_id].converted_content)
                if not config.silent:
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
    def encrypted_notes(self):
        return self._encrypted_notes
