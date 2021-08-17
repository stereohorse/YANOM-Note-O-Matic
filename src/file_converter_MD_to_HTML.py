import checklist_processing
from file_converter_abstract import FileConverter
from metadata_processing import MetaDataProcessor


class MDToHTMLConverter(FileConverter):
    def pre_process_content(self):
        self.logger.debug(f'pre-process content for - {self._file}')
        self._pre_processed_content = self._file_content
        self.parse_metadata_if_required()
        self.pre_process_obsidian_image_links_if_required()
        self.rename_target_file_if_it_already_exists()

    def parse_metadata_if_required(self):
        self._metadata_processor = MetaDataProcessor(self._conversion_settings)
        self._pre_processed_content = self._metadata_processor.parse_md_metadata(self._pre_processed_content)

    def post_process_content(self):
        self.logger.debug(f'Post process HTML content')
        self._post_processed_content = self._converted_content
        self._post_processed_content = self.update_note_links_in_html_content(self._post_processed_content)
        self.add_meta_data_if_required()
        self.update_checklists()
        self._post_processed_content = self.handle_attachment_paths(self._post_processed_content)

    def add_meta_data_if_required(self):
        self._post_processed_content = self._metadata_processor.add_metadata_html_to_content(self._post_processed_content)

    def update_checklists(self):
        self._post_processed_content = checklist_processing.enable_checklist_tags(self._post_processed_content)
