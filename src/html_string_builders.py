from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, Union
from typing import Dict, List


if TYPE_CHECKING:  # avoid circular import error for Typing pragma: no cover
    from note_content_data import Caption, ImageAttachment, NoteData, NumberedList  # pragma: no cover

import helper_functions


def head(contents):
    head_lead = """<head>"""
    head_tail = """<style>
    table, th, td {
      border: 1px solid black;
      border-collapse: collapse;
    }
    </style></head>"""
    head_tags = join_multiple_items_of_html(contents)

    return f'{head_lead}{head_tags}{head_tail}'


def join_multiple_items_of_html(contents: List, join_character: str = ''):
    strings = [item.html() for item in contents]

    return join_character.join(strings)


def wrap_string_in_tag(string, tag: str):
    return f'<{tag}>{string}</{tag}>'


def wrap_items_in_tag(items: List, tag_name: str):
    html_text = ""
    for item in items:
        html_text = f"{html_text}{item.html()}"

    if not html_text:  # If could end with empty tag just return empty string
        return ""

    html_text = f"<{tag_name}>{html_text}</{tag_name}>"

    return html_text


def table_of_contents(title_contents: List[NoteData], items: NumberedList):
    title = join_multiple_items_of_html(title_contents)
    title = wrap_string_in_tag(title, 'h2')
    outline_items = items.html()
    outline_items = wrap_string_in_tag(outline_items, 'h4')

    return f'{title}{outline_items}'


def heading(contents: List, heading_id, heading_level: int):
    id_text = f' id="{heading_id}"' if heading_id else ''
    heading_text = join_multiple_items_of_html(contents)

    return f"<h{heading_level}{id_text}>{heading_text}</h{heading_level}>"


def anchor_link(contents: NoteData, link_id: str):
    return f'<a href="{link_id}">{contents.html()}</a>'


def hyperlink(contents: Union[str, NoteData], target_path):
    display_text = contents if isinstance(contents, str) else contents.html()
    path = str(target_path) if target_path else ''
    return f'<a href="{path}">{display_text}</a>'


def checklist_item(contents: List[NoteData], checked: bool, indent: int):
    styling = f' style= "padding-left: {indent * 30}px;"' if indent else ''
    checked = ' checked' if checked else ''
    item_text = join_multiple_items_of_html(contents)

    return f'<p{styling}><input{checked} type="checkbox">{item_text}</p>'


def image_tag(contents: str, width, height, target_path):
    tag_width = f' width="{width}"' if width else ''
    tag_height = f' height="{height}"' if height else ''
    tag_alt = f' alt="{contents}"' if contents else ''
    tag_src = f'src="{target_path}"' if target_path else 'src=""'

    return f'<img {tag_src}{tag_alt}{tag_width}{tag_height}>'


def pre_code_block(contents: str, language: str):
    if language:
        return f'<pre data-{language}>{contents}</pre>'

    return f'<pre>{contents}</pre>'


def line_break():
    return '<br>'


def block_quote(contents, citation):
    html_citation = f' cite="{citation}"' if citation else ''
    item_text = join_multiple_items_of_html(contents)

    return f'<blockquote{html_citation}>{item_text}</blockquote>'


def meta_tags_from_dict(contents: Dict):
    meta_text = ''
    for key, value in contents.items():
        content = str(value)
        if isinstance(value, list):
            content = ", ".join(value)
        meta_text = f'{meta_text}<meta name="{key}" content="{content}"/>'

    return meta_text


def format_text(contents: List, text_format: str):
    text = join_multiple_items_of_html(contents)
    leading_whitespace, body_text, trailing_whitespace = helper_functions.separate_whitespace_from_text(text)
    html_text = f"{leading_whitespace}<{text_format}>{body_text}</{text_format}>{trailing_whitespace}"

    return html_text


def build_table_row(items: List[NoteData], row_item_type: str):
    row_html = f"<tr>"

    for item in items:
        row_html = f"{row_html}<{row_item_type}>{item.html()}</{row_item_type}>"

    return f"<tr>{row_html}</tr>"


def generate_html_list(list_items, ordered=False):
    """
    Create a new cleaned ordered or <ol> or unordered list <ul> from the provided list of items and return it.

    Generate a <li> tag for each item and add it to a new <ul> or <ol> tag.  Indentation is managed through additional
    <ul> <ol> tags to create nested lists to achieve clean html indented lists.  The <ul> or <ol> tag is returned.

    Parameters
    ==========
    list_items : list
        List of items of Type NoteData such as BulletListItems or NumberedListItems, that make up the items of an
        unordered list.
    ordered : bool
        If True return ordered list, (numbered list <ol> tag), if False return unordered list <ul> tag.

    Returns
    =======
    str
        The list items as a formatted html string.

    """
    open_list = '<ul>'
    close_list = '</ul>'
    if ordered:
        open_list = '<ol>'
        close_list = '</ol>'

    last_indent = 0

    list_string = open_list
    for item in list_items:

        indent = item.indent

        if indent == last_indent:
            list_string = f"{list_string}{item.html()}"
            continue

        if indent > last_indent:
            list_string = f"{list_string}{open_list * (indent - last_indent)}"
            list_string = f"{list_string}{item.html()}"
            last_indent = indent
            continue

        # indent must be < last_indent:
        list_string = f"{list_string}{close_list * (last_indent - indent)}"
        list_string = f"{list_string}{item.html()}"
        last_indent = indent

    list_string = f"{list_string}{close_list * (last_indent + 1)}"

    return list_string


def figure(contents: Tuple[ImageAttachment, Caption]):
    image_tag_html = ''
    caption_html = ''
    if contents[0]:
        image_tag_html = contents[0].html()

    if contents[1]:
        caption_html = contents[1].html()

    if caption_html:
        return f'<figure>' \
               f'{image_tag_html}' \
               f'<figcaption>{caption_html}</figcaption>' \
               f'</figure>'

    return image_tag_html
