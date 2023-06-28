import logging
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from bs4 import BeautifulSoup

import config
import helper_functions
import markdown_format_styling
from note_content_data import BlockQuote, Body, Break, BulletList, BulletListItem
from note_content_data import Caption
from note_content_data import Figure
from note_content_data import Head, HeadingItem
from note_content_data import Hyperlink
from note_content_data import ImageEmbed
from note_content_data import NoteData, NumberedList, NumberedListItem
from note_content_data import Paragraph
from note_content_data import SectionContent
from note_content_data import TextColorItem, TextFormatItem, TextItem
from note_content_data import Title
from note_content_data import UnrecognisedTag
from processing_options import ProcessingOptions

logger = logging.getLogger(f'{config.yanom_globals.app_name}.{__name__}')
logger.setLevel(config.yanom_globals.logger_level)


def is_a_tag(tag):
    """
    Simple BeautifulSoup Tag identification.

    If tag had s field of name assume it is a Beautiful Soup Tag.  This is simplistic as any object with .name will
    also return true.

    Parameters
    ----------
    tag : BeautifulSoup Tag object

    Returns
    -------
    bool

    """
    try:
        return True if tag.name else False  # if beautiful soup element has a name it is a tag
    # NOTE have to use try except as navigable string hss a name attribute even though it is not visible or accessible
    # passing navigable string does not cause exception but other objects would.  Can not use .hassattr() to avoid
    # exceptions with other objects because navigable strings would return True not False because of their
    # hidden .name attribute.  Of course could use isinstance but Tag is not listed in Beautiful Soups __all__ and
    # get an annoying linting warning.
    except AttributeError:
        return False


def process_child_items(tag, processing_options: ProcessingOptions,
                        note_specific_tag_cleaning: Optional[Callable] = None,
                        ) -> List[NoteData]:
    items = []
    for child in tag.children:
        if not is_a_tag(child):
            potential_string_to_keep = str(child).strip('\n')
            if potential_string_to_keep:
                items.append(TextItem(processing_options, potential_string_to_keep))
            continue

        found_items_this_tag = extract_from_tag(child, processing_options, note_specific_tag_cleaning)
        if found_items_this_tag:
            items = helper_functions.merge_iterable_or_item_to_list(items, found_items_this_tag)

    return items


IGNORED_TAGS = ['link', 'meta', 'hr', 'br', 'placeholder']
P_LIKE_TAGS = ['pre', 'center', 'font', 'code', 'cite', 'article']
SPAN_LIKE_TAGS = ['small', 'strong', 'ins', 'dl', 'dt', 'dd', 'abbr', 's', 'mention', 'kbd', 'sup', 'host', 'port',
                  'api-access-token', 'bot-username']
TABLE_TAGS = ['table', 'thead', 'tbody', 'td', 'tr', 'th', 'colgroup', 'col', 'caption']


def extract_from_tag(tag, processing_options: ProcessingOptions,
                     note_specific_tag_cleaning: Optional[Callable] = None,
                     ) -> Optional[Union[List[NoteData], NoteData]]:
    if not is_a_tag(tag):
        # is navigable string
        return

    if note_specific_tag_cleaning:
        data = note_specific_tag_cleaning(tag, processing_options)
        if data:
            return data

    if tag.name in IGNORED_TAGS:
        return

    if tag.name == 'head':
        return extract_from_head_tag(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == 'body':
        return extract_from_body(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == 'div':
        return extract_from_div(tag, processing_options, note_specific_tag_cleaning)

    if len(tag.name) == 2 and tag.name[:1] == 'h' and tag.name[-1].isdigit():
        return extract_from_heading(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == "a":
        return extract_from_hyperlink(tag, processing_options)

    if tag.name == "br":
        return Break(processing_options, [])

    if tag.name == "title":
        return extract_from_title(tag, processing_options)

    if tag.name == "blockquote":
        return extract_from_blockquote(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == "iframe":
        return extract_from_iframe(tag, processing_options, )

    if tag.name == 'section':
        return extract_from_section(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == 'p':
        return extract_from_p_or_i_tag(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == 'i':
        return extract_from_p_or_i_tag(tag, processing_options, note_specific_tag_cleaning)

    if tag.name in P_LIKE_TAGS:
        return extract_from_p_like(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == 'img':
        return extract_from_img_tag(tag, processing_options)

    if tag.name == 'svg':
        return extract_from_svg_tag(tag, processing_options)

    if tag.name == 'figure':
        return extract_from_figure(tag, processing_options)

    if tag.name == 'figcaption':
        return extract_from_figure_caption(tag, processing_options)

    if tag.name == 'ol':
        return extract_numbered_list_from_ol_tag(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == 'ul':
        return extract_bullet_list_from_ul_tag(tag, processing_options, note_specific_tag_cleaning)

    if tag.name == 'li':
        return extract_from_li_tag(tag, processing_options, note_specific_tag_cleaning)

    if tag.name in markdown_format_styling.format_styling:
        return extract_text_formatting(tag, markdown_format_styling.format_styling,
                                       processing_options, note_specific_tag_cleaning)

    if tag.name == 'span':
        if 'style' in tag.attrs:
            if 'color:' in tag['style']:
                return extract_from_coloured_text_span(tag, processing_options)

        return extract_from_unknown_span(tag, processing_options, note_specific_tag_cleaning)

    if tag.name in SPAN_LIKE_TAGS:
        return extract_from_span_like(tag, processing_options, note_specific_tag_cleaning)

    if tag.name in TABLE_TAGS:
        return extract_from_table(tag, processing_options, note_specific_tag_cleaning)

    return UnrecognisedTag(processing_options, str(tag), tag.text)


def extract_from_head_tag(tag, processing_options: ProcessingOptions,
                          note_specific_tag_cleaning: Optional[Callable] = None):
    if tag.name != 'head':
        return None

    head_items = process_child_items(tag, processing_options, note_specific_tag_cleaning)
    if head_items:
        return Head(processing_options, head_items)


def extract_from_body(tag, processing_options: ProcessingOptions,
                      note_specific_tag_cleaning: Optional[Callable] = None):
    if tag.name != 'body':
        return None

    items = process_child_items(tag, processing_options, note_specific_tag_cleaning)
    return Body(processing_options, items)


def extract_from_heading(heading_tag, processing_options: ProcessingOptions, note_specific_tag_cleaning):
    """Extract data from HTML 'h' tag.  Headings levels are restricted to 1-6"""
    if len(heading_tag.name) != 2 or heading_tag.name[:1] != 'h' or not heading_tag.name[-1].isdigit():
        return
    level_from_tag = int(''.join(filter(str.isdigit, heading_tag.name)))
    heading_level = helper_functions.bounded_number(level_from_tag, min_value=1, max_value=6)

    heading_text_items = process_child_items(heading_tag, processing_options, note_specific_tag_cleaning)
    heading_id = heading_tag.get('id', '')
    return HeadingItem(processing_options, heading_text_items, heading_level, heading_id)


def extract_from_coloured_text_span(tag, processing_options: ProcessingOptions):
    if tag.name == 'span':
        if 'style' in tag.attrs and 'color:' in tag['style']:
            if 'class' in tag.attrs:
                del tag.attrs['class']
            html_text = str(tag)
            plain_text = tag.string
            return TextColorItem(processing_options, html_text, plain_text)


def extract_text_formatting(tag, valid_formats: Dict, processing_options: ProcessingOptions,
                            note_specific_tag_cleaning: Optional[Callable] = None):
    if tag.name in valid_formats:
        items = process_child_items(tag, processing_options, note_specific_tag_cleaning)
        return TextFormatItem(processing_options, items, tag.name)


def extract_from_div(div_tag, processing_options: ProcessingOptions,
                     note_specific_tag_cleaning: Optional[Callable] = None):
    if div_tag.name != 'div':
        return

    items = []
    all_children = [child for child in div_tag.children if is_a_tag(child)]
    # child_items = process_child_items(div_tag, processing_options, note_specific_tag_cleaning)
    child_items = process_child_items(div_tag, processing_options, note_specific_tag_cleaning)

    items = helper_functions.merge_iterable_or_item_to_list(items, child_items)
    items = list(items)

    # stop multiple child divs creating multiple empty paragraphs
    if len(all_children) == 1 and all_children[0].name == 'div':
        return items

    # stop multiple child divs creating multiple empty paragraphs
    if len(items):
        if isinstance(items[0], Paragraph):
            return items

    return Paragraph(processing_options, items)


def extract_from_section(tag, processing_options: ProcessingOptions,
                         note_specific_tag_cleaning: Optional[Callable] = None):
    if tag.name != 'section':
        return

    section_items = process_child_items(tag, processing_options, note_specific_tag_cleaning)

    return SectionContent(processing_options, section_items)


def extract_from_blockquote(blockquote_tag, processing_options: ProcessingOptions,
                            note_specific_tag_cleaning: Optional[Callable] = None):
    if blockquote_tag.name != 'blockquote':
        return

    text_items = process_child_items(blockquote_tag, processing_options, note_specific_tag_cleaning)
    cite = blockquote_tag.attrs.get('cite', '')

    return BlockQuote(processing_options, text_items, cite)


def extract_from_title(title_tag, processing_options: ProcessingOptions):
    if title_tag.name != 'title':
        return

    return Title(processing_options, title_tag.string.strip())


def extract_from_p_or_i_tag(tag, processing_options: ProcessingOptions,
                            note_specific_tag_cleaning: Optional[Callable] = None) -> List[NoteData]:
    if tag.name not in ['p', 'i']:
        return

    return process_child_items(tag, processing_options, note_specific_tag_cleaning)


def extract_from_p_like(tag, processing_options: ProcessingOptions,
                        note_specific_tag_cleaning: Optional[Callable] = None) -> List[NoteData]:
    if tag.name not in P_LIKE_TAGS:
        return

    return process_child_items(tag, processing_options, note_specific_tag_cleaning)


def extract_from_img_tag(img_tag, processing_options: ProcessingOptions):
    if img_tag.name != 'img':
        return

    href = img_tag.get('src', '')
    query_param_index = href.find("?")
    if query_param_index != -1:
        href = href[:query_param_index]

    alt = img_tag.get('alt', '')
    width = img_tag.get('width', '')
    height = img_tag.get('height', '')
    image_path = Path(href)

    return ImageEmbed(processing_options, alt, href, image_path, width, height)


def extract_from_svg_tag(img_tag, processing_options: ProcessingOptions):
    if img_tag.name != 'svg':
        return

    href = ''
    width = img_tag.get('width', '')
    height = img_tag.get('height', '')
    contents = str(img_tag)
    image_path = Path(href)

    return ImageEmbed(processing_options=processing_options, contents=contents, href=href, width=width, height=height,
                      source_path=image_path)


def extract_from_hyperlink(tag, processing_options: ProcessingOptions):
    if tag.name != 'a':
        return

    link_href = tag.attrs.get('href', '')
    display_text = tag.text

    return Hyperlink(processing_options, display_text, link_href)


def extract_from_iframe(tag, processing_options: ProcessingOptions):
    if tag.name != 'iframe':
        return

    return TextItem(processing_options, str(tag))


def extract_from_figure(tag, processing_options: ProcessingOptions,
                        note_specific_tag_cleaning: Optional[Callable] = None):
    if tag.name != 'figure':
        return
    image_object = None
    caption_object = None

    image_tag = tag.find('img')
    if image_tag:
        image_object = extract_from_img_tag(image_tag, processing_options)

    caption_tag = tag.find('figcaption')
    if caption_tag:
        caption_object = extract_from_figure_caption(caption_tag, processing_options, note_specific_tag_cleaning)

    return Figure(processing_options, (image_object, caption_object))


def extract_from_figure_caption(tag, processing_options: ProcessingOptions,
                                note_specific_tag_cleaning: Optional[Callable] = None):
    caption_text = process_child_items(tag, processing_options, note_specific_tag_cleaning)

    return Caption(processing_options, caption_text)


def extract_from_unknown_span(tag, processing_options: ProcessingOptions, note_specific_tag_cleaning):
    if tag.name != 'span':
        return

    return process_child_items(tag, processing_options, note_specific_tag_cleaning)


def extract_from_span_like(tag, processing_options: ProcessingOptions, note_specific_tag_cleaning):
    if tag.name not in SPAN_LIKE_TAGS:
        return

    return process_child_items(tag, processing_options, note_specific_tag_cleaning)


def extract_from_table(tag, processing_options: ProcessingOptions, note_specific_tag_cleaning):
    if tag.name not in TABLE_TAGS:
        return

    return process_child_items(tag, processing_options, note_specific_tag_cleaning)


def extract_numbered_list_from_ol_tag(ol_tag, processing_options: ProcessingOptions, note_specific_tag_cleaning):
    if ol_tag.name != 'ol':
        return

    parser = HTMLListParser(processing_options, note_specific_tag_cleaning, NumberedListItem, ordered=True)
    parser.feed(str(ol_tag))
    num_list = NumberedList(processing_options, parser.list_of_list_items)
    return num_list


def extract_bullet_list_from_ul_tag(ul_tag, processing_options: ProcessingOptions, note_specific_tag_cleaning):
    if ul_tag.name != 'ul':
        return

    parser = HTMLListParser(processing_options, note_specific_tag_cleaning, BulletListItem, ordered=False)
    parser.feed(str(ul_tag))
    num_list = BulletList(processing_options, parser.list_of_list_items)
    return num_list


def extract_from_li_tag(li_tag, processing_options: ProcessingOptions, note_specific_tag_cleaning):
    if li_tag.name != 'li':
        return

    contents = process_child_items(li_tag, processing_options, note_specific_tag_cleaning)

    # Note we return list of contents.  another function must identify indent level and create
    # a ListItem type of instance
    return contents


class HTMLListParser(HTMLParser):
    def error(self, message):  # pragma: no cover
        # This is a deprecated abstract method that is still lurking around in HTMLParser and needs to be implemented
        pass  # pragma: no cover

    def __init__(self, processing_options, note_specific_tag_cleaning, list_item_type, ordered=False):
        super().__init__()
        self.processing_options = processing_options
        self.note_specific_tag_cleaning = note_specific_tag_cleaning
        self.list_item_type = list_item_type
        self.ordered = ordered
        self.indent = -1
        self.li_contents = []
        self.current_tag_is_li = False
        self.list_of_list_items = []
        self.list_type_tag = ''
        self.set_list_type_tag()

    def set_list_type_tag(self):
        if self.ordered:
            self.list_type_tag = 'ol'
            return

        self.list_type_tag = 'ul'

    def handle_starttag(self, tag, attrs):
        if tag == self.list_type_tag:
            self.indent += 1
            return

        if tag == 'li':
            self.li_contents = []
            self.current_tag_is_li = True
            return

        if self.current_tag_is_li:
            self.li_contents.append(f'<{tag}>')

    def handle_endtag(self, tag):
        if tag == self.list_type_tag:
            self.indent -= 1
            return

        if tag == 'li':
            li_contents = ''.join(self.li_contents)
            li_tag_html = f'<li>{li_contents}</li>'
            soup = BeautifulSoup(li_tag_html, 'html.parser')
            tag = soup.find()
            contents = extract_from_tag(tag, self.processing_options, self.note_specific_tag_cleaning)
            if contents:
                list_item = self.list_item_type(self.processing_options, contents, self.indent)
                self.list_of_list_items.append(list_item)
                self.current_tag_is_li = False
                return

        if self.current_tag_is_li:
            self.li_contents.append(f'</{tag}>')

    def handle_data(self, data):
        if self.current_tag_is_li:
            self.li_contents.append(data)
