from collections import namedtuple
import os.path
from pathlib import Path
import re
from typing import Iterable
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup

import helper_functions


def absolute_path_from_relative_path(file: Path, link: str) -> Path:
    """Generate an absolute path given a relative link from a file and the absolute link to that file"""
    return Path(os.path.abspath(Path(file.parent, link)))


def calculate_relative_path(absolute_link, target_root) -> Path:
    """Generate a relative path given an absolute link and a target path the ink is to be relative to"""
    return Path(os.path.relpath(absolute_link, target_root))


def update_content_with_new_link(old_path, new_path, content: str) -> str:
    """Update provided content string with a new path to replace an old path"""
    return content.replace(helper_functions.path_to_posix_str(old_path), helper_functions.path_to_posix_str(new_path))


def update_href_link_suffix_in_content(content: str, output_suffix: str, links_to_update: Iterable[Path]) -> str:
    """
    Update file extensions for href links in the provided content str.

    The links provided will be searched for in the content and the file extensions on those links will be updated to
    the new output_suffix value.

    Parameters
    ----------
    content : str
        string containing href links to be updated
    output_suffix :  str
        string for the new suffix including the leading '.' for example '.md'
    links_to_update : Iterable[Path]
        iterable of path objects where each path is checked as being a href link path in the provided content

    Returns
    -------
    str:
        The updated content

    """
    soup = BeautifulSoup(content, 'html.parser')
    for a_tag in soup.findAll(href=True):
        url_path = Path(urlparse(a_tag['href']).path)
        if url_path in links_to_update:
            link = helper_functions.path_to_posix_str(url_path.with_suffix(output_suffix))
            a_tag['href'] = link

    return str(soup)


def update_relative_links_to_absolute_links(content_file_path: Path, link_set: set[str]) -> set[Path]:
    """
    Change any relative file paths to absolute file paths and return a full set of absolute paths.

    Uses the location of the converted file to calculate an absolute patt and returns a new set of links that contains
    only absolute paths.

    Parameters
    ==========
    content_file_path : Path
        The Path to the final location of the file the provided links sets were generated from.  This path is used to
        calculate absolute paths for any relative paths provided.
    link_set : set[Path}
        set of Path objects that may be absolute or relative paths

    Returns
    =======
    set[str]
        Set of links that are all absolute paths.

    """
    new_link_set = set()
    for link in link_set:
        link = Path(link)
        if not Path(link).is_absolute():
            link = absolute_path_from_relative_path(content_file_path, str(link))

        new_link_set.add(link)

    return new_link_set


def scan_html_content_for_all_paths(content: str):
    """
    Search a html formatted content string string for links and return a set of file links

    Search for all links and build set of those links where the link is not a link to a 'https:\\' address,
    and then return the set of local file links. The returned set of links is ALL links if you have links between
    content pages these are included and can be removed using the remove_content_links_from_links method.

    Link formats supported are
    <a href="../test-book-2/this-is-a-duplicated-title-1.md">This is a duplicated title</a>
    <img src="markdown_monster_icon.png" />

    uri's also have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
    becomes 'a path/another file.pdf'

    Parameters
    ==========
    content : str
        String containing markdown formatted text.

    Returns
    =======
    set :
        Set containing local file links.

    """

    set_of_html_img_formatted_paths = set_of_html_img_file_paths_from(content)

    set_of_html_href_formatted_paths = set_of_html_href_file_paths_from(content)

    return set_of_html_img_formatted_paths | set_of_html_href_formatted_paths


def scan_markdown_content_for_all_paths(content: str):
    """
    Search a markdown formatted content string for links and return a set of file links

    Search for all links and build set of those links where the link is not a link to a 'https:\\' address,
    and then return the set of local file links.  The returned set of links is ALL links if you have links between
    content pages these are included and can be removed using the remove_content_links_from_links method.

    Link formats supported are
    [any text](../my_other_notebook/attachments/five.pdf "test tool tip text")
    [or empty](../my_other_notebook/attachments/five.pdf)
    [any text](https://www.google.com "google")
    [or empty](https://www.google.com)
    <a href="../test-book-2/this-is-a-duplicated-title-1.md">This is a duplicated title</a>
    <img src="markdown_monster_icon.png" />

    uri's also have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
    becomes 'a path/another file.pdf'

    Parameters
    ==========
    content : str
        String containing markdown formatted text.

    Returns
    =======
    set :
        Set containing local file links.

    """
    set_of_md_formatted_paths = set_of_markdown_file_paths_from(content)

    set_of_html_paths = scan_html_content_for_all_paths(content)

    return set_of_md_formatted_paths | set_of_html_paths


def set_of_html_href_file_paths_from(content):
    """
    Search content for href html local file uri links and return a set of those links.

    Links will have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
    becomes 'a path/another file.pdf'

    Parameters
    ==========
    content : str
        string containing html formatted href tags

    Returns
    =======
    set[Path]
        set of local href link paths

    """
    soup = BeautifulSoup(content, 'html.parser')

    url_paths = set()
    for a_tag in soup.findAll(href=True):
        if (urlparse(a_tag['href']).scheme == "" or urlparse(a_tag['href']).scheme == "file") \
                and len(urlparse(a_tag['href']).path):

            path_to_add = unquote(a_tag['href'])
            path_to_add = helper_functions.unescape(path_to_add)
            url_paths.add(path_to_add)

    return url_paths


def set_of_html_img_file_paths_from(content: str) -> set[str]:
    """
    Search string for html img tag links and return a set of local file path objects.

    Returned paths will have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
    becomes 'a path/another file.pdf'.

    Parameters
    ==========
    content : str
        string containing html formatted img links

    Returns
    =======
    set[str]
        set of local img links

    """

    soup = BeautifulSoup(content, 'html.parser')
    url_paths = {
        unquote(urlparse(i_tag['src']).path)
        for i_tag in soup.findAll(src=True)
        if
        (urlparse(i_tag['src']).scheme == "" or urlparse(i_tag['src']).scheme == "file")
        and
        len(urlparse(i_tag['src']).path)
    }

    return url_paths


def set_of_markdown_file_paths_from(content: str) -> set[str]:
    """
    Search string for markdown formatted image and file links and return a set of local file path objects.

    Returned Paths will have unquote applied to generate the paths so 'a%20path/another%20file.pdf'
    becomes 'a path/another file.pdf'
    Link formats supported are
        [any text](../my_other_notebook/attachments/five.pdf "test tool tip text")
        [or empty](../my_other_notebook/attachments/an_image.jpg)
        [any text](https://www.google.com "google")
        [or empty](https://www.google.com)

    Parameters
    ==========
    content : str
        string containing html formatted img links

    Returns
    =======
    set[str]
        set of local link strings
    """

    regex_md_pattern = re.compile(r'''
        \[[^]]*]\(     # match the '[alt text](' part of the markdown link
        (              # start capturing group
        [^) ]*         # match many characters up to ) or up to a space [ ]
        )              # close capturing group
        (?:            # start non capturing group
        \)|            # match literal ) or single space
        )              # close non capturing group
    ''', re.MULTILINE | re.VERBOSE)

    matches_md = regex_md_pattern.findall(content)

    set_of_md_formatted_links = set()

    for match in matches_md:
        if not match.startswith("https://") and not match.startswith("http://") and len(match):
            path = unquote(match)
            path = helper_functions.unescape(path)
            set_of_md_formatted_links.add(path)

    return set_of_md_formatted_links


def remove_content_links_from_links(content_file_path: Path,
                                    content_links: Iterable[Path],
                                    links: Iterable[str]) -> set[str]:
    """
    Remove any links that are links between note pages from the provided set of links.

    Parameters
    ==========
    content_file_path : Path
        The Path to the final location of the file the provided links sets were generated from.  This path is used to
        calculate absolute paths for any relative paths provided.
    content_links : Iterable[Path}
        Iterable of Path objects for the paths each note being processed and will be removed from the
        links set if present.
    links :
        Iterable of Path objects that contains a mixture of links between to note pages and to images and attachments.

    Returns
    =======
    set[str]
        Set of links that does not contain links between note pages.

    """
    links = set(links)
    links_to_remove = set()
    for link in links:
        abs_link = Path(link)
        if not Path(link).is_absolute():
            abs_link = absolute_path_from_relative_path(content_file_path, link)

        if abs_link in content_links:
            links_to_remove.add(link)

    links.difference_update(links_to_remove)
    return links


def split_set_existing_non_existing_links(content_file_path: Path, links: set[str]) -> namedtuple:
    """
    Split a list of links into sets of existing and non-existing file links

    Each path in the provided set of links is tested to see if the file exists and the path is then placed into the
    relevant set.

    Parameters
    ==========
    content_file_path : Path
        The Path to the final location of the file the provided links sets were generated from.  This path is used to
        calculate absolute paths for any relative paths provided.
    links : set[str]
        set of links to be split into existing and non-existing sets of links

    Returns
    =======
    namedtuple : (non_existing_links: set[Path], existing_links: set[Path])
        namedtuple containing sets of existing and non-existing paths

    """
    existing_links = set()
    non_existing_links = set()

    for link in links:
        if Path(link).is_absolute():
            if Path(link).exists():
                existing_links.add(link)
            else:
                non_existing_links.add(link)
            continue

        absolute_link_path = absolute_path_from_relative_path(content_file_path, link)

        if absolute_link_path.exists():
            existing_links.add(link)
            continue

        non_existing_links.add(link)

    file_exists_status_links = namedtuple('file_exists_status_links', 'existing, non_existing')
    return file_exists_status_links(existing_links, non_existing_links)


def split_existing_links_copyable_non_copyable(content_file_path: Path,
                                               root_for_copyable_paths: Path,
                                               links_to_split: set[str]) -> namedtuple:
    """
    Split the set of existing file links into two sets.  One set of links that will be copyable to the new export
    folder and one set that will not be copyable.

    The non-copyable links are links that have a path outside of the current conversion source path.
    For example if the source path is /somewhere/data  then files in paths outside of that path can not be
    copied to the export folder for example /somewhere/another_folder/attachment.pdf can not be copied whilst
    /somewhere/data/any_file_or_path/any_file.pdf can be copied
    _non_copyable_attachment_path_set and _copyable_attachment_path_set will be updated with the
    relevant paths

    Parameters
    ==========
    content_file_path : Path
        The Path to the final location of the file the provided links sets were generated from.  This path is used to
        calculate absolute paths for any relative paths provided.
    root_for_copyable_paths : Path
        Path object for the path that sets if a file if copyable or not.  Typically for a set of notes being converted
        this is the source folder, where any file in the source directory or it's subdirectories can be easily moved
        when a relative path is used in the note content.
    links_to_split : set[Path]
        Set of paths that are known to be existing files

    Returns
    =======
    namedtuple : (copyable_attachment_path_set: set[Path], non_copyable_attachment_path_set: set[Path])
        namedtuple containing sets of copyable and non-copyable paths

    """
    copyable_attachment_path_set = set()
    non_copyable_relative = set()
    non_copyable_absolute = set()

    for link in links_to_split:
        abs_link = Path(link)
        if not Path(link).is_absolute():
            abs_link = absolute_path_from_relative_path(content_file_path, link)

        if root_for_copyable_paths in abs_link.parents:
            copyable_attachment_path_set.add(link)
            continue

        if Path(link).is_absolute():
            non_copyable_absolute.add(link)
            continue

        non_copyable_relative.add(link)

    copyable_status_links = namedtuple('copyable_status_links',
                                       'copyable, non_copyable_relative, non_copyable_absolute',
                                       )
    return copyable_status_links(copyable_attachment_path_set, non_copyable_relative, non_copyable_absolute)


def split_valid_and_invalid_link_paths(all_paths: set[str]):
    valid_paths = set()
    invalid_paths = set()
    for path in all_paths:
        if helper_functions.is_path_valid(path):
            valid_paths.add(path)
            continue
        invalid_paths.add(path)

    validity_status_links = namedtuple('validity_status_links',
                                       'valid, invalid')
    return validity_status_links(valid_paths, invalid_paths)


def update_content_with_new_paths(content: str,
                                  content_file_path: Path,
                                  path_set: Iterable[str],
                                  make_absolute: bool,
                                  root_for_absolute_paths: Path):
    """
    Update content with a new relative or absolute path for provided set of Paths

    If make_absolute is True, a relative link  provided in path_set will be made absolute and updated in the content.
    If make_absolute is False relative paths in the content to files in the provided path_set are
    updated with new paths that are relative to the root_for_absolute_paths path.

    Parameters
    ==========
    content : str
        Str containing links that are in the non_copyable_attachment_path_set.
    content_file_path : Path
        The Path to the final location of the file the provided links sets were generated from.  This path is used to
        calculate absolute paths for any relative paths provided.
    path_set : set[str]
        set of Path objects that require to be updated.  Typically this would be a set of paths that are to files that
        are outside of the root of the notes set.
    make_absolute : bool
        If True then relative paths will be made absolute.
        If false relative paths remain as relative paths.
    root_for_absolute_paths : Path
        Path that is the root of the notes content final location and is used to calculate relative paths.

    Returns
    =======
    str
        Modified content string with new paths

    """
    for original_link in path_set:
        if Path(original_link).is_absolute():  # no need to change as an absolute path
            continue

        attachment_absolute_path = absolute_path_from_relative_path(content_file_path, original_link)
        new_path = attachment_absolute_path

        if not make_absolute:
            new_relative_path = calculate_relative_path(
                absolute_link=attachment_absolute_path,
                target_root=root_for_absolute_paths,
            )
            new_path = new_relative_path

        content = update_html_link_src(content, original_link, new_path)
        content = update_markdown_link_src(content, original_link, new_path)

    return content


def process_attachments(path_to_content_file: Path, set_of_links: set[str], note_paths: set[Path],
                        source_absolute_root):
    """
    Generate sets of attachment links from content.

    The sets of links based on the status of that links.
        all - all links found in the content that are not to other note files being converted.
        valid_links - set of links that are invalid for the current file system.
        invalid_links - set of links that are invalid for the current file system.
        non-existing - file is not found in file system.
        existing - file was found in file system.
        copyable - file is in the path of the source_absolute path.
        non-copyable - file is NOT in the path of the source_absolute path.


    Absolute attachment links
    Absolute links are not changed in the content.
    If the file exists the path is added to self._non_copyable_attachment_path_set
    If the file does not exist the path is added to self._non_existing_links_set

    Relative attachment links
    Links may be changed in the note content
    If the file does not exist the path is added to self._non_existing_links_set
    If the file for the relative link exists then:-
    If the relative link is with in the path of conversion_settings.source then it is
    NOT changed in the note content and the path to the attachment is added
    to self._copyable_attachment_absolute_path_set
    If the relative link is to a file not on the path of conversion_settings.source it is
    recalculated and IS changed in the content and the path to the attachment is added
    to self._non_copyable_attachment_path_set

    Parameters
    ==========
    path_to_content_file : Path
        Absolute path to the file the set_of _links if from
    set_of_links : set[str]
        set of path strings for all links from note content
    note_paths : set[Path]
        set of paths to each of the note files names being processed.
    source_absolute_root : Path
        Absolute path to the source folder for the note the links are being processed from

    Returns
    =======
    namedtuple attachment_links:
        named tuple containing
        all_links - set of all links to local files attached to the note page
        valid_links - set of links that are invalid for the current file system
        invalid_links - set of links that are invalid for the current file system
        existing - set of links to files that exist on the local file system
        non_existing - set of links to files that do not exist on the local file system
        copyable - set of links to files that are in the same path as the source of the content
        non_copyable - set of links to files that are NOT in the same path as the source of the content

    """
    all_attachments = remove_content_links_from_links(path_to_content_file, note_paths, set_of_links)

    link_validity = split_valid_and_invalid_link_paths(all_attachments)
    file_exists_status_links = split_set_existing_non_existing_links(path_to_content_file,
                                                                     link_validity.valid)

    copyable_status_links = split_existing_links_copyable_non_copyable(path_to_content_file,
                                                                       source_absolute_root,
                                                                       file_exists_status_links.existing)

    copyable_absolute = update_relative_links_to_absolute_links(path_to_content_file,
                                                                copyable_status_links.copyable)

    attachment_links = namedtuple('attachment_links',
                                  'all, '
                                  'valid, '
                                  'invalid, '
                                  'existing, '
                                  'non_existing, '
                                  'copyable, '
                                  'non_copyable_relative, '
                                  'non_copyable_absolute, '
                                  'copyable_absolute'
                                  )

    return attachment_links(all_attachments,
                            link_validity.valid,
                            link_validity.invalid,
                            file_exists_status_links.existing,
                            file_exists_status_links.non_existing,
                            copyable_status_links.copyable,
                            copyable_status_links.non_copyable_relative,
                            copyable_status_links.non_copyable_absolute,
                            copyable_absolute
                            )


def find_local_file_links_in_content(file_type, content):
    if file_type == 'html':
        return scan_html_content_for_all_paths(content)

    return scan_markdown_content_for_all_paths(content)


def get_attachment_paths(source_absolute_root, file_type, file, files_to_convert, content) -> namedtuple:
    """
    Generate sets of attachment links from content.

    The sets of links based on the status of that links.
        all - all links found in the content that are not to other note files being converted.
        valid_links - set of links that are invalid for the current file system.
        invalid_links - set of links that are invalid for the current file system.
        non-existing - file is not found in file system.
        existing - file was found in file system.
        copyable - file is in the path of the source_absolute path.
        non-copyable - file is NOT in the path of the source_absolute path.


    Absolute attachment links
    Absolute links are not changed in the content.
    If the file exists the path is added to self._non_copyable_attachment_path_set
    If the file does not exist the path is added to self._non_existing_links_set

    Relative attachment links
    Links may be changed in the note content
    If the file does not exist the path is added to self._non_existing_links_set
    If the file for the relative link exists then:-
    If the relative link is with in the path of conversion_settings.source then it is
    NOT changed in the note content and the path to the attachment is added
    to self._copyable_attachment_absolute_path_set
    If the relative link is to a file not on the path of conversion_settings.source it is
    recalculated and IS changed in the content and the path to the attachment is added
    to self._non_copyable_attachment_path_set

    Parameters
    ==========
    source_absolute_root : Path
        Absolute path to the source folder for the content
    file_type : str
        Str of the file type being converted
    file : Path
        Path to the file the content has come from
    files_to_convert : Iterable[Path]
        Iterable of Path objects representing all files in a conversion job, used to exclude content files from the
        set of attachments
    content : str
        Note content

    Returns
    =======
    namedtuple attachment_links:
        named tuple containing
        all_links - set of all links to local files attached to the note page
        valid_links - set of links that are invalid for the current file system
        invalid_links - set of links that are invalid for the current file system
        existing - set of links to files that exist on the local file system
        non_existing - set of links to files that do not exist on the local file system
        copyable - set of links to files that are in the same path as the source of the content
        non_copyable - set of links to files that are NOT in the same path as the source of the content and can not
        be moved during note conversion

    """
    set_of_links = find_local_file_links_in_content(file_type, content)

    attachment_links = process_attachments(file,
                                           set_of_links,
                                           set(files_to_convert),
                                           source_absolute_root)

    return attachment_links


def update_html_link_src(content: str, old_name: str, new_name: Path) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    for a_tag in soup.findAll(href=True):
        url_path = urlparse(a_tag['href']).path
        if url_path == old_name:
            a_tag['href'] = helper_functions.path_to_posix_str(new_name)
            # do not return early after finding link as content may have more than one link to the renamed file

    return str(soup)


def update_markdown_link_src(content: str, old_name: str, new_name: Path) -> str:
    tags = re.findall(r'\[.*?]\(.*?\)', content)

    if not tags:
        return content

    for tag in tags:
        src = tag.rsplit('(', 1)[1].rstrip(')')
        if src == old_name:
            new_image_tag = tag.replace(old_name, helper_functions.path_to_posix_str(new_name))
            content = content.replace(tag, new_image_tag)

    return content


def get_set_of_all_files(path: Path):
    set_of_all_files = {
        Path(file)
        for file
        in path.rglob('*')
        if Path(file).is_file()
    }
    return set_of_all_files
