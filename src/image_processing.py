import base64
import logging
import re
from typing import Optional

import cairosvg
from bs4 import BeautifulSoup

import config
import helper_functions


def what_module_is_this():
    return __name__


logger = logging.getLogger(f'{config.yanom_globals.app_name}.{what_module_is_this()}')


def clean_html_image_tag(tag, src_path=None):
    """
    Generate a clean tag object attrs dictionary

    Process the tag object to retrieve alt text, width and src if present.  If a value for src_path is not
    provided the src in the tag will be used, else src_path is used.
    If the img tag does not contain alt or width they will not be in the returned dict. If src is missing
    and src_path is not provided src is set to "".
    then and return a attrs dictionary with only the values for these 3 items that can be used to update the tag.

    Parameters
    ==========
    tag : bs4.Tag
        img tag to be processed for data
    src_path : str
        path to the image content if not provided the src from the img tag will be used

    Returns
    =======
    dict : attrs dict that can be used to replace an existing attrs dictionary of an img tag - "tag.attrs = new_attrs"

    """
    if not src_path:
        src_path = tag.attrs.get('src', "")

    src_path = helper_functions.path_to_posix_str(src_path)
    new_attrs = {'src': src_path}

    if 'width' in tag.attrs:
        new_attrs['width'] = tag.attrs['width']

    if 'height' in tag.attrs:
        new_attrs['height'] = tag.attrs['height']

    if 'alt' in tag.attrs:
        clean_alt = tag.attrs['alt']
        clean_alt = clean_alt.replace('[', '')
        clean_alt = clean_alt.replace(']', '')
        new_attrs['alt'] = clean_alt

    return new_attrs


def generate_obsidian_image_markdown_link(tag) -> Optional[str]:
    """
    Generate an obsidian image markdown link string.

    Use the values in the tag.attrs dict to populate a obsidian image link and return as a string.  The source path
    in the returned link is formatted as a posix path (forward slashes).

    Parameters
    ==========
    tag : bs4.Tag
        an img tag element

    Returns
    =======
    str : if width in html tag returns obsidian markdown formatted image link
    None : if width is not in the image tag - no need to format for obsidian

    """
    width = tag.attrs.get('width', '')
    if not width:
        return

    height = tag.attrs.get('height', '')

    alt = tag.attrs.get('alt', '')
    alt = alt.replace('[', '')
    alt = alt.replace(']', '')
    src = tag.attrs.get('src', '')
    src = helper_functions.path_to_posix_str(src)

    height_string = ''
    if height:
        height_string = f'x{height}'

    with_and_height = f'{width}{height_string}'
    obsidian_img_tag_markdown = f'![{alt}|{with_and_height}]({src})'

    return obsidian_img_tag_markdown


def replace_obsidian_image_links_with_html_img_tag(content: str) -> str:
    """
    Reformat obsidian markdown formatted image links to markdown html img tag format in the provided content.

    The string provided is analysed, the source is formatted as a posix path and a html img tag string is generated.

    ![Some alt text|600x300](my_image.gif)
    becomes
    <img src="my_image.gif" alt="Some alt text" width="600" height="300" />

    Tags that are not obsidian formatted - so do not contain '|width' or '|widthxheight' will not be changed

    Parameters
    ==========
    content :  str
        Markdown content

    Returns
    =======
    str
        Updated content with replaced image links

    """
    image_tag_lines = find_image_tag_lines(content)

    while image_tag_lines:
        for image_tag_line in image_tag_lines:
            image_tags = re.findall(r'!\[.*?\|.*?]\(.*?\)', image_tag_line)

            # Now process the first tag on a line,
            # once we have looped the first tags on each line the while loop
            # will loop until no tags left on any lines
            alt_text, width, height, original_alt_box = find_alt_box_details(image_tags[0])
            path = find_markdown_path(image_tag_line)
            auto_tag = create_image_autolink(alt_text, width, height, path)
            old = f'{original_alt_box}({path})'
            content = content.replace(old, auto_tag)

        image_tag_lines = find_image_tag_lines(content)

    return content


def find_alt_box_details(text_line):
    width = ''
    height = ''

    tag_part_one = text_line.split('[', 1)[1].rsplit(']', 1)[0]
    original_alt_box = f'![{tag_part_one}]'

    alt_text, width_and_height = tag_part_one.rsplit('|', 1)

    if width_and_height.isnumeric():
        width = str(int(width_and_height))
    else:
        try:
            found_width, found_height = width_and_height.split('x')
            if found_width.isnumeric():
                width = str(int(found_width))
            if found_height.isnumeric() and width:
                height = str(int(found_height))
            if width == '':
                # width and height were invalid entries add to alt text
                alt_text = tag_part_one
        except ValueError:
            alt_text = f'{alt_text}|{width_and_height}'  # invalid width and height include them in the alt text

    return alt_text, width, height, original_alt_box


def replace_markdown_html_img_tag_with_obsidian_image_links(content: str) -> str:
    """
    Reformat markdown html img tag to obsidian markdown formatted image links in the provided content

    <img src="my_image.gif" alt="Some alt text" width="600"/>
    becomes
    ![Some alt text|600](my_image.gif)

    Parameters
    ==========
    content :  str
        Markdown content

    Returns
    =======
    str
        Updated content with replaced image links

    """
    soup = BeautifulSoup(content, 'html.parser')
    tags = soup.findAll('img')
    replacements = {}
    for i in range(len(tags)):
        new_obsidian_link = generate_obsidian_image_markdown_link(tags[i])
        if not new_obsidian_link:  # no new link was returned skip ahead
            continue

        replacements[str(tags[i])] = new_obsidian_link

    new_content = str(soup)
    # we use the str(soup) because the string in the replacements list may not be the same string as in the content
    # as soup swaps parameters around etc

    for old, new in replacements.items():
        new_content = new_content.replace(old, new)

    return new_content


def find_markdown_path(line: str):
    """Parse the given string for the path in a markdown image tag"""
    path = ''
    open_paren_count = 0
    for char in line:
        if char == '(':
            open_paren_count += 1
        if char == ')':
            open_paren_count -= 1
        if open_paren_count > 0:
            path = f"{path}{char}"
        if len(path) > 0 and open_paren_count == 0:
            break
    path = path.strip('(')

    return path


def find_image_tag_lines(text_to_search):
    """Return a list of lines that contain a markdown image tag with a pipe ![ | ]()"""
    lines = re.findall(r'^.*!\[.*?\|.*?]\(.*\).*$', text_to_search, re.MULTILINE)
    return lines


def create_image_autolink(alt_text='', img_width='', img_height='', path=''):
    """create an image autolink formatted markdown string """
    alt = ''
    width = ''
    height = ''
    if alt_text:
        alt = f'alt="{alt_text}" '
    src = f'src="{path}" '
    if img_width:
        width = f'width="{img_width}" '
    if img_height:
        height = f'height="{img_height}" '

    return f'<img {alt}{src}{width}{height}/>'


base64_href_pattern = re.compile(r"data:image/(png|jpeg|jpg);base64,")


def has_base64_image_embedded(href: str) -> bool:
    return href and (base64_href_pattern.match(href) is not None)


def read_base64_image(href: str) -> bytes:
    data_start = href.find(",") + 1
    return base64.b64decode(href[data_start:])


def is_svg(contents: str) -> bool:
    return contents and contents.startswith("<svg ")


def read_svg(contents: str) -> bytes:
    return cairosvg.svg2png(contents)
