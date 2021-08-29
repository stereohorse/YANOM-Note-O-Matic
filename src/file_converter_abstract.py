from abc import ABC, abstractmethod
from collections import namedtuple
import logging
from pathlib import Path

import config
import content_link_management
import helper_functions
import file_writer
import file_mover
import image_processing
from pandoc_converter import PandocConverter


def what_module_is_this():
    return __name__


RenamedFile = namedtuple('RenamedFile',
                         'original_absolute, original_relative, new_absolute, new_relative',
                         )


class FileConverter(ABC):
    def __init__(self, conversion_settings, files_to_convert):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._file = None
        self._files_to_convert = files_to_convert
        self._file_content = ''
        self._meta_content = {}
        self._pre_processed_content = ''
        self._converted_content = ''
        self._post_processed_content = ''
        self._conversion_settings = conversion_settings
        self._output_extension = file_mover.get_file_suffix_for(self._conversion_settings.export_format)
        self._pandoc_converter = PandocConverter(self._conversion_settings)
        self._pre_processor = None
        self._checklist_processor = None
        self._image_processor = None
        self._metadata_processor = None
        self._note_page_count = 0
        self._copyable_attachment_absolute_path_set = set()
        self._non_copyable_attachment_path_set = set()
        self._non_existing_links_set = set()
        self._existing_links_set = set()
        self._copyable_attachment_path_set = set()
        self._created_note_path = None
        self._renamed_note_file = None
        self._current_note_attachment_links = None

    @abstractmethod
    def pre_process_content(self):  # pragma: no cover
        pass

    @abstractmethod
    def post_process_content(self):  # pragma: no cover
        pass

    @abstractmethod
    def parse_metadata_if_required(self):  # pragma: no cover
        pass

    @abstractmethod
    def add_meta_data_if_required(self):  # pragma: no cover
        pass

    # def update_note_links_in_html_content(self, content):
    #     soup = BeautifulSoup(content, 'html.parser')
    #     for a_tag in soup.findAll(href=True):
    #         url_path = Path(urlparse(a_tag['href']).path)
    #         if url_path in self._files_to_convert:
    #             link = str(url_path.with_suffix(self._output_extension))
    #             a_tag['href'] = str(link)
    #
    #     return str(soup)

    def convert_note(self, file):
        self._file = Path(file)
        self.read_file()
        self.pre_process_content()
        self.convert_content()
        self.post_process_content()

    def read_file(self):
        self._file_content = self._file.read_text(encoding='utf-8')

    def convert_content(self):
        self.logger.info(f"Converting content of '{self._file}'")
        self._converted_content = self._pandoc_converter.convert_using_strings(self._pre_processed_content,
                                                                               str(self._file))

    def pre_process_obsidian_image_links_if_required(self):
        if self._conversion_settings.markdown_conversion_input == 'obsidian':
            self.logger.debug(f"Pre process obsidian image links")
            self._pre_processed_content = image_processing.replace_obsidian_image_links_with_html_img_tag(
                self._pre_processed_content)

    def post_process_obsidian_image_links_if_required(self):
        if self._conversion_settings.export_format == 'obsidian':
            self.logger.debug(f"Post process obsidian image links")
            self._post_processed_content = image_processing.replace_markdown_html_img_tag_with_obsidian_image_links(
                self._post_processed_content)

    def write_post_processed_content(self):
        target_path = file_mover.create_target_absolute_file_path(
            file_path=self._file,
            source_absolute_root=self._conversion_settings.source_absolute_root,
            target_path_root=self._conversion_settings.export_folder_absolute,
            target_suffix=self._output_extension)

        self.logger.info(f"Writing new file {target_path}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        file_writer.write_text(target_path, self._post_processed_content)
        self._created_note_path = target_path

    def rename_target_file_if_it_already_exists(self):
        """
        Rename an exiting file that the new converted content would overwrite

        For the currently being converted file if an existing file exists for the name that will be exported
        and rename that original file.  Return named tuple containing required file paths that will allow
        any links in the content being converted to be updated with the new filename.

        Returns
        -------
        RenamedFile
            Named tuple containing the relative and absolute paths for the original and new filename

        """
        # NOTE this is still required for edge case.  When copying over attachments, in theory, an attachment
        # may have same name as a newly created note file.  SO we rename that attachment to old-1 here.
        n = 0
        target_path = file_mover.create_target_absolute_file_path(
            file_path=self._file,
            source_absolute_root=self._conversion_settings.source_absolute_root,
            target_path_root=self._conversion_settings.export_folder_absolute,
            target_suffix=self._output_extension)

        if not target_path.exists():  # no need for renaming if target file does not exist
            return

        new_target_path = target_path
        while new_target_path.exists():
            n += 1
            new_target_path = Path(target_path.parent, f'{target_path.stem}-old-{n}{target_path.suffix}')

        target_path.replace(new_target_path)  # rename the existing target file with the new -old-'n' name
        self._renamed_note_file = new_target_path

        original_absolute = helper_functions.absolute_path_for(Path(target_path.name),
                                                               self._conversion_settings.source_absolute_root
                                                               )
        new_absolute = new_target_path
        original_relative = helper_functions.relative_path_for(Path(target_path.name),
                                                               self._conversion_settings.source_absolute_root
                                                               )
        new_relative = helper_functions.relative_path_for(new_target_path,
                                                          self._conversion_settings.export_folder_absolute
                                                          )

        return RenamedFile(original_absolute, original_relative, new_absolute, new_relative)

    def update_content_for_renamed_file(self, renamed_file: RenamedFile):
        # replace relative and absolute version as either may exist in the content
        # html replacement is always used as html formatted links can be in any of the input formats
        self._pre_processed_content = content_link_management.update_html_link_src(
            self._pre_processed_content,
            renamed_file.original_absolute,
            renamed_file.new_absolute,
        )
        self._pre_processed_content = content_link_management.update_html_link_src(
            self._pre_processed_content,
            renamed_file.original_relative,
            renamed_file.new_relative,
        )
        if self._conversion_settings.conversion_input == 'markdown':
            #  if input is markdown also replace name in any markdown formatted links
            self._pre_processed_content = content_link_management.update_markdown_link_src(
                self._pre_processed_content,
                renamed_file.original_absolute,
                renamed_file.new_absolute,
            )
            self._pre_processed_content = content_link_management.update_markdown_link_src(
                self._pre_processed_content,
                renamed_file.original_relative,
                renamed_file.new_relative,
            )

    @property
    def renamed_note_file(self):
        return self._renamed_note_file

    @property
    def current_note_attachment_links(self):
        return self._current_note_attachment_links
