from checklist_processing import HTMLInputMDOutputChecklistProcessor
from content_link_management import get_attachment_paths, update_content_with_new_paths
from content_link_management import update_href_link_suffix_in_content
from file_converter_abstract import FileConverter
from iframe_processing import pre_process_iframes_from_html, post_process_iframes_to_markdown
from metadata_processing import MetaDataProcessor


class HTMLToMDConverter(FileConverter):
    def __init__(self, conversion_settings, files_to_convert):
        super().__init__(conversion_settings, files_to_convert)
        self._iframes_dict = {}

    def pre_process_content(self):
        self.logger.debug(f'Pre-process HTML file {self._file}')
        self._checklist_processor = HTMLInputMDOutputChecklistProcessor(self._file_content)
        self._pre_processed_content = self._checklist_processor.processed_html
        self._pre_processed_content = update_href_link_suffix_in_content(self._pre_processed_content,
                                                                                                 self._output_extension,
                                                                                                 self._files_to_convert)
        self.parse_metadata_if_required()
        self.logger.debug(f'Search for iframes')
        self._pre_processed_content, self._iframes_dict = pre_process_iframes_from_html(self._pre_processed_content)
        renamed_file = self.rename_target_file_if_it_already_exists()
        if renamed_file is not None:
            self.update_content_for_renamed_file(renamed_file)

    def parse_metadata_if_required(self):
        self._metadata_processor = MetaDataProcessor(self._conversion_settings)
        self._metadata_processor.parse_html_metadata(self._pre_processed_content)

    def post_process_content(self):
        self._post_processed_content = self._converted_content
        self.post_process_obsidian_image_links_if_required()
        self.update_checklists()
        self.add_meta_data_if_required()
        if self._iframes_dict:
            self.logger.debug(f'Add iframes to Markdown content')
            self._post_processed_content = post_process_iframes_to_markdown(self._post_processed_content,
                                                                            self._iframes_dict)
        self.add_one_last_line_break()
        self._current_note_attachment_links = get_attachment_paths(self._conversion_settings.source_absolute_root,
                                                                   self._conversion_settings.export_format,
                                                                   self._file,
                                                                   self._files_to_convert,
                                                                   self._post_processed_content
                                                                   )

        self._post_processed_content = update_content_with_new_paths(
            self._post_processed_content,
            self._file,
            self._current_note_attachment_links.non_copyable_relative,
            self._conversion_settings.make_absolute,
            self._conversion_settings.export_folder_absolute
        )

    def update_checklists(self):
        self._post_processed_content = self._checklist_processor.checklist_post_processing(self._post_processed_content)

    def add_one_last_line_break(self):
        self._post_processed_content = f'{self._post_processed_content}\n'

    def add_meta_data_if_required(self):
        self._post_processed_content = self._metadata_processor.add_metadata_md_to_content(self._post_processed_content)
