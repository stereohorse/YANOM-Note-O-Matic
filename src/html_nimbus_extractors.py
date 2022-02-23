import datetime
from pathlib import Path
from typing import Optional

import helper_functions
import html_data_extractors
from nimbus_note_content_data import EmbedNimbus, NimbusProcessingOptions
from nimbus_note_content_data import FileEmbedNimbusHTML, NimbusToggle
from nimbus_note_content_data import MentionFolder, MentionNote, MentionUser, MentionWorkspace
from nimbus_note_content_data import NimbusDateItem
from nimbus_note_content_data import TableCheckItem, TableCollaborator
from note_content_data import BlockQuote, BulletList, BulletListItem, Caption, Figure
from note_content_data import Checklist, ChecklistItem
from note_content_data import CodeItem
from note_content_data import HeadingItem, Paragraph
from note_content_data import Hyperlink
from note_content_data import NumberedList, NumberedListItem
from note_content_data import Outline, OutlineItem
from note_content_data import Table, TableItem, TableHeader, TableRow
from note_content_data import TextItem


def process_child_items(tag, processing_options: NimbusProcessingOptions):
    items = html_data_extractors.process_child_items(tag, processing_options, extract_from_nimbus_tag)
    return items


def extract_from_nimbus_tag(tag, processing_options: NimbusProcessingOptions):
    if tag.name == "div":
        data = extract_from_nimbus_div(tag, processing_options)
        if data:
            return data

    if tag.name == "ul":
        return extract_from_nimbus_unordered_lists(tag, processing_options)

    if tag.name == 'mention':
        return extract_from_nimbus_mention_tag(tag, processing_options)

    if tag.name == 'date':
        return extract_from_nimbus_date(tag, processing_options)

    if tag.name == 'span':
        if 'data-highlight' in tag.attrs:
            return extract_from_nimbus_highlight_span(tag, processing_options)

    if tag.name == 'nimbus-button':
        return extract_from_nimbus_inline_button(tag, processing_options)

    if tag.name == 'nimbus-html':
        return extract_from_nimbus_html_tag(tag, processing_options)

    return None


def extract_from_nimbus_div(div_tag, processing_options: NimbusProcessingOptions):
    if div_tag.get('class'):
        if 'hintblock' in div_tag['class']:
            return extract_from_hint_block(div_tag, processing_options)

        if 'image-wrapper' in div_tag['class']:
            return extract_from_nimbus_image_attachment(div_tag, processing_options)

        if 'attachment-caption' in div_tag['class']:
            return extract_from_nimbus_attachment_caption(div_tag, processing_options)

        if 'horizontal-line' in div_tag['class']:
            return TextItem(processing_options, '<hr>')

        if 'file-wrapper' in div_tag['class']:
            return extract_from_nimbus_file_embed(div_tag, processing_options)

        if 'table-wrapper' in div_tag['class']:
            return extract_from__nimbus_table(div_tag, processing_options)

        if 'syntax-wrapper' in div_tag['class']:
            return extract_from_nimbus_code_pre(div_tag, processing_options)

        if 'nimbus-toggle' in div_tag['class']:
            return extract_from_nimbus_toggle(div_tag, processing_options)

        if 'outline' in div_tag['class']:
            return extract_from_nimbus_outline(div_tag, processing_options)

        if 'nimbus-bookmark' in div_tag['class']:
            return extract_from_nimbus_bookmark(div_tag, processing_options)

        if 'button-single' in div_tag['class']:
            return extract_from_nimbus_button(div_tag, processing_options)

        if 'remote-frame-wrapper' in div_tag['class']:
            return extract_from_nimbus_embed(div_tag, processing_options)


def extract_from_hint_block(tag, processing_options: NimbusProcessingOptions):
    if tag.name != 'div' or not tag.get('class') or 'hintblock' not in tag['class']:
        return

    text_items = process_child_items(tag, processing_options)

    return BlockQuote(processing_options, text_items, '')


def extract_from_nimbus_highlight_span(tag, processing_options: NimbusProcessingOptions):
    if tag.name != 'span' or 'data-highlight' not in tag.attrs:
        return

    tag.name = 'mark'
    tag.attrs = {}
    return html_data_extractors.extract_from_tag(tag, processing_options)


def extract_from_nimbus_outline(div_tag, processing_options: NimbusProcessingOptions):
    if div_tag.name != 'div' or not div_tag.get('class') or 'outline' not in div_tag['class']:
        return

    ul_tag = div_tag.find('ul')
    outline_items = extract_from_nimbus_unordered_lists(ul_tag, processing_options)

    title_items = process_child_items(div_tag.find('div', class_='outline-name'), processing_options)

    return Outline(processing_options, title_items, outline_items)


def extract_from_nimbus_outline_items(outline_items, processing_options: NimbusProcessingOptions) -> NumberedList:
    outline_list = []
    for item in outline_items:
        if item.name == 'li' and item.get('class') and 'outline-list-item' in item['class']:
            class_list = item['class']
            for class_item in class_list:
                if "level" in class_item:
                    indent = int(''.join(filter(str.isdigit, class_item)))
                    inner_a_tag = item.find('a')
                    contents = inner_a_tag.text
                    link_id = inner_a_tag.attrs.get('href')
                    outline_text = TextItem(processing_options, contents)
                    outline_item = OutlineItem(processing_options, outline_text, indent, link_id)
                    outline_list.append(outline_item)
    if outline_list:
        return NumberedList(processing_options, outline_list)


def extract_from_nimbus_unordered_lists(unordered_list_tag, processing_options: NimbusProcessingOptions):
    if unordered_list_tag.name != 'ul':
        return

    list_items = unordered_list_tag.find_all('li')
    if list_items and list_items[0].get('class'):
        if 'list-item-bullet' in list_items[0]['class']:
            list_data = extract_from_nimbus_bullet_list(list_items, processing_options)
            return list_data

        if 'list-item-number' in list_items[0]['class']:
            list_data = extract_from_nimbus_numbered_list(list_items, processing_options)
            return list_data

        if 'list-item-checkbox' in list_items[0]['class']:
            list_data = extract_from_nimbus_checklist(list_items, processing_options)
            return list_data

        if 'outline-list-item' in list_items[0]['class']:
            list_data = extract_from_nimbus_outline_items(list_items, processing_options)
            return list_data


def extract_from_nimbus_embed(div_tag, processing_options: NimbusProcessingOptions):
    """"Extract embedded HTML contents such as iframes and twitter blockquotes."""

    def extract_embed_block_quote_if_present():
        """
        Inner function to extract a block quote and caption from an embed div.
        A twitter block quote repeats itself twice in nimbus html so using the above blockquote extractor. This also
        result  int the contents being indented as a blockquote like a twitter tweet does.

        """
        embed_content_tag = div_tag.find('blockquote')
        if embed_content_tag:
            data = html_data_extractors.extract_from_blockquote(embed_content_tag, processing_options)
            # NOTE the exported remote frame and iframe work using process_child items
            # but a twitter block quote repeats itself twice in nimbus html so using the above blockquote extractor.
            # This also indents the contents as a blockquote like a twitter tweet does

            # and because we have extracted just the blockquote we need to now try and get the caption
            try:
                caption_items = extract_from_nimbus_attachment_caption(div_tag.find('div', class_='attachment-caption'),
                                                                       processing_options)
            except AttributeError:
                # all is OK just no caption data asking for forgiveness approach we make an empty entry
                caption_items = Caption(processing_options, [TextItem(processing_options, '')])

            if data:
                return EmbedNimbus(processing_options, data, caption_items)

    if not div_tag.name == 'div' or not div_tag.get('class') or 'remote-frame-wrapper' not in div_tag['class']:
        return

    # blockquotes appear to have the data repeated twice so using a separate function to handle those embeds
    found_blockquote = extract_embed_block_quote_if_present()
    if found_blockquote:
        return found_blockquote

    # for other embeds just use child items to extract the contents
    return process_child_items(div_tag, processing_options)


def extract_from_nimbus_button(div_tag, processing_options: NimbusProcessingOptions):
    if not div_tag.name == 'div' or not div_tag.get('class') or 'button-single' not in div_tag['class']:
        return

    button_tag = div_tag.find('nimbus-button')
    if button_tag:
        # set class to inline-button to reuse the inline-button extract
        button_tag.attrs['class'] = ['inline-button']
        hyperlink = extract_from_nimbus_inline_button(button_tag, processing_options)
        return Paragraph(processing_options, [hyperlink])
        # returns hyperlink wrapped in Paragraph as button-single are alone on a line


def extract_from_nimbus_inline_button(tag, processing_options: NimbusProcessingOptions):
    if not tag.name == 'nimbus-button' or not tag.get('class') or 'inline-button' not in tag['class']:
        return

    display_text = tag.text
    url = tag['data-url']
    return Hyperlink(processing_options, display_text, url)


def extract_from_nimbus_bookmark(tag, processing_options: NimbusProcessingOptions):
    if tag.name != 'div' or not tag.get('class') or 'nimbus-bookmark' not in tag['class']:
        return

    a_tag = tag.find('a')
    items = []
    if a_tag:
        href = a_tag['href']
        text_tag = tag.find('div', class_='nimbus-bookmark__info__name')
        display_text = text_tag.text
        link_object = Hyperlink(processing_options, display_text, href)
        items.append(link_object)

        description_tag = tag.find('div', class_="nimbus-bookmark__info__desc")
        if description_tag:
            description_object = TextItem(processing_options, description_tag.text)
            items.append(description_object)

        image_div_tag = tag.find("div", class_="nimbus-bookmark__preview")
        if image_div_tag:
            image_tag = image_div_tag.find('img')
            if image_tag:
                image_data_object = html_data_extractors.extract_from_img_tag(image_tag, processing_options)
                image_data_object.width = "280"  # match max width size in nimbus css
                items.append(image_data_object)

        return Paragraph(processing_options, items)
        # returns hyperlink wrapped in Paragraph as div bookmarks appear to be buttons alone on a line


def extract_from_nimbus_toggle(tag, processing_options: NimbusProcessingOptions) -> Optional[NimbusToggle]:
    if tag.name != 'div' or not tag.get('class') or 'nimbus-toggle' not in tag['class']:
        return

    list_items = []

    # process header toggle
    toggle_header = tag.find('div', class_='nimbus-toggle-header')
    header_text_items = process_child_items(toggle_header, processing_options)
    if header_text_items:
        list_items.append(HeadingItem(processing_options, header_text_items, 2, ''))

    toggle_content_tag = tag.find('div', class_='nimbus-toggle-content')
    toggle_items = process_child_items(toggle_content_tag, processing_options)
    if toggle_items:
        list_items = helper_functions.merge_iterable_or_item_to_list(list_items, toggle_items)

    if list_items:
        return NimbusToggle(processing_options, list_items)


def extract_from_nimbus_mention_span(span_tag, processing_options: NimbusProcessingOptions):
    if span_tag.name != 'span' or 'data-mention-type' not in span_tag.attrs:
        return

    return extract_from_mention_items(span_tag, processing_options)


def extract_from_nimbus_mention_tag(mention_tag, processing_options: NimbusProcessingOptions):
    if mention_tag.name != 'mention':
        return

    return extract_from_mention_items(mention_tag, processing_options)


def extract_from_mention_items(mention_tag, processing_options: NimbusProcessingOptions):
    mention_type = mention_tag.get('data-mention-type', None)
    if not mention_type:
        return

    contents = mention_tag.get('data-mention-name', '')

    if mention_type == 'user':
        return MentionUser(processing_options, contents)

    if mention_type == 'workspace':
        mention_workspace_id = mention_tag.get('data-mention-object_id', '')
        return MentionWorkspace(processing_options, contents, mention_workspace_id)

    if mention_type == 'folder':
        mention_workspace_id = mention_tag.get('data-mention-workspace_id', '')
        mention_folder_id = mention_tag.get('data-mention-object_id', '')
        return MentionFolder(processing_options, contents, mention_workspace_id, mention_folder_id)

    if mention_type == 'note':
        mention_workspace_id = mention_tag.get('data-mention-workspace_id', '')
        mention_note_id = mention_tag.get('data-mention-object_id', '')
        return MentionNote(processing_options, contents, mention_workspace_id, mention_note_id)


def extract_from_nimbus_date(date_tag, processing_options: NimbusProcessingOptions):
    if date_tag.name != 'date':
        return

    unix_time_seconds = int(date_tag['data-date-timestamp']) / 1000
    string_time = datetime.datetime.fromtimestamp(unix_time_seconds).strftime('%Y-%m-%d %H:%M:%S')
    return NimbusDateItem(processing_options, string_time, unix_time_seconds)


def extract_from_nimbus_code_pre(div_tag, processing_options: NimbusProcessingOptions):
    if div_tag.name != 'div' or not div_tag.get('class') or 'syntax-wrapper' not in div_tag['class']:
        return

    syntax_tag = div_tag.find('syntax')
    if not syntax_tag:
        return

    language = syntax_tag.get('data-nimbus-language', "")

    pre_tag = div_tag.find('pre')
    if not pre_tag:
        return
    code = pre_tag.text

    return CodeItem(processing_options, code, language)


def extract_from_nimbus_file_embed(div_tag, processing_options: NimbusProcessingOptions):
    """Extra file link from nimbus html including it's original file name"""
    if div_tag.name != 'div':
        return

    a_tag = div_tag.find('a')
    if not a_tag:
        return

    link_href = a_tag.get('href', '')

    try:  # use try except as 99.9% of time will be there.. probably.. anyway using ask for forgiveness approach
        filename_part = a_tag.find('span', class_='file-name-main').text
    except AttributeError:
        # if the file name parts are not in html use the parts of the href filename
        # it is the name of the file in the zip file
        filename_part = f"{Path(link_href).stem}."

    try:
        extension_part = a_tag.find('span', class_='file-name-ext').text
    except AttributeError:
        extension_part = str(Path(link_href).suffix).lstrip('.')

    dirty_filename = f"{filename_part}{extension_part}"
    # if filename parts were mot present, and so dirty filename is '' the clean file name will be a random string
    clean_filename = helper_functions.generate_clean_filename(dirty_filename, processing_options.filename_options)

    caption_text = get_caption_text(div_tag, processing_options)

    return FileEmbedNimbusHTML(processing_options, caption_text, link_href, clean_filename)


def extract_from_nimbus_attachment_caption(div_tag, processing_options: NimbusProcessingOptions):
    if div_tag.name != 'div':
        return

    if div_tag.text == '':
        # catches captions that are empty and just have <br> in them
        return Caption(processing_options, [TextItem(processing_options, '')])

    text_items = process_child_items(div_tag, processing_options)

    return Caption(processing_options, text_items)


def extract_from_nimbus_image_attachment(div_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data from a nimbus image attachment.

    Priority is given to width and height in a style parameter over the <img> tag if the style is present.

    Parameters
    ----------
    div_tag : BeautifulSoup Tag
        div tag to be analysed
    processing_options : NimbusProcessingOptions
        Processing options for this note conversion

    Returns
    -------
    ImageAttachmentNimbusHtml or None
        If the div tag provided is not value for the extraction None is returned, else an instance of
        ImageAttachmentNimbusHtml is returned
    """
    if div_tag.name != 'div':
        return

    img_tag = div_tag.find('img')
    if not img_tag:
        return

    image_object = html_data_extractors.extract_from_tag(img_tag, processing_options)
    if image_object:
        width, height = get_with_and_height_from_nimbus_tag(div_tag)

        if width:
            image_object.width = width
        if height:
            image_object.height = height

    caption_object = get_caption_text(div_tag, processing_options)

    return Figure(processing_options, (image_object, caption_object))


def get_with_and_height_from_nimbus_tag(div_tag):
    width = ''
    height = ''

    try:
        style_tag = div_tag.find('div', class_='resize-container disabled-resize')
        style_list = style_tag.get('style').replace('px;', '').replace(':', '').split()
        style_dict = {}

        # build dict from list where each 2 items in the list are a key and value
        for i in range(0, len(style_list), 2):
            style_dict[style_list[i]] = style_list[i + 1]

        width = str(int(float(style_dict.get('width'))))
        height = str(int(float(style_dict.get('height'))))

    except AttributeError:
        pass  # is OK can continue just no width and height form style

    return width, height


def get_caption_text(div_tag, processing_options):
    try:
        if div_tag.get('class') and 'attachment-caption' in div_tag['class']:
            tag_to_use = div_tag
        else:
            tag_to_use = div_tag.find('div', class_='attachment-caption')

        caption_text = extract_from_nimbus_attachment_caption(tag_to_use, processing_options)

    except AttributeError:
        caption_text = Caption(processing_options, [TextItem(processing_options, '')])

    return caption_text


def extract_from__nimbus_table(div_tag, processing_options: NimbusProcessingOptions) -> Table:
    """
    Extract data from nimbus note html table and return a Table object containing the data.

    The nimbus HTML table includes 123 ABC row and column headers like a spreadsheet and these can be included in the
    data extracted or ignored based on the keep_abc_123_columns value passed within the processing_option parameter.

        Parameters
        ==========
        div_tag : BeautifulSoup div tag
            tag being analysed
        processing_options : NimbusProcessingOptions
            NimbusProcessingOptions object containing processing options for nimbus HTML conversion.  The key value of
            interest in the processing options for this function is processing_options.keep_abc_123_columns

        returns
        =======
        Table :
            Table object.  With list of TableHeader and TableRow objects, each of which will contain a list of
            TableItems.

        """

    keep_abc_123_columns = processing_options.keep_abc_123_columns

    table = Table(processing_options, [])
    header_data = []
    row_data = []

    rows = div_tag.find_all('tr')

    for row_number, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        if row_number == 0 and keep_abc_123_columns:
            header_data.extend(extract_from_123abc_table_header_row(cells, processing_options))
        elif row_number == 1 and not keep_abc_123_columns:  # treat first row as header
            cell_data = extract_from_table_row(cells, processing_options)
            header_data.extend(cell_data)
        elif row_number > 0:
            cell_data = extract_from_table_row(cells, processing_options)
            row_data.extend(cell_data)

        if header_data:
            table.contents.append(TableHeader(processing_options, header_data))
            header_data = []
        if row_data:
            table.contents.append(TableRow(processing_options, row_data))
            row_data = []

    return table


def extract_from_123abc_table_header_row(cells, processing_options):
    """
    If 123 and ABC row and columns headers are to be kept extract and return the ABC row

    Parameters
    ----------
    cells : list[Tag]
        lost of <th> tags form a nimbus html table.  No check is made that the provided tags are <th> tags
    processing_options : NimbusProcessingOptions
        processing settings for the current conversion

    Returns
    -------
    list
        list of TableItem objects
    """
    skip_next = False
    data = []
    for cell in cells:
        if skip_next:
            skip_next = False
            continue

        if cell.get('class') and 'table-head-start' in cell['class']:
            skip_next = True

            # append an empty cell where numbers and letters row/columns meet
            data.append(TableItem(processing_options, [TextItem(processing_options, '')]))

            continue

        header_div = cell.find('div', class_="item-title")
        cell_text = process_child_items(header_div, processing_options)

        data.append(TableItem(processing_options, cell_text))

    return data


def extract_from_table_row(cells, processing_options):
    keep_abc_123_columns = processing_options.keep_abc_123_columns
    skip_next = False
    data = []
    for cell in cells:
        if skip_next:
            skip_next = False
            continue

        # if cell.name == 'td':
        if cell.get('class'):
            if 'table-head-item' in cell['class']:
                skip_next = True
                if not keep_abc_123_columns:
                    continue
            if 'add-row' in cell['class']:
                break

        table_check_item = extract_from_nimbus_table_check_item(cell, processing_options)
        if table_check_item:
            data.append(table_check_item)
            continue

        table_select_item = extract_from_nimbus_table_select_item(cell, processing_options)
        if table_select_item:
            data.append(table_select_item)
            continue

        table_mention_item = extract_from_nimbus_table_mention_item(cell, processing_options)
        if table_mention_item:
            data.append(table_mention_item)
            continue

        table_collaboration_item = extract_from_nimbus_table_collaboration_item(cell, processing_options)
        if table_collaboration_item:
            data.append(table_collaboration_item)
            continue

        table_date_item = extract_from_nimbus_table_date_item(cell, processing_options)
        if table_date_item:
            data.append(table_date_item)
            continue

        table_cell_hyperlink = extract_from_nimbus_table_hyperlink_item(cell, processing_options)
        if table_cell_hyperlink:
            data.append(table_cell_hyperlink)
            continue

        table_cell_rating = extract_from_nimbus_table_rating_item(cell, processing_options)
        if table_cell_rating:
            data.append(table_cell_rating)
            continue

        table_cell_progress_bar = extract_from_nimbus_table_progress_item(cell, processing_options)
        if table_cell_progress_bar:
            data.append(table_cell_progress_bar)
            continue

        cell_text = extract_from_nimbus_table_text_item(cell, processing_options)
        if cell_text:
            data.append(TableItem(processing_options, cell_text))
            continue

        # handle empty cells <td></td> or unrecognised cells e.g. table-attachements are currently there but
        # have no content
        # <td class="cell-attachment"><div class="table-attachment-wrap"><div><div class="table-attachment">
        # <div class="attachment-item"></div></div></div></div></td>
        data.append(TableItem(processing_options, [TextItem(processing_options, '')]))

    return data


def extract_from_nimbus_table_text_item(cell_tag, processing_options: NimbusProcessingOptions):
    if cell_tag.name != 'td':
        return

    cell_div = cell_tag.find('div', class_='table-text-common')
    if cell_div:
        cell_text = process_child_items(cell_div, processing_options)
        if not cell_text:  # is empty cell
            cell_text = [TextItem(processing_options, '')]

        return cell_text

    # item-title is used for ABC and 123 column and row label entries
    cell_div = cell_tag.find('div', class_='item-title')
    if cell_div:
        cell_text = [TextItem(processing_options, cell_div.text)]
        return cell_text


def extract_from_nimbus_table_progress_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus table progress item.
    Nimbus HTML uses a <span> tag and tag class to specify the progress as a text value.  Returns a Hyperlink object
    in a TableItem wrapper

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    Returns
    =======
    TableItem
        TextItem object in a TableItem wrapper

    """
    if cell_tag.name != 'td':
        return

    progress_span = cell_tag.find('span', class_="progress-value")
    if progress_span:
        progress_text = f'Progress {progress_span.text}'
        return TableItem(processing_options, [TextItem(processing_options, progress_text)])


def extract_from_nimbus_table_rating_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus table rating item.
    Nimbus HTML uses a <span> tag and tag class to specify each star in the rating. Count the number of active stars
    and return a rating string.  Returns a Hyperlink object in a TableItem wrapper

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    Returns
    =======
    TableItem
        Hyperlink object in a TableItem wrapper

    """
    if cell_tag.name != 'td':
        return

    active_stars = cell_tag.find_all('span', class_="rating-active")
    if active_stars:
        rating_text = f'Rating {len(active_stars)}/5 stars'
        return TableItem(processing_options, [TextItem(processing_options, rating_text)])


def extract_from_nimbus_table_hyperlink_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus table hyperlink item.
    Nimbus HTML uses a tag class to specify a the date item. Returns a Hyperlink object in a TableItem wrapper

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    Returns
    =======
    TableItem
        Hyperlink object in a TableItem wrapper

    """
    if cell_tag.name != 'td':
        return

    a_tag_search = cell_tag.find_all('a')
    if a_tag_search:
        a_tag = a_tag_search[0]
        hyperlink = html_data_extractors.extract_from_hyperlink(a_tag, processing_options)
        return TableItem(processing_options, [hyperlink])


def extract_from_nimbus_table_date_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus table date item.
    Nimbus HTML uses a tag class to specify a the date item. Returns a text as a TextItem in a TableItem wrapper

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    Returns
    =======
    TableItem
        Date text as a TextItem in a TableItem wrapper

    """
    if cell_tag.name != 'td':
        return

    span_tag = cell_tag.find('span', class_="input-date-text")
    if not span_tag:
        return

    return TableItem(processing_options, [TextItem(processing_options, span_tag.text)])


def extract_from_nimbus_table_collaboration_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus table collaboration item.
    Nimbus HTML uses a  tag class to specify a collaboration item. Returns a text as a TextItem in a TableItem wrapper

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    Returns
    =======
    TableItem
        collaboration text as a TextItem in a TableItem wrapper

    """
    if cell_tag.name != 'td':
        return

    span_tag = cell_tag.find('span', class_="collaborate-item")
    if not span_tag:
        return

    return TableItem(processing_options, [TableCollaborator(processing_options, span_tag["data-mention-name"])])


def extract_from_nimbus_table_mention_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus table mention item.
    Nimbus HTML uses a  tag class to specify a mention item. Returns a text as a TextItem in a TableItem wrapper

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    Returns
    =======
    TableItem
        Mention text as a TextItem in a TableItem wrapper
    """
    if cell_tag.name != 'td':
        return

    def span_has_data_mention_type(tag):
        return tag.has_attr('data-mention-type')

    if cell_tag.get('class') and 'cell-mention' in cell_tag.attrs['class']:

        # NOTE here passing function to find so we can get the correct tag with out iterating all the spans
        # to find the right one.
        mention_tag = cell_tag.find(span_has_data_mention_type)

        if not mention_tag:
            return

        mention_item = extract_from_nimbus_mention_span(mention_tag, processing_options)

        return TableItem(processing_options, [mention_item])


def extract_from_nimbus_table_select_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus table select item.
    Nimbus HTML uses a  tag class to specify a select item. Returns a text as a TextItem in a TableItem wrapper

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    Returns
    =======
    TableItem
        Select text as a TextItem in a TableItem wrapper

    """
    if cell_tag.name != 'td':
        return

    span_tags = cell_tag.find_all('span', class_="select-label-text")
    if not span_tags:
        return

    cell_text = ''
    for span in span_tags:
        cell_text = f"{cell_text}{span.text} "

    cell_text = cell_text.strip()
    return TableItem(processing_options, [TextItem(processing_options, cell_text)])


def extract_from_nimbus_table_check_item(cell_tag, processing_options: NimbusProcessingOptions):
    """
    Extract data form a Nimbus Table check item.
    Nimbus HTML uses a  tag class to specify a check item and a second class for it's checked status within a
    <span> tag.  Returns a TableCheckItem

    Parameters
    ==========
    processing_options : NimbusProcessingOptions
        Processing options for nimbus html conversion
    cell_tag : beautiful soup <td> tag object

    """
    if cell_tag.name != 'td':
        return

    span_tag = cell_tag.find('span', class_="checkbox-component")
    if span_tag:
        if 'checked' in span_tag['class']:
            return TableCheckItem(processing_options, True)

        return TableCheckItem(processing_options, False)


def extract_from_nimbus_bullet_list(bullet_list_tags, processing_options: NimbusProcessingOptions):
    """
    Return a BulletList instance containing BulletListItems.

    The provided list of bullet list tag items are expected to be <li> tags and no check is made to confirm this.
    Each tag is processed and infomration extracted and a BulletListItem instance is used to store the data.

    Parameters
    ----------
    bullet_list_tags : list[Tag]
        lost of <li> tags form a nimbus bullet list .  No check is made that the provided tags are <li> tags
    processing_options : NimbusProcessingOptions
        processing settings for the current conversion

    Returns
    -------
    BulletList
        containing BulletListItems for each of the provided tags

    """

    list_items = []
    for tag in bullet_list_tags:
        if tag.get('class'):
            class_list = tag['class']
            for class_item in class_list:
                if "indent" in class_item:
                    indent = int(''.join(filter(str.isdigit, class_item)))
                    contents = process_child_items(tag, processing_options)
                    list_items.append(BulletListItem(processing_options, contents, indent))
                    break

    return BulletList(processing_options, list_items)


def extract_from_nimbus_numbered_list(numbered_list_items, processing_options: NimbusProcessingOptions):
    numbered_list = []
    for item in numbered_list_items:
        if item.get('class'):
            class_list = item['class']
            for class_item in class_list:
                if "indent" in class_item:
                    indent = int(''.join(filter(str.isdigit, class_item)))
                    contents = process_child_items(item, processing_options)
                    numbered_list.append(NumberedListItem(processing_options, contents, indent))

    return NumberedList(processing_options, numbered_list)


def extract_from_nimbus_checklist(checklist_items, processing_options: NimbusProcessingOptions):
    check_items_list = []
    current_indent = 0
    checked_status = False
    for item in checklist_items:
        if item.get('class'):
            class_list = item['class']
            for class_item in class_list:
                if "indent" in class_item:
                    current_indent = int(''.join(filter(str.isdigit, class_item)))
            if item.get('data-checked'):
                checked_status = helper_functions.string_to_bool(item['data-checked'])
            contents = process_child_items(item, processing_options)
            check_items_list.append(ChecklistItem(processing_options, contents, current_indent, checked_status))

    return Checklist(processing_options, check_items_list)


def extract_from_nimbus_html_tag(tag, processing_options: NimbusProcessingOptions):
    return process_child_items(tag, processing_options)
