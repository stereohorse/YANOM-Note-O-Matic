from __future__ import annotations
import itertools
from pathlib import Path
from typing import List
from typing import TYPE_CHECKING


if TYPE_CHECKING:  # avoid circular import error for Typing  pragma: no cover
    from note_content_data import TextItem  # pragma: no cover

import helper_functions
from markdown_format_styling import format_styling
from processing_options import ProcessingOptions


def embed_image(processing_options: ProcessingOptions, alt_text, width, height, target_path):
    md_embed_symbol = ''
    md_alt_text = f' alt="{alt_text.strip()}"' if alt_text else ''
    md_width = f' width="{width}"' if width else ''
    md_height = f' height="{height}"' if height else ''

    if md_height or md_width:
        md_target_path = f'<img src="{str(target_path)}"' if target_path else f'<img src=""'
        return f'{md_target_path}{md_alt_text}{md_width}{md_height}>\n'

    if target_path and target_path.suffix.lstrip('.') in processing_options.embed_files.images:
        md_embed_symbol = '!'

    md_target_path = str(target_path) if target_path else ''
    return f"{md_embed_symbol}[{alt_text.strip()}]({md_target_path})\n"


def embed_file(processing_options: ProcessingOptions,
               alt_text: str,
               target_path: Path,
               caption: str = ''
               ):

    md_embed_symbol = ''
    md_alt_text = alt_text.strip() if alt_text else ''
    md_target_path = str(target_path) if target_path else ''
    md_caption = f"*{caption.strip()}*\n" if caption else ''

    embed_types = [*processing_options.embed_files.documents,
                   *processing_options.embed_files.audio,
                   *processing_options.embed_files.video]

    if target_path and target_path.suffix.lstrip('.') in embed_types:
        md_embed_symbol = '!'

    return f"{md_embed_symbol}[{md_alt_text}]({md_target_path})\n{md_caption}"


def link(contents, target_path):
    display_text = contents if isinstance(contents, str) else contents.markdown()
    md_target_path = str(target_path) if target_path else ''
    return f"[{display_text.strip()}]({md_target_path})"


def mail_to_link(email_address):
    if helper_functions.is_valid_email(email_address):
        return f"Mention [{email_address}](mailto:{email_address})"

    return f"Mention {email_address}"


def join_multiple_items(contents: List, join_character: str = ''):
    strings = [item.markdown() for item in contents]
    return join_character.join(strings)


def heading(items: List, level: int):
    heading_character = '#'
    heading_text = join_multiple_items(items)
    return f"{heading_character * level} {heading_text}\n"


def escape_leading_number_if_required(item_text):
    int_part = "".join(itertools.takewhile(str.isdigit, item_text))

    if int_part and item_text[len(int_part)] == '.':
        escaped_number = f"{int_part}\\."
        rest_of_text = item_text.lstrip(f"{int_part}.")
        item_text = f"{escaped_number}{rest_of_text}"

    return item_text


def bullet_item(contents, indent_level):
    item_text = join_multiple_items(contents)
    item_text = escape_leading_number_if_required(item_text)
    tab = '\t'

    return f"{tab * indent_level}- {item_text}"


def bullet_list(contents):
    bullet_list_text = join_multiple_items(contents, '\n')

    return f'{bullet_list_text}\n\n'


def checklist(contents):
    return bullet_list(contents)


def numbered_list(contents):
    text = ""
    last_level_numbers = {int: int}  # key = indentation level, value = last number item used
    last_level = -1
    for item in contents:
        current_level = item.indent
        if current_level > last_level:
            last_level_numbers[current_level] = 0
        current_number = last_level_numbers.get(item.indent, 0) + 1
        last_level = current_level
        last_level_numbers[current_level] = current_number

        tab = '\t'
        text = f"{text}{tab * item.indent}{current_number}. {item.markdown()}\n"

    return text


def markdown_anchor_tag_link(contents: TextItem):
    text = contents.markdown().strip()

    link_text = text.replace(' ', '-')
    link_text = f"(#{link_text.lower()})"
    return f"[{text}]{link_text}"


def checklist_item(contents: List, checked: bool, indent):
    tab = '\t'
    checked = 'x' if checked else ' '

    item_text = join_multiple_items(contents)

    item_text = escape_leading_number_if_required(item_text)

    return f"{tab * indent}- [{checked}] {item_text}"


def numbered_list_item(contents):
    item_text = join_multiple_items(contents)
    item_text = escape_leading_number_if_required(item_text)

    return item_text


def pipe_table_header(contents):
    # Note make sure there is at least one line break above table
    header_line = f'\n|{join_multiple_items(contents, "|")}|\n'
    header_section = '--|'

    return f"{header_line}|{header_section * len(contents)}\n"


def pipe_table_row(contents):
    return f'|{join_multiple_items(contents, "|")}|\n'


def code_block(contents, language):
    return f"```{language}\n{contents}\n```\n"


def block_quote(contents, citation):
    cite_text = f'\n[source]({citation})' if citation else ''
    item_text = join_multiple_items(contents)

    return f"> {item_text}{cite_text}\n"


def formatted_text(contents, text_format):
    leading_tag = format_styling[text_format].leading_tag
    trailing_tag = format_styling[text_format].trailing_tag

    markdown_text = join_multiple_items(contents)

    leading_whitespace, body_text, trailing_whitespace = helper_functions.separate_whitespace_from_text(markdown_text)
    markdown_text = f"{leading_whitespace}{leading_tag}{body_text}{trailing_tag}{trailing_whitespace}"

    return markdown_text


def caption(contents: list):
    return f'*{join_multiple_items(contents)}*\n\n'

