from abc import ABC, abstractmethod
import logging
import os.path
from pathlib import Path
import re
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup

import config
import file_writer
import file_mover
import image_processing
from pandoc_converter import PandocConverter


def what_module_is_this():
    return __name__


class FileConverter(ABC):
    def __init__(self, conversion_settings, files_to_convert):
        self.logger = logging.getLogger(
            f'{config.yanom_globals.app_name}.{what_module_is_this()}.{self.__class__.__name__}')
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
        self._created_note_path = set()
        self._renamed_note_file = None

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

    def update_note_links_in_html_content(self, content):
        soup = BeautifulSoup(content, 'html.parser')
        for a_tag in soup.findAll(href=True):
            url_path = Path(urlparse(a_tag['href']).path)
            if url_path in self._files_to_convert:
                link = str(url_path.with_suffix(self._output_extension))
                a_tag['href'] = str(link)

        return str(soup)

    def convert_note(self, file):
        self._file = Path(file)
        self.read_file()
        self.pre_process_content()
        self.convert_content()
        self.post_process_content()
        self.write_post_processed_content()

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
        target_path = file_mover.create_target_file_path(
            file_path=self._file,
            source_absolute_root=self._conversion_settings.source_absolute_root,
            target_path_root=self._conversion_settings.export_folder_absolute,
            target_suffix=self._output_extension)

        self.logger.info(f"Writing new file {target_path}")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        file_writer.write_text(target_path, self._post_processed_content)
        self._created_note_path = target_path

    def rename_target_file_if_it_already_exists(self):
        """Rename an exiting file that the new converted content would overwrite"""
        # NOTE this is still required for edge case.  When copying over attachments, in theory, an attachment
        # may have same name as a newly created note file.  SO we rename that attachment to old-1 here.
        # There is an issue as then where ever it was linked from the link will no longer work....
        self._renamed_note_file = None
        n = 0
        target_path = file_mover.create_target_file_path(
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

    def handle_attachment_paths(self, content):
        """
        Generate sets of attachment links that can be used to move attachment files where applicable and change
        links in content when required so that the links work to the new attachment file locations.

        Absolute attachment links
        Absolute links are not changed in the content.
        If the file exists the path is added to self._non_copyable_attachment_path_set
        If the file does not exist the path is added to self._non_existing_links_set

        Relative attachment links
        Links may be changed in the note content
        If the file does not exist the path is added to self._non_existing_links_set
        If the file for the relative link exists then:-
        If the relative link is with in the path of conversion_settings.source then it is
        NOT changed in the note content and the path to the attachment is added
        to self._copyable_attachment_absolute_path_set
        If the relative link is to a file not on the path of conversion_settings.source it is
        recalculated and IS changed in the content and the path to the attachment is added
        to self._non_copyable_attachment_path_set

        Parameters
        ==========
        content : str
            Note content

        Returns
        =======
        str
            The content provided with changed links if required.

        """

        set_of_links = self.scan_content_for_attachments(content)
        if set_of_links:
            existing_links, non_existing_links = self._split_set_existing_non_existing_links(set_of_links)
            copyable_attachment_path_set, non_copyable_attachment_path_set = self._split_existing_links_copyable_non_copyable(existing_links)
            content = self._update_content_with_new_attachment_paths(content, non_copyable_attachment_path_set)
            copyable_attachment_absolute_path_set = self._update_relative_links_to_absolute_links(copyable_attachment_path_set)

            self._non_existing_links_set.update(non_existing_links)
            self._existing_links_set.update(existing_links)
            self._copyable_attachment_path_set.update(copyable_attachment_path_set)
            self._copyable_attachment_absolute_path_set.update(copyable_attachment_absolute_path_set)
            self._non_copyable_attachment_path_set.update(non_copyable_attachment_path_set)

        return content

    def _update_relative_links_to_absolute_links(self, link_set) -> set[Path]:
        """Change any relative file paths to absolute file paths using the location of the converted file to calculate
        that absolute path"""
        new_link_set = set()
        for link in link_set:
            if not link.is_absolute():
                link = self._absolute_path_from_relative_path(self._file, str(link))

            new_link_set.add(link)

        return new_link_set

    def scan_content_for_attachments(self, content: str):
        """
        Search a markdown or html formatted content string string for links and return a set of file links

        Search for all links and build set of those links where the link is not a link to a 'https:\\' address,
        and then return the set of local file links

        Link formats supported are
        [any text](../my_other_notebook/attachments/five.pdf "test tool tip text")
        [or empty](../my_other_notebook/attachments/five.pdf)
        [any text](https:\\www.google.com "google")
        [or empty](https:\\www.google.com)
        <img src="markdownmonstericon.png" />

        uri's also have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
        becomes 'a path/another file.pdf'

        Parameters
        ----------
        content : str
            String containing markdown formatted text

        Returns
        -------
        set :
            Set containing local file links.

        """
        set_of_md_formatted_links = set()
        if not self._conversion_settings.export_format == 'html':
            set_of_md_formatted_links = FileConverter.set_of_markdown_file_paths_from(content)

        set_of_html_img_formatted_links = FileConverter.set_of_html_img_file_paths_from(content)

        set_of_html_href_formatted_links = FileConverter.set_of_html_href_file_paths_from(content)

        links = set_of_md_formatted_links | set_of_html_img_formatted_links | set_of_html_href_formatted_links

        attachment_links = self._remove_content_links_from_set_of_links(links)
        return attachment_links

    @staticmethod
    def set_of_html_href_file_paths_from(content):
        """
        search content for local file uri links and return a set of those links
        that have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
        becomes 'a path/another file.pdf'
        """
        soup = BeautifulSoup(content, 'html.parser')
        url_paths = {
            Path(unquote(urlparse(a_tag['href']).path))
            for a_tag in soup.findAll(href=True)
            if not urlparse(a_tag['href']).path.startswith("https:\\")}

        return url_paths

    @staticmethod
    def set_of_html_img_file_paths_from(content: str) -> set[Path]:
        """
        Search string for img tag links and return a set of local file path objects
        that have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
        becomes 'a path/another file.pdf'
        """

        soup = BeautifulSoup(content, 'html.parser')
        url_paths = {
            Path(unquote(urlparse(i_tag['src']).path))
            for i_tag in soup.findAll(src=True)
            if not urlparse(i_tag['src']).path.startswith("https:\\")}

        return url_paths

    @staticmethod
    def set_of_markdown_file_paths_from(content: str) -> set[Path]:
        """
        Search string for markdown formatted image and file links and return a set of local file path objects
        that have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
        becomes 'a path/another file.pdf'
        """

        regex_md_pattern = re.compile(r'''
            \[[^]]*]\(     # match the '[alt text](' part of the markdown link
            (              # start capturing group
            [^) ]*         # match many charcaters up to ) or up to a space [ ]
            )              # close capturing group
            (?:            # start non capturing group
            \)|            # match literal ) or single space
            )              # close non capturing group
        ''', re.MULTILINE | re.VERBOSE)

        matches_md = regex_md_pattern.findall(content)
        set_of_md_formatted_links = {Path(unquote(match))
                                     for match in matches_md
                                     if not match.startswith("https:\\")
                                     }
        return set_of_md_formatted_links

    def _remove_content_links_from_set_of_links(self, links: set[Path]) -> set[Path]:
        """Remove any links to the set of notes being converted from the provided set of links"""
        links_to_remove = set()
        for link in links:
            abs_link = link
            if not link.is_absolute():
                abs_link = self._absolute_path_from_relative_path(self._file, str(link))

            if abs_link in self._files_to_convert:
                links_to_remove.add(link)

        links.difference_update(links_to_remove)
        return links

    def _split_set_existing_non_existing_links(self, links: set[Path]):
        """Split a list of links into sets of existing and non-existing file links and return those sets"""
        existing_links = set()
        non_existing_links = set()

        for link in links:
            if link.is_absolute():
                if link.exists():
                    existing_links.add(link)
                else:
                    non_existing_links.add(link)
                continue

            absolute_link = self._absolute_path_from_relative_path(self._file, str(link))

            if absolute_link.exists():
                existing_links.add(link)
                continue

            non_existing_links.add(absolute_link)

        return existing_links, non_existing_links

    def _split_existing_links_copyable_non_copyable(self, existing_links):
        """
        Split the set of existing file links into two sets.  One set of links that will be copyable to the new export
        folder and one set that will not be copyable.

        The non-copyable links are links that have a path outside of the current conversion source path.
        For example if the source path is /somewhere/data  then files in paths outside of that path can not be
        copied to the export folder for example /somewhere/another_folder/attachment.pdf can not be copied whilst
        /somewhere/data/any_file_or_path/any_file.pdf can be copied
        _non_copyable_attachment_path_set and _copyable_attachment_path_set will be updated with the
        relevant paths

        """
        copyable_attachment_path_set = set()
        non_copyable_attachment_path_set = set()

        for link in existing_links:
            abs_link = link
            if not link.is_absolute():
                abs_link = self._absolute_path_from_relative_path(self._file, str(link))

            if self._conversion_settings.source_absolute_root in abs_link.parents:
                copyable_attachment_path_set.add(link)
                continue

            non_copyable_attachment_path_set.add(link)

        return copyable_attachment_path_set, non_copyable_attachment_path_set

    def _update_content_with_new_attachment_paths(self, content, non_copyable_attachment_path_set):
        """
        Update content with a new relative path or absoliute path for non_copyable attachment files

        Using the conversion setting 'make_absolute' relative paths in the content to files that can not be copied are
        updated with new paths that are relative to the export folder when make_absolute is False, or absolute paths
        when make_absolute is True

        """
        for link in non_copyable_attachment_path_set:
            if link.is_absolute():
                continue

            attachment_absolute_path = self._absolute_path_from_relative_path(self._file, str(link))
            new_path = attachment_absolute_path

            if not self._conversion_settings.make_absolute:
                new_relative_path = self._calculate_relative_path(
                    absolute_link=attachment_absolute_path,
                    target_root=self._conversion_settings.export_folder_absolute,
                )
                new_path = new_relative_path

            content = self._update_content_with_new_link(str(new_path), str(link), content)

        return content

    @staticmethod
    def _absolute_path_from_relative_path(file: Path, link: str) -> Path:
        return Path(os.path.abspath(Path(file.parent, link)))

    @staticmethod
    def _calculate_relative_path(absolute_link, target_root) -> Path:
        return Path(os.path.relpath(absolute_link, target_root))

    @staticmethod
    def _update_content_with_new_link(new_relative_path: str, link: str, content: str) -> str:
        return content.replace(link, new_relative_path)

    @property
    def copyable_attachment_absolute_path_set(self):
        return self._copyable_attachment_absolute_path_set

    @property
    def created_note_path(self):
        return self._created_note_path

    @property
    def renamed_note_file(self):
        return self._renamed_note_file

    @property
    def non_existing_links_set(self):
        return self._non_existing_links_set
