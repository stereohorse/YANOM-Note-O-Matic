import logging
from pathlib import Path

import config


def what_module_is_this():
    return __name__


def get_result_as_string(item_count, message):
    if item_count == 0:
        return ''

    plural = ''
    if item_count > 1:
        plural = 's'
    result = f'{item_count} {message}{plural}'
    return result


class Report:
    def __init__(self, note_converter):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._report = ''
        self._source = note_converter

    @property
    def report(self):
        return self._report

    def generate_report(self):
        self._report = self.get_conversion_summary()
        self.update_report_for_invalid_links()
        self.update_report_for_orphan_files()
        self.update_report_for_missing_attachments()
        if self._source.conversion_settings.conversion_input == 'nsx':
            self.update_report_for_null_attachments()
            self.update_report_for_encrypted_notes()
        self.update_report_for_non_copyable_attachments()
        self.update_report_for_absolute_attachments()

    def get_conversion_summary(self):
        conversion_results = '# Conversion summary'
        result = get_result_as_string(self._source.note_book_count, 'Note book')
        if result:
            conversion_results = f"{conversion_results}\n{result}"

        result = get_result_as_string(self._source.note_page_count, 'Note page')
        if result:
            conversion_results = f"{conversion_results}\n{result}"

        result = get_result_as_string(self._source.image_count, 'Image')
        if result:
            conversion_results = f"{conversion_results}\n{result}"

        result = get_result_as_string(self._source.attachment_count, 'Attachment')
        if result:
            conversion_results = f"{conversion_results}\n{result}"

        num_links_corrected = 0
        num_links_not_corrected = 0
        for nsx_file in self._source.nsx_backups:
            num_links_corrected = num_links_corrected + len(nsx_file.inter_note_link_processor.replacement_links)
            num_links_not_corrected = num_links_not_corrected + len(
                nsx_file.inter_note_link_processor.renamed_links_not_corrected)

        if (num_links_corrected + num_links_not_corrected) > 0:
            links_results = f'{num_links_corrected} out of {num_links_corrected + num_links_not_corrected} ' \
                            f'links between notes were re-created'
            conversion_results = f"{conversion_results}\n{links_results}"

        for nsx_file in self._source.nsx_backups:
            if nsx_file.inter_note_link_processor.unmatched_links_msg:
                conversion_results = f"{conversion_results}\n{nsx_file.inter_note_link_processor.unmatched_links_msg}"

        return conversion_results

    def get_orphan_file_report_details(self):
        orphan_messages = {
            'ignore': 'The following orphan files were left in the source location and not copied to the export folder',
            'move': 'The following orphan files were included in the export folder',
            'orphan': 'The following orphan files were put in the `orphan` folder in the export folder',
        }

        orphan_message = orphan_messages[self._source.conversion_settings.orphans]

        orphan_report_details = f"# Orphan Files\n{orphan_message}"

        for file in self._source.orphan_files:
            orphan_report_details = f"{orphan_report_details}\n{str(file)}"

        return orphan_report_details

    def get_file_list_report_details(self, title: str, attachment_list_name: str) -> str:
        report_details = title

        for file, attachment_results in self._source.attachment_details.items():
            if len(attachment_results[attachment_list_name]):
                report_details = f"{report_details}\n## For the note: [{file.name}]({str(file)})"
                for attachment in attachment_results[attachment_list_name]:
                    report_details = f"{report_details}\n{str(attachment)}"

        if report_details == title:
            return ''

        return report_details

    def update_report_for_orphan_files(self):
        if self._source.orphan_files:
            orphan_report_details = self.get_orphan_file_report_details()
            self._report = f"{self._report}\n{orphan_report_details}"

    def update_report_for_invalid_links(self):
        title = '# The following links are invalid for the current file system'

        invalid_link_details = self.get_file_list_report_details(title, 'invalid')
        self._report = f"{self._report}\n{invalid_link_details}"

    def update_report_for_absolute_attachments(self):
        title = '# Files linked to that are outside of the export path with absolute paths\n' \
                'The following files are linked from note pages but they are stored on disk in directories that ' \
                'are not the export path - "" or its subdirectories and use absolute file system paths\n' \
                'These links reduce the portability.  If the exported notes directory is moved between file ' \
                'systems the links may no longer work.'
        non_copyable_absolute_details = self.get_file_list_report_details(title, 'non_copyable_absolute')
        self._report = f"{self._report}\n{non_copyable_absolute_details}"

    def update_report_for_non_copyable_attachments(self):
        title = f'# Files linked to that are outside of the export path with relative paths\n' \
                f'The following files are linked from note pages but they are stored on disk in directories that ' \
                f'are not the export path - "{self._source.conversion_settings.export_folder_absolute}" or its ' \
                f'subdirectories and use relative paths to the export folder\n' \
                f'These links reduce the portability of notes as the export folder can not be moved without these ' \
                f'links breaking.  Consider changing these to absolute paths, however this can still lead to ' \
                f'portability issues as if the exported notes directory is moved between file systems the links may ' \
                f'no longer work.'
        non_copyable_relative_details = self.get_file_list_report_details(title, 'non_copyable_relative')
        self._report = f"{self._report}\n{non_copyable_relative_details}"

    def update_report_for_missing_attachments(self):
        title = '# Missing file links\nThe following files are linked from note pages but were not located on disk'
        missing_attachment_details = self.get_file_list_report_details(title, 'non_existing')
        self._report = f"{self._report}\n{missing_attachment_details}"

    def update_report_for_null_attachments(self):
        section_title = '# Null file links\n' \
                        'The following note pages had their attachment data set as nul in the export file ' \
                        'as such attachments may be missing'
        null_list_string = ''
        for note_book, null_title_list in self._source.nsx_null_attachments.items():
            for title in null_title_list:
                null_list_string = f'{null_list_string}\nNotebook - "{note_book}" - Note page - "{title}'

        if null_list_string:
            self._report = f'{self._report}\n{section_title}{null_list_string}'

    def update_report_for_encrypted_notes(self):
        section_title = '# Encrypted Notes\nThe following note pages are encrypted and have not been converted'
        encrypted_notes_string = ''
        for title in self._source.encrypted_notes:
            encrypted_notes_string = f'{encrypted_notes_string}\n{title}'

        if encrypted_notes_string:
            self._report = f'{self._report}\n{section_title}{encrypted_notes_string}'

    def save_results(self):
        from datetime import datetime
        now = datetime.now()
        filename = f"conversion_report-{now.strftime('%Y%m%d-%H%M%S')}.md"
        report_file = Path(self._source.conversion_settings.export_folder_absolute, filename)
        report_file.write_text(self._report)

    def output_results_if_not_silent_mode(self):
        if not config.yanom_globals.is_silent:
            print(f"{self._report}")

    def log_results(self):
        self.logger.info(f"{self._report}")
