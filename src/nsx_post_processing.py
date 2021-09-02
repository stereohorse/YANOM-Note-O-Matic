import logging

import config
import helper_functions
from iframe_processing import post_process_iframes_to_markdown


def what_module_is_this():
    return __name__


class NoteStationPostProcessing:
    def __init__(self, note):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._note = note
        self._conversion_settings = note.conversion_settings
        self._yaml_header = ''
        self._post_processed_content = note.converted_content
        self.post_process_note_page()

    def post_process_note_page(self):
        if self._conversion_settings.front_matter_format != 'none':
            self._add_meta_data()
        if self._conversion_settings.export_format != 'html':
            self._post_processed_content = helper_functions.replace_markdown_pseudo_html_href_tag_with_markdown_links(
                self._post_processed_content)
        self._add_check_lists()
        if self._note.conversion_settings.export_format != 'pandoc_markdown_strict':
            self._add_iframes()
        self._format_images_links()
        self._add_one_last_line_break()

    def _add_meta_data(self):
        self.logger.debug(f"Adding meta-data to page")
        self._post_processed_content = \
            self._note.pre_processor.metadata_processor.add_metadata_md_to_content(self._post_processed_content)

    def _add_check_lists(self):
        if self._note.pre_processor.checklist_processor.list_of_checklist_items:
            self.logger.debug(f"Adding checklists to page")
            self._post_processed_content = \
                self._note.pre_processor.checklist_processor.checklist_post_processing(self._post_processed_content)

    def _add_iframes(self):
        if self._note.pre_processor.iframes_dict:
            self.logger.debug(f"Adding iframes to note page")
            self._post_processed_content = post_process_iframes_to_markdown(self._post_processed_content,
                                                                            self._note.pre_processor.iframes_dict)

    def _format_images_links(self):
        if self._conversion_settings.export_format == 'obsidian':
            self.logger.debug(f"Formatting image links for Obsidian")
            for placeholder, new_tag in self._note.pre_processor.obsidian_image_tags.items():
                self._post_processed_content = self._post_processed_content.replace(f'{placeholder}', new_tag)

    def _add_one_last_line_break(self):
        self._post_processed_content = f'{self._post_processed_content}\n'

    @property
    def post_processed_content(self):
        return self._post_processed_content
