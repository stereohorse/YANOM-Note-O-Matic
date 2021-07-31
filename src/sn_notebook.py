import logging
from pathlib import Path

from alive_progress import alive_bar

import config
from config import yanom_globals
import helper_functions
from helper_functions import generate_clean_directory_name
from sn_note_page import NotePage
import zip_file_reader


def what_module_is_this():
    return __name__


class Notebook:
    def __init__(self, nsx_file, notebook_id):
        self.logger = logging.getLogger(f'{config.APP_NAME}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.logger_level)
        self.nsx_file = nsx_file
        self.notebook_id = notebook_id
        self.conversion_settings = self.nsx_file.conversion_settings
        self._notebook_json = self.fetch_notebook_json(notebook_id)
        self.title = self.fetch_notebook_title()
        self.folder_name = ''
        self.create_folder_name()
        self._full_path_to_notebook = None
        self.note_pages = []
        self.note_titles = []

    def process_notebook_pages(self):
        self.logger.info(f"Processing note book {self.title} - {self.notebook_id}")

        if not config.silent:
            print(f"Processing '{self.title}' Notebook")
        with alive_bar(len(self.note_pages), bar='blocks') as bar:
            for note_page in self.note_pages:
                note_page.process_note()
                if not config.silent:
                    bar()

    def fetch_notebook_json(self, notebook_id):
        if notebook_id == 'recycle-bin':
            return {'title': 'recycle-bin'}

        self.logger.info(f"Fetching json data file {notebook_id} from {self.nsx_file.nsx_file_name}")
        note_book_json = zip_file_reader.read_json_data(self.nsx_file.nsx_file_name, notebook_id)

        if note_book_json is None:
            self.logger.warning("Unable to read notebook json data from nsx file. using 'title': 'Unknown Notebook'")
            return {'title': 'Unknown Notebook'}

        return note_book_json

    def fetch_notebook_title(self):
        notebook_title = self._notebook_json.get('title', None)
        if notebook_title is None:
            self.logger.warning(f"The data for notebook id '{self.notebook_id}' does not have a key for 'title' using 'Unknown Notebook'")
            return 'Unknown Notebook'
        if notebook_title == "":  # The notebook with no title is called 'My Notebook' in note station
            return "My Notebook"

        return notebook_title

    def pair_up_note_pages_and_notebooks(self, note_page: NotePage):
        self.logger.debug(f"Adding note '{note_page.title}' - {note_page.note_id} "
                          f"to Notebook '{self.title}' - {self.notebook_id}")

        note_page.notebook_folder_name = self.folder_name
        note_page.parent_notebook_id = self.notebook_id

        while note_page.title in self.note_titles:
            note_page.increment_duplicated_title(self.note_titles)

        self.note_titles.append(note_page.title)
        self.note_pages.append(note_page)

    def create_folder_name(self):
        self.folder_name = Path(generate_clean_directory_name(self.title,
                                                              yanom_globals.path_part_max_length,
                                                              allow_unicode=True))
        self.logger.info(f'For the notebook "{self.title}" the folder name used is is {self.folder_name }')

    def create_notebook_folder(self, parents=True):
        self.logger.debug(f"Creating notebook folder for {self.title}")

        n = 0
        target_path = Path(self.conversion_settings.working_directory,
                           config.DATA_DIR,
                           self.nsx_file.conversion_settings.export_folder,
                           self.folder_name)

        while target_path.exists():
            n += 1
            target_path = Path(self.conversion_settings.working_directory,
                               config.DATA_DIR,
                               self.nsx_file.conversion_settings.export_folder,
                               f"{self.folder_name}-{n}")
        try:
            target_path.mkdir(parents=parents, exist_ok=False)
            self.folder_name = Path(target_path.name)
            self._full_path_to_notebook = target_path
        except FileNotFoundError as e:
            msg = f'Unable to create notebook folder there is a problem with the path.\n{e}'
            self.logger.error(f'{msg}')
            self.logger.error(helper_functions.log_traceback(e))
            if not config.silent:
                print(f'{msg}')
        except OSError as e:
            msg = f'Unable to create note book folder\n{e}'
            self.logger.error(f'{msg}')
            self.logger.error(helper_functions.log_traceback(e))
            if not config.silent:
                print(f'{msg}')

    def create_attachment_folder(self):
        if self.full_path_to_notebook:   #if full path is still None then the fodler was not created and we can skip
            self.logger.debug(f"Creating attachment folder")
            Path(self.full_path_to_notebook, self.conversion_settings.attachment_folder_name).mkdir()
            return

        self.logger.warning(f"Attachment folder for '{self.title}' was not created as the notebook folder has not been created")

    @property
    def full_path_to_notebook(self):
        return self._full_path_to_notebook
