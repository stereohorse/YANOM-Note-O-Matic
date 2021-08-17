import logging
from pathlib import Path
import shutil
import sys

from alive_progress import alive_bar

import config
from file_converter_HTML_to_MD import HTMLToMDConverter
from file_converter_MD_to_HTML import MDToHTMLConverter
from file_converter_MD_to_MD import MDToMDConverter
from interactive_cli import StartUpCommandLineInterface
from nsx_file_converter import NSXFile
from pandoc_converter import PandocConverter
from timer import Timer


def what_module_is_this():
    return __name__


class NotesConvertor:
    """
    A class to direct the conversion of note files into alternative output formats.

    Uses the passed in command line arguments to direct flow to use the ini file conversion settings or the
    interactive command line interface to set the conversion settings.  Then using the conversion settings
    directs the conversion of the required source file type. Once conversion is completed a summary of the process
    is displayed.

    """

    def __init__(self, args, config_data):
        self.logger = logging.getLogger(
            f'{config.yanom_globals.app_name}.{what_module_is_this()}.{self.__class__.__name__}')
        self.logger.setLevel(config.yanom_globals.logger_level)
        self.logger.info(f'Conversion startup')
        self.command_line_args = args
        self.conversion_settings = None
        self._note_page_count = 0
        self._note_book_count = 0
        self._image_count = 0
        self._attachment_count = 0
        self._nsx_backups = []
        self.pandoc_converter = None
        self.config_data = config_data
        self._set_of_found_attachments = set()
        self._set_files_to_convert = set()
        self._orphan_files = set()
        self._encrypted_notes = []
        self._set_of_created_note_files = set()
        self._set_of_renamed_note_files = set()
        self._set_of_not_found_attachments = set()

    def convert_notes(self):
        self.evaluate_command_line_arguments()
        self.create_export_folder_if_required()
        if self.conversion_settings.conversion_input == 'html':
            self.convert_html()
        elif self.conversion_settings.conversion_input == 'markdown':
            self.convert_markdown()
        else:
            self.convert_nsx()

        self.output_results_if_not_silent_mode()
        self.log_results()
        self.logger.info("Processing Completed")

    def create_export_folder_if_required(self):
        self.conversion_settings.export_folder_absolute.mkdir(parents=True, exist_ok=True)

    def convert_markdown(self):
        with Timer(name="md_conversion", logger=self.logger.info, silent=bool(config.yanom_globals.is_silent)):
            file_extension = 'md'
            md_files_to_convert = self.generate_file_list(file_extension)
            self.exit_if_no_files_found(md_files_to_convert, file_extension)

            if self.conversion_settings.export_format == 'html':
                md_file_converter = MDToHTMLConverter(self.conversion_settings, md_files_to_convert)
            else:
                md_file_converter = MDToMDConverter(self.conversion_settings, md_files_to_convert)

            self.process_files(md_files_to_convert, md_file_converter)

            self.handle_orphan_files_as_required()

    def handle_orphan_files_as_required(self):
        self._orphan_files = self.get_list_of_orphan_files()
        path_to_orphans = ''

        if self.conversion_settings.orphans == 'ignore':
            return

        if self.conversion_settings.orphans == 'copy':
            path_to_orphans = Path(self.conversion_settings.export_folder_absolute)

        if self.conversion_settings.orphans == 'orphan':
            path_to_orphans = Path(self.conversion_settings.export_folder_absolute, 'orphan')

        for file in self._orphan_files:
            relative_to_source = file.relative_to(self.conversion_settings.source_absolute_root)
            new_absolute_path = Path(path_to_orphans, relative_to_source)
            new_absolute_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy2(file, new_absolute_path)

    def generate_file_list(self, file_extension):
        if not self.conversion_settings.source.is_file():
            file_list_generator = self.conversion_settings.source_absolute_root.rglob(f'*.{file_extension}')
            file_list = {item for item in file_list_generator}
            return file_list

        return {self.conversion_settings.source}

    def exit_if_no_files_found(self, files_to_convert, file_extension):
        if not files_to_convert:
            self.logger.info(
                f"No .{file_extension} files found at path {self.conversion_settings.source}. Exiting program")
            if not config.yanom_globals.is_silent:
                print(f'No .{file_extension} files found at {self.conversion_settings.source}')
            sys.exit(0)

    def process_files(self, files_to_convert, file_converter):
        file_count = 0
        self._attachment_count = 0
        set_of_attachments = set()
        set_created_note_files = set()
        not_found_attachments = set()
        renamed_note_files = set()

        if not config.yanom_globals.is_silent:
            print(f"Processing note pages")
        with alive_bar(len(files_to_convert), bar='blocks') as bar:
            for file in files_to_convert:
                file_converter.convert_note(file)
                set_created_note_files.add(file_converter.created_note_path)
                set_of_attachments.update(file_converter.copyable_attachment_absolute_path_set)
                not_found_attachments.update(file_converter.non_existing_links_set)
                if file_converter.renamed_note_file:
                    renamed_note_files.add(file_converter.renamed_note_file)
                file_converter.write_post_processed_content()
                file_count += 1
                if not config.yanom_globals.is_silent:
                    bar()
                # TODO to handle the case of new note replaced by attachment
                #  if there is an attachment in the folder the notes are coming from
                #  and that attachment has the same name as a converted note,
                #  then the attachment will overwrite the note

        if not self.conversion_settings.source_absolute_root == self.conversion_settings.export_folder_absolute:
            if not config.yanom_globals.is_silent:
                print(f"Copying attachments")
            with alive_bar(len(set_of_attachments), bar='blocks') as bar:
                for attachment in set_of_attachments:
                    attachment_path_relative_to_source = attachment.relative_to(
                        self.conversion_settings.source_absolute_root)
                    target_attachment_absolute_path = Path(self.conversion_settings.export_folder_absolute,
                                                           attachment_path_relative_to_source
                                                           )
                    target_attachment_absolute_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(attachment, target_attachment_absolute_path)

                    if not config.yanom_globals.is_silent:
                        bar()

        self._note_page_count = file_count

        self._set_of_found_attachments = set_of_attachments
        self._set_of_not_found_attachments = not_found_attachments
        self._set_files_to_convert = set(files_to_convert)
        self._set_of_created_note_files = set(set_created_note_files)
        self._set_of_renamed_note_files = set(renamed_note_files)

    def get_list_of_orphan_files(self):
        set_of_all_files = {
            Path(file)
            for file
            in self.conversion_settings.source_absolute_root.rglob('*')
            if Path(file).is_file()
        }

        orphans = set_of_all_files \
                  - self._set_files_to_convert \
                  - self._set_of_found_attachments \
                  - self._set_of_created_note_files \
                  - self._set_of_renamed_note_files

        return orphans

    def convert_html(self):
        with Timer(name="html_conversion", logger=self.logger.info, silent=bool(config.yanom_globals.is_silent)):
            file_extension = 'html'
            html_files_to_convert = self.generate_file_list(file_extension)
            self.exit_if_no_files_found(html_files_to_convert, file_extension)
            html_file_converter = HTMLToMDConverter(self.conversion_settings, html_files_to_convert)
            self.process_files(html_files_to_convert, html_file_converter)
            self.handle_orphan_files_as_required()

    def convert_nsx(self):
        file_extension = 'nsx'
        nsx_files_to_convert = self.generate_file_list(file_extension)
        self.exit_if_no_files_found(nsx_files_to_convert, file_extension)
        self.pandoc_converter = PandocConverter(self.conversion_settings)
        self._nsx_backups = [NSXFile(file, self.conversion_settings, self.pandoc_converter)
                             for file in nsx_files_to_convert]
        self.process_nsx_files()

    def process_nsx_files(self):
        with Timer(name="nsx_conversion", logger=self.logger.info, silent=bool(config.yanom_globals.is_silent)):
            for nsx_file in self._nsx_backups:
                nsx_file.process_nsx_file()
                self.update_processing_stats(nsx_file)
                self._encrypted_notes += nsx_file.encrypted_notes

    def update_processing_stats(self, nsx_file):
        self._note_page_count += nsx_file.note_page_count
        self._note_book_count += nsx_file.note_book_count
        self._image_count += nsx_file.image_count
        self._attachment_count += nsx_file.attachment_count

    def evaluate_command_line_arguments(self):
        self.configure_for_ini_settings()

        if self.command_line_args['source']:
            self.conversion_settings.source = self.command_line_args['source']

        if self.command_line_args['export']:
            self.conversion_settings.export_folder = self.command_line_args['export']

        if self.command_line_args['silent'] or self.command_line_args['ini']:
            return

        self.logger.debug("Starting interactive command line tool")
        self.run_interactive_command_line_interface()

    def run_interactive_command_line_interface(self):
        command_line_interface = StartUpCommandLineInterface(self.conversion_settings)
        self.conversion_settings = command_line_interface.run_cli()
        self.config_data.conversion_settings = self.conversion_settings  # this will save the setting in the ini file
        self.logger.info("Using conversion settings from interactive command line tool")

    def configure_for_ini_settings(self):
        self.logger.info("Using settings from config  ini file")
        self.conversion_settings = self.config_data.conversion_settings

    def output_results_if_not_silent_mode(self):
        if not config.yanom_globals.is_silent:
            self.print_result_if_any(self._note_book_count, 'Note book')
            self.print_result_if_any(self._note_page_count, 'Note page')
            self.print_result_if_any(self._image_count, 'Image')
            self.print_result_if_any(self._attachment_count, 'Attachment')
            num_links_corrected = 0
            num_links_not_corrected = 0
            for nsx_file in self._nsx_backups:
                num_links_corrected = num_links_corrected + len(nsx_file.inter_note_link_processor.replacement_links)
                num_links_not_corrected = num_links_not_corrected + len(
                    nsx_file.inter_note_link_processor.renamed_links_not_corrected)
            if (num_links_corrected + num_links_not_corrected) > 0:
                print(f'{num_links_corrected} out of {num_links_corrected + num_links_not_corrected} '
                      f'links between notes were re-created')
            for nsx_file in self._nsx_backups:
                if nsx_file.inter_note_link_processor.unmatched_links_msg:
                    print(nsx_file.inter_note_link_processor.unmatched_links_msg)

    @staticmethod
    def print_result_if_any(conversion_count, message):
        if conversion_count == 0:
            return
        plural = ''
        if conversion_count > 1:
            plural = 's'
        print(f'{conversion_count} {message}{plural}')

    def log_results(self):
        self.logger.info(f"{self._note_book_count} Note books")
        self.logger.info(f"{self._note_page_count} Note Pages")
        self.logger.info(f"{self._image_count} Images")
        self.logger.info(f"{self._attachment_count} Attachments")
