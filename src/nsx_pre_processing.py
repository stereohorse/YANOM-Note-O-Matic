import logging
import re

from bs4 import BeautifulSoup

from chart_processing import NSXChartProcessor
from checklist_processing import NSXInputMDOutputChecklistProcessor, NSXInputHTMLOutputChecklistProcessor
import config
from helper_functions import add_strong_between_tags, change_html_tags
from iframe_processing import pre_process_iframes_from_html
import image_processing
from metadata_processing import MetaDataProcessor
from sn_attachment import FileNSAttachment


def what_module_is_this():
    return __name__


class NoteStationPreProcessing:
    """
    Main driver for pre-processing of synology html note data.

    Clean and format data for pandoc.  Also regenerate html checklists or put in place holders to aid adding checklists
    back in markdown files after pandoc processing.
    """

    def __init__(self, note):
        self.logger = logging.getLogger(f'{config.yanom_globals.app_name}.'
                                        f'{what_module_is_this()}.'
                                        f'{self.__class__.__name__}'
                                        )
        self.logger.setLevel(config.yanom_globals.logger_level)
        self._note = note
        self.pre_processed_content = note.raw_content
        self._attachments = note.attachments
        self._image_attachments = []
        self._image_tags = {}
        self._obsidian_image_tags = {}
        self._iframes_dict = {}
        self._checklist_processor = None
        self._charts = []
        self._metadata_processor = None
        self.soup = None

    @property
    def metadata_processor(self):
        return self._metadata_processor

    @property
    def checklist_processor(self):
        return self._checklist_processor

    @property
    def iframes_dict(self):
        return self._iframes_dict

    @property
    def obsidian_image_tags(self):
        return self._obsidian_image_tags

    def pre_process_note_page(self):
        self.logger.debug(f"Pre processing of note page {self._note.title}")
        self.process_image_tags()
        if self._note.conversion_settings.export_format != 'pandoc_markdown_strict' \
                and self._note.conversion_settings.export_format != 'html':
            self._process_iframes()
        self._fix_ordered_list()
        self._fix_unordered_list()
        self._fix_check_lists()
        self._add_boarder_to_tables()
        if self._note.conversion_settings.first_row_as_header:
            self._fix_table_headers()
        if self._note.conversion_settings.first_column_as_header:
            self._first_column_in_table_as_header_if_required()
        self._extract_and_generate_chart()
        if self._note.conversion_settings.front_matter_format != 'none':
            self._generate_metadata()
        self._generate_links_to_other_note_pages()
        self._add_file_attachment_links()
        self._clean_excessive_divs()

    def _process_iframes(self):
        self.pre_processed_content, self._iframes_dict = pre_process_iframes_from_html(self.pre_processed_content)

    def process_image_tags(self):
        self.logger.debug(f"Cleaning image tags")
        self.soup = BeautifulSoup(self.pre_processed_content, 'html.parser')

        image_tags = self.soup.findAll('img')

        for i in range(len(image_tags)):
            if 'src' not in image_tags[i].attrs:
                self.logger.warning(f"No 'src' in html content for tag '{image_tags[i]}'")

            self.clean_image_tag(image_tags[i])

            self.generate_obsidian_tag_if_required(image_tags[i])

        self.pre_processed_content = str(self.soup)

    def clean_image_tag(self, tag):
        src_path = None
        if 'ref' in tag.attrs:
            src_path = self.get_image_relative_path(tag.attrs['ref'])
        new_attrs = image_processing.clean_html_image_tag(tag, src_path)
        tag.attrs = new_attrs

    def generate_obsidian_tag_if_required(self, tag):
        if self._note.conversion_settings.export_format == 'obsidian':
            obsidian_img_tag_markdown = image_processing.generate_obsidian_image_markdown_link(tag)
            if not obsidian_img_tag_markdown:
                return  # Return as tag did not need obsidian formatting
            # Using a placeholder text inserted into content because pandoc will escape characters
            # in the obsidian link like this \!\[\|600]() which is valid markdown but ugly it is a 'feature' of pandoc
            # and not going to be changed because escaping still gives valid markdown it is due to the intermediate step
            # in pandoc's conversion where it cannot recognise the text is already valid markdown so assumes
            # the special characters need to be escaped.
            placeholder = str(id(obsidian_img_tag_markdown))
            self._obsidian_image_tags[placeholder] = obsidian_img_tag_markdown

            new_tag = self.soup.new_tag("p")
            new_tag.string = placeholder

            tag.replaceWith(new_tag)
            # placeholder is replaced with actual link in nsx_post_processing._format_images_links()

    def get_image_relative_path(self, tag_ref):
        for attachment in self._attachments.values():
            try:
                if attachment.image_ref == tag_ref:
                    return str(attachment.path_relative_to_notebook)
                # the ask for forgiveness approach an non file attachment object will not have an image_ref attribute
                # raise exception and then continue effectively skipping the file attachments
            except AttributeError:
                continue

    def _clean_excessive_divs(self):
        """
        Replace all the div tags with p tags
        """
        self.logger.debug(f"Cleaning html <div")
        self.pre_processed_content = self.pre_processed_content.replace('<div></div>', '<p></p>')
        self.pre_processed_content = self.pre_processed_content.replace('<div', '<p')
        self.pre_processed_content = self.pre_processed_content.replace('</div', '</p')

    def _fix_ordered_list(self):
        self.logger.debug(f"Cleaning number lists")
        self.pre_processed_content = self.pre_processed_content.replace('</li><ol><li>', '<ol><li>')
        self.pre_processed_content = self.pre_processed_content.replace('</li></ol><li>', '</li></ol></li><li>')

    def _fix_unordered_list(self):
        self.logger.debug(f"Cleaning bullet lists")
        self.pre_processed_content = self.pre_processed_content.replace('</li><ul><li>', '<ul><li>')
        self.pre_processed_content = self.pre_processed_content.replace('</li></ul><li>', '</li></ul></li><li>')

    def _fix_check_lists(self):
        self.logger.debug(f"Cleaning check lists")

        if self._note.conversion_settings.export_format == 'html':
            self._checklist_processor = NSXInputHTMLOutputChecklistProcessor(self.pre_processed_content)
        else:
            self._checklist_processor = NSXInputMDOutputChecklistProcessor(self.pre_processed_content)

        self.pre_processed_content = self._checklist_processor.processed_html
        pass

    def _extract_and_generate_chart(self):
        self.logger.debug(f"Cleaning charts")

        chart_options = {'create_image': self._note.conversion_settings.chart_image,
                         'create_csv': self._note.conversion_settings.chart_csv,
                         'create_data_table': self._note.conversion_settings.chart_data_table,
                         }
        chart_processor = NSXChartProcessor(self._note, self.pre_processed_content, **chart_options)

        self.pre_processed_content = chart_processor.processed_html

    def _fix_table_headers(self):
        self.logger.debug(f"Cleaning table headers")
        tables = re.findall('<table.*</table>', self.pre_processed_content)

        for table in tables:
            if table.count('<tr>') > 2:  # only make header row if table has more than one row
                new_table = table
                new_table = new_table.replace('<b>', '<strong>')
                new_table = new_table.replace('</b>', '</strong>')
                new_table = new_table.replace('<tbody>', '<thead>')
                new_table = new_table.replace('</td></tr>', '</td></tr></thead><tbody>', 1)
                self.pre_processed_content = self.pre_processed_content.replace(table, new_table)

    def _first_column_in_table_as_header_if_required(self):
        self.logger.debug(f"Make tables first column bold")
        tables = re.findall('<table.*</table>', self.pre_processed_content)

        for table in tables:
            new_table = add_strong_between_tags('<tr><td>', '</td><td>', table)
            new_table = change_html_tags('<tr><td>', '</td>', '<tr><th>', '</th>', new_table)
            self.pre_processed_content = self.pre_processed_content.replace(table, new_table)

    def _add_boarder_to_tables(self):
        self.logger.debug(f"Adding boarders to tables")
        tables = re.findall('<table.*</table>', self.pre_processed_content)

        for table in tables:
            new_table = table
            new_table = new_table.replace('<table', '<table border="1"')
            self.pre_processed_content = self.pre_processed_content.replace(table, new_table)

    def _generate_metadata(self):
        self.logger.debug(f"Generating meta-data")
        self._metadata_processor = MetaDataProcessor(self._note.conversion_settings)
        self._metadata_processor.parse_dict_metadata(self._note.note_json)
        self.pre_processed_content = f'<head><title> </title></head>{self.pre_processed_content}'
        self.pre_processed_content = self._metadata_processor.add_metadata_html_to_content(self.pre_processed_content)

    def _generate_links_to_other_note_pages(self):
        self.logger.debug(f"Creating links between pages")
        self.pre_processed_content = \
            self._note.nsx_file.inter_note_link_processor.update_content(self.pre_processed_content)

    def _add_file_attachment_links(self):
        self.logger.debug(f"Add attachment links to page content")
        attachments = [attachment
                       for attachment in self._note.attachments.values()
                       if type(attachment) is FileNSAttachment
                       ]
        if attachments:
            self.pre_processed_content = f'{self.pre_processed_content}<h6>Attachments</h6>'
            for attachment in attachments:
                self.pre_processed_content = f'{self.pre_processed_content}<p>{attachment.html_link}</p>'
