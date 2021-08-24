from content_link_management import get_attachment_paths, update_content_with_new_paths
from content_link_management import update_href_link_suffix_in_content
import checklist_processing
from file_converter_abstract import FileConverter
from metadata_processing import MetaDataProcessor


class MDToHTMLConverter(FileConverter):
    def pre_process_content(self):
        self.logger.debug(f'pre-process content for - {self._file}')
        self._pre_processed_content = self._file_content
        self.parse_metadata_if_required()
        self.pre_process_obsidian_image_links_if_required()
        renamed_file = self.rename_target_file_if_it_already_exists()
        if renamed_file is not None:
            self.update_content_for_renamed_file(renamed_file)

    def parse_metadata_if_required(self):
        self._metadata_processor = MetaDataProcessor(self._conversion_settings)
        self._pre_processed_content = self._metadata_processor.parse_md_metadata(self._pre_processed_content)

    def post_process_content(self):
        self.logger.debug(f'Post process HTML content')
        self._post_processed_content = self._converted_content
        self._post_processed_content = update_href_link_suffix_in_content(self._post_processed_content,
                                                                          self._output_extension,
                                                                          self._files_to_convert)
        self.add_meta_data_if_required()
        self.update_checklists()
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

    def add_meta_data_if_required(self):
        self._post_processed_content = self._metadata_processor.add_metadata_html_to_content(
            self._post_processed_content)

    def update_checklists(self):
        self._post_processed_content = checklist_processing.enable_checklist_tags(self._post_processed_content)
