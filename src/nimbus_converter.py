from copy import copy
from pathlib import Path
from typing import Set
from uuid import uuid4

from bs4 import BeautifulSoup

import file_writer
import helper_functions
import zip_file_reader
from conversion_settings import ConversionSettings
from html_data_extractors import process_child_items
from html_nimbus_extractors import extract_from_nimbus_tag
from image_processing import read_base64_image, has_base64_image_embedded, is_svg, read_svg
from nimbus_note_content_data import MentionLink
from nimbus_note_content_data import NimbusIDs, NimbusProcessingOptions
from note_content_data import Body, Outline, ImageEmbed
from note_content_data import FileAttachment, FileAttachmentCleanHTML
from note_content_data import HeadingItem
from note_content_data import ImageAttachment
from note_content_data import NimbusNote, NoteData
from note_content_data import TextItem
from processing_options import ProcessingOptions


def get_file_suffix_for(export_format: str) -> str:
    if export_format == 'html':
        return '.html'
    return '.md'


def read_link_source_file(path_to_zip, path_in_zip_file):
    return zip_file_reader.read_binary_file(path_to_zip, Path(path_in_zip_file), message=str(path_to_zip))


def write_asset_to_target(asset_content, asset_link, path_to_note_folder):
    full_path = Path(path_to_note_folder, asset_link.target_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)

    new_target_path = helper_functions.find_valid_full_file_path(full_path)
    if new_target_path != full_path:
        asset_link.update_target(Path(asset_link.target_path.parent, new_target_path.name))

    file_writer.write_bytes(new_target_path, asset_content)


def match_nimbus_mentions_to_files_or_folders(a_document, nimbus_ids, dict_of_notes):
    mentions = a_document.find_items(class_=MentionLink)
    for mention in mentions:
        mention.try_to_set_target_path(a_document.note_paths, nimbus_ids, dict_of_notes)


def process_note_assets(a_note, attachment_folder_name, processing_options):
    asset_links = a_note.find_items(class_=(FileAttachment, ImageAttachment))
    zip_file_path = Path(a_note.note_paths.path_to_note_source, a_note.note_paths.note_source_file_name)

    # process the known about linked files
    filenames_processed = extract_and_write_assets(a_note, asset_links, attachment_folder_name, zip_file_path)

    # now locate orphan files
    orphans = find_orphan_filenames_in_zipfile(filenames_processed, str(zip_file_path))
    if not orphans:
        return

    # now process the orphan files and add links for these files to to body content
    process_orphan_files(a_note, attachment_folder_name, orphans, processing_options, zip_file_path)


def process_orphan_files(a_note, attachment_folder_name, orphans, processing_options, zip_file_path):
    asset_links = []

    # find body content and add a heading
    new_body_contents = get_copy_of_note_body_contents(a_note)

    new_body_contents.append(HeadingItem(processing_options,
                                         [TextItem(processing_options, 'Note Attachments')],
                                         level=3,
                                         id=''
                                         )
                             )
    for file in orphans:
        # create a new link object for the orphan file
        contents = TextItem(processing_options, str(file))
        href = str(Path('assets', file))
        target_filename = str(file)
        # source_path = Path('assets', file)
        new_link = FileAttachmentCleanHTML(processing_options, contents, href, target_filename)
        new_link.set_target_path(attachment_folder_name)

        # add link to body
        new_body_contents.append(new_link)

        # add link to asset_links
        asset_links.append(new_link)

    # update the body_contents
    update_note_body_contents(a_note, new_body_contents)

    # process the new links
    _ = extract_and_write_assets(a_note, asset_links, attachment_folder_name, zip_file_path)


def get_copy_of_note_body_contents(a_note) -> [NoteData]:
    body_contents = a_note.find_items(class_=Body)[0].contents.copy()
    return body_contents


def update_note_body_contents(a_note, new_body_contents):
    a_note.find_items(class_=Body)[0].contents = new_body_contents


def extract_and_write_assets(a_note, asset_links, attachment_folder_name, zip_file_path):
    filenames_processed = set()
    for link in asset_links:
        link.set_target_path(attachment_folder_name)
        asset = None

        if isinstance(link, ImageEmbed):
            if is_svg(link.contents):
                asset = read_svg(link.contents)
                correct_image_name(asset, attachment_folder_name, link)
            elif not link.href:
                # ignore absent source paths
                continue
            elif has_base64_image_embedded(link.href):
                asset = read_base64_image(link.href)
                correct_image_name(asset, attachment_folder_name, link)

        if not asset:
            asset = read_link_source_file(zip_file_path, str(link.source_path))

        # in nimbus all audio files are exported as .mpga irrespective of what the file actually is
        # so use header bytes form the asset to identify the correct extension
        if link.source_path.suffix == '.mpga':
            link.target_path = helper_functions.correct_file_extension(asset[:261], link.target_path)

        write_asset_to_target(asset, link, a_note.note_paths.path_to_note_target)

        filenames_processed.add(str(link.source_path.name))

    return filenames_processed


def correct_image_name(asset, attachment_folder_name, link):
    link.filename = str(uuid4())
    link.set_target_path(attachment_folder_name)
    link.target_path = helper_functions.correct_file_extension(asset, link.target_path)


def find_orphan_filenames_in_zipfile(filenames_known_about: Set, zip_file_path: str) -> Set[str]:
    """
    Find a set tof files that are in the zipfile that are not in the set of files already known about.  This set of
    'orphan' files is returned.  If there are no orphan files an empty set is returned

    Parameters
    ----------
    filenames_known_about : Set
        set of file names that are already known about, this set of files will be subtracted from the files in the
        zipfile.
    zip_file_path: str
        path to the zip file that a file list will be extracted from.

    Returns
    -------
    Set
        Set of files that are in the zip file but not in the filenames_known_about set.
    """
    files_in_zip = zip_file_reader.list_files_in_zip_file_from_a_directory(zip_file_path, 'assets', ['theme.css'])
    filenames_in_zip_asset_folder = {file.name for file in files_in_zip}
    orphans = filenames_in_zip_asset_folder - filenames_known_about

    return orphans


def initialise_new_note(zip_file, conversion_settings, processing_options: NimbusProcessingOptions):
    new_note = NimbusNote(processing_options, contents=[], conversion_settings=conversion_settings)

    new_note.title = zip_file.stem.replace('_', ' ')

    new_note.note_paths.path_to_note_source = Path(zip_file.parent)

    new_note.note_paths.path_to_source_folder = conversion_settings.source_absolute_root

    dirty_workspace_folder_name = Path(zip_file.parent).relative_to(conversion_settings.source_absolute_root).parts[0]

    new_note.note_paths.path_to_source_workspace = Path(conversion_settings.source_absolute_root,
                                                        dirty_workspace_folder_name)

    new_note.note_paths.path_to_target_folder = conversion_settings.export_folder_absolute
    new_note.note_paths.note_target_suffix = get_file_suffix_for(conversion_settings.export_format)

    new_note.note_paths.note_source_file_name = zip_file.name
    clean_file_name = helper_functions.generate_clean_filename(new_note.title, processing_options.filename_options)

    new_note.note_paths.note_target_file_name = Path(f'{clean_file_name}'
                                                     f'{new_note.note_paths.note_target_suffix}')

    new_note.note_paths.set_note_target_path(processing_options)

    new_note.note_paths.set_path_to_attachment_folder(conversion_settings.attachment_folder_name, processing_options)

    return new_note


def extract_note_data_from_zip_file(zip_file, processing_options: ProcessingOptions):
    html_content = zip_file_reader.read_text(zip_file, Path('note.html'), '')
    soup = BeautifulSoup(html_content, 'html.parser')
    zip_file_data = process_child_items(soup.find("html"),
                                        processing_options,
                                        note_specific_tag_cleaning=extract_from_nimbus_tag,
                                        )

    return zip_file_data


def match_up_file_links(dict_of_notes, notes):
    nimbus_ids = NimbusIDs()
    for i in range(2):  # requires two passes of the matching routine to match renamed notes
        for note in notes:
            match_nimbus_mentions_to_files_or_folders(note, nimbus_ids, dict_of_notes)


def write_note_to_file(document):
    target_folder = document.note_paths.path_to_note_target

    # ensure all folder exist, they may already from writing assets but a file with no assets need them created here
    target_folder.mkdir(exist_ok=True, parents=True)

    target_file_name = document.note_paths.note_target_file_name
    document_target = Path(target_folder, target_file_name)

    if document.conversion_settings.export_format == 'html':
        file_writer.write_text(document_target, document.html())
        return

    file_writer.write_text(document_target, document.markdown())


def convert_nimbus_notes(conversion_settings: ConversionSettings, nimbus_zip_files: Set):
    processing_options = NimbusProcessingOptions(conversion_settings.embed_files,
                                                 conversion_settings.export_format,
                                                 conversion_settings.unrecognised_tag_format,
                                                 conversion_settings.filename_options,
                                                 conversion_settings.keep_nimbus_row_and_column_headers,
                                                 )

    notes = extract_note_content(conversion_settings, nimbus_zip_files, processing_options)

    notes = process_metadata(notes)

    # find outline if there then set id's if out put format not html
    if not processing_options.export_format == 'html':
        create_heading_ids_if_outline_in_note_data(notes, processing_options)

    dict_of_notes = create_dictionary_of_notes(notes)

    match_up_file_links(dict_of_notes, notes)

    num_images = 0
    num_attachments = 0
    for note in notes:
        process_note_assets(note, conversion_settings.attachment_folder_name, processing_options)
        write_note_to_file(note)
        images = note.find_items(class_=ImageAttachment)
        attachments = note.find_items(class_=FileAttachment)
        if images:
            num_images += len(images)
        if attachments:
            num_attachments += len(attachments)

    return num_images, num_attachments


def extract_note_content(conversion_settings, nimbus_zip_files, processing_options):
    notes = []
    for zip_file in nimbus_zip_files:
        note = initialise_new_note(zip_file, conversion_settings, processing_options)
        note.contents = extract_note_data_from_zip_file(zip_file, processing_options)
        notes.append(note)

    return notes


def process_metadata(notes):
    notes_copy = copy(notes)
    for note_to_process in notes_copy:
        note_to_process.find_tags()
        note_to_process.add_front_matter_to_content()

    return notes_copy


def create_dictionary_of_notes(notes):
    dict_of_notes = {}
    # key = title, value = list of links  This is used to look up notes when matching links using note titles
    for note in notes:
        if note.title not in dict_of_notes:
            dict_of_notes[note.title] = []

        dict_of_notes[note.title].append(note)

    return dict_of_notes


def create_heading_ids_if_outline_in_note_data(notes, processing_options):
    for note in notes:
        outline = note.find_items(class_=Outline)
        if not outline:
            continue

        headings = note.find_items(class_=HeadingItem)
        for heading in headings:
            heading.include_id_format = processing_options.export_format


def main():
    def generate_file_list(file_extension, path_to_files: Path):
        if path_to_files.is_file():
            return [path_to_files]

        file_list_generator = path_to_files.rglob(f'*{file_extension}')
        file_list = {item for item in file_list_generator}
        return file_list

    conversion_settings = ConversionSettings()
    conversion_settings.quick_set_gfm_settings()
    conversion_settings.working_directory = Path('/Users/nimbus')
    conversion_settings.export_format = 'obsidian'
    # conversion_settings.export_format = 'gfm'
    # conversion_settings.export_format = 'multimarkdown'
    conversion_settings.conversion_input = 'nimbus'
    conversion_settings.split_tags = True
    conversion_settings.source = 'source'
    conversion_settings.export_folder = 'target'
    conversion_settings.attachment_folder_name = 'assets'
    conversion_settings.front_matter_format = 'yaml'
    # conversion_settings.front_matter_format = 'toml'
    # conversion_settings.front_matter_format = 'json'
    # conversion_settings.front_matter_format = 'text'
    # conversion_settings.front_matter_format = 'none'
    conversion_settings.tag_prefix = '#'

    conversion_settings.keep_nimbus_row_and_column_headers = False
    conversion_settings.embed_these_document_types = ['md', 'pdf']
    conversion_settings.embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    conversion_settings.embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    conversion_settings.embed_these_video_types = ['mp4', 'webm', 'ogv']

    conversion_settings.unrecognised_tag_format = 'html'
    # options html = as html tag, text or '' = string content of tag

    nimbus_zip_files = generate_file_list('zip', conversion_settings.source_absolute_root)

    convert_nimbus_notes(conversion_settings, nimbus_zip_files)


# TODO docstrings
# TODO logging - all logging but also add all unrecognised html objects to warning log


if __name__ == '__main__':
    main()
