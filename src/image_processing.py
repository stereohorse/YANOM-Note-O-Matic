import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

import helper_functions
import config


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

    if 'alt' in tag.attrs:
        new_attrs['alt'] = tag.attrs['alt']

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
    if 'width' not in tag.attrs:
        return  # no width so no need for obsidian format

    if tag.attrs['width'] == '':
        return  # no width so no need for obsidian format
    else:
        width = f"|{tag.attrs['width']}"

    alt = tag.attrs.get('alt', '')
    src = tag.attrs.get('src', '')
    src = helper_functions.path_to_posix_str(src)

    obsidian_img_tag_markdown = f'![{width}]({src})'
    if alt:
        obsidian_img_tag_markdown = f'![{alt}{width}]({src})'

    return obsidian_img_tag_markdown


def replace_obsidian_image_links_with_html_img_tag(content: str) -> str:
    """
    Reformat obsidian markdown formatted image links to markdown html img tag format in the provided content.

    The string provided is analysed, the source is formatted as a posix path and a html img tag string is generated.

    ![Some alt text|600](my_image.gif)
    becomes
    <img src="my_image.gif" alt="Some alt text" width="600"/>

    Tags that are not obsidian formatted - so do not contain |width will not be changed

    Parameters
    ==========
    content :  str
        Markdown content

    Returns
    =======
    str
        Updated content with replaced image links

    """
    image_tags = re.findall(r'!\[.*?]\(.*?\)', content)

    if not image_tags:
        return content

    for tag in image_tags:
        tag_part_one = tag.split('[', 1)[1].rsplit(']', 1)[0]

        if not tag_part_one:
            continue  # skip ahead as this tag is not formatted for obsidian as first part is empty[]

        if '|' not in tag_part_one:
            continue  # skip ahead as this tag is not formatted for obsidian as no pipe so no width so not obsidian

        alt_text, width = tag_part_one.rsplit('|', 1)
        if not width.isnumeric():
            continue  # skip ahead as this tag is not formatted for obsidian

        if alt_text:
            alt_text = f'alt="{alt_text}" '

        width = f' width="{width}"'

        src = tag.rsplit('(', 1)[1].rstrip(')')
        src = helper_functions.path_to_posix_str(src)
        src = f'src="{src}"'

        new_image_tag = f'<img {alt_text}{src}{width} />'

        content = content.replace(tag, new_image_tag)

    return content


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
