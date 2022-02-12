from dataclasses import dataclass, field
from pathlib import Path
from typing import Set

from bs4 import BeautifulSoup

from embeded_file_types import EmbeddedFileTypes
import file_writer
import helper_functions
from html_data_extractors import process_child_items
from html_nimbus_extractors import extract_from_nimbus_tag
from nimbus_note_content_data import MentionLink
from nimbus_note_content_data import NimbusIDs, NimbusProcessingOptions
from note_content_data import Body
from note_content_data import FileAttachment, FileAttachmentCleanHTML
from note_content_data import HeadingItem
from note_content_data import ImageAttachment
from note_content_data import Note, NoteData
from processing_options import ProcessingOptions
from note_content_data import TextItem
import zip_file_reader


def get_file_suffix_for(export_format: str) -> str:
    if export_format == 'html':
        return '.html'
    return '.md'


def generate_file_list(file_extension, path_to_files: Path):
    if path_to_files.is_file():
        return [path_to_files]

    file_list_generator = path_to_files.rglob(f'*{file_extension}')
    file_list = {item for item in file_list_generator}
    return file_list


@dataclass
class ConversionSettings:  # simulating conversion settings object from YANOM
    export_format: str = field(default='obsidian')
    conversion_input: str = field(default='nimbus')
    split_tags: bool = field(default=True)
    source: Path = Path('/Users/kevindurston/nimbus/source')
    target: Path = Path('/Users/kevindurston/nimbus/target')
    attachment_folder_name: str = 'assets'
    front_matter_format: str = 'yaml'  # options yaml, toml, json, none, text
    # front_matter_format: str = 'toml'  # options yaml, toml, json, none, text
    # front_matter_format: str = 'json'  # options yaml, toml, json, none, text
    # front_matter_format: str = 'text'  # options yaml, toml, json, none, text
    # front_matter_format: str = 'none'  # options yaml, toml, json, none, text
    tag_prefix = '#'
    keep_nimbus_row_and_column_headers = False
    embed_these_document_types = ['md', 'pdf']
    embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    embed_these_video_types = ['mp4', 'webm', 'ogv']
    embed_files = EmbeddedFileTypes(embed_these_document_types, embed_these_image_types,
                                    embed_these_audio_types, embed_these_video_types)
    unrecognised_tag_format = 'html'  # options html = as html tag, none = ignore, text = string content of tag
    filename_options = helper_functions.FileNameOptions(max_length=255,
                                                        allow_unicode=True,
                                                        allow_uppercase=True,
                                                        allow_non_alphanumeric=True,
                                                        allow_spaces=False,
                                                        space_replacement='-')


def read_link_source_file(path_to_zip, path_in_zip_file):
    return zip_file_reader.read_binary_file(path_to_zip, path_in_zip_file, message=str(path_to_zip))


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

        asset = read_link_source_file(zip_file_path, str(link.source_path))

        # in nimbus all audio files are exported as .mpga irrespective of what the file actually is
        # so use header bytes form the asset to identify the correct extension
        if link.source_path.suffix == '.mpga':
            link.target_path = helper_functions.correct_file_extension(asset[:261], link.target_path)

        write_asset_to_target(asset, link, a_note.note_paths.path_to_note_target)

        filenames_processed.add(str(link.source_path.name))

    return filenames_processed


def find_orphan_filenames_in_zipfile(filenames_known_about: Set, zip_file_path: str) -> Set[str]:
    """
    Find a set tof files that are in the zipfile that are not in the set of files already known about.  This set of
    'orpahn' files is returned.  If there are no orphan files an empty set is returned

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
    new_note = Note(processing_options, contents=[], conversion_settings=conversion_settings)

    new_note.title = zip_file.stem.replace('_', ' ')

    new_note.note_paths.path_to_note_source = Path(zip_file.parent)

    new_note.note_paths.path_to_source_folder = conversion_settings.source

    dirty_workspace_folder_name = Path(zip_file.parent).relative_to(conversion_settings.source).parts[0]

    new_note.note_paths.path_to_source_workspace = Path(conversion_settings.source, dirty_workspace_folder_name)

    new_note.note_paths.path_to_target_folder = conversion_settings.target
    new_note.note_paths.note_target_suffix = get_file_suffix_for(conversion_settings.export_format)

    new_note.note_paths.note_source_file_name = zip_file.name
    clean_file_name = helper_functions.generate_clean_filename(new_note.title, processing_options.filename_options)

    new_note.note_paths.note_target_file_name = Path(f'{clean_file_name}'
                                                         f'{new_note.note_paths.note_target_suffix}')

    new_note.note_paths.set_note_target_path(processing_options)

    new_note.note_paths.set_path_to_attachment_folder(conversion_settings.attachment_folder_name, processing_options)

    return new_note


def extract_note_data_from_zip_file(zip_file, processing_options: ProcessingOptions):
    html_content = zip_file_reader.read_text(zip_file, 'note.html', '')
    soup = BeautifulSoup(html_content, 'html.parser')
    zip_file_data = process_child_items(soup.find("html"),
                                        processing_options,
                                        note_specific_tag_cleaning=extract_from_nimbus_tag,
                                        )

    return zip_file_data


def match_up_file_links(dict_of_notes, documents, nimbus_ids):
    for i in range(2):  # requires two passes of the matching routine to match renamed notes
        for document in documents:
            match_nimbus_mentions_to_files_or_folders(document, nimbus_ids, dict_of_notes)


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

    # TODO below 3 lines fudge to also get html saved whilst testing
    target_file_name = Path(document.note_paths.note_target_file_name).with_suffix('.html')
    document_target = Path(target_folder, target_file_name)
    # file_writer.write_text(document_target, helper_functions.make_soup_from_html(document.html()).prettify())
    file_writer.write_text(document_target, document.html())
    # TODO end of html extra save here
    return


def main():
    conversion_settings = ConversionSettings()
    notes = []

    processing_options = NimbusProcessingOptions(conversion_settings.embed_files,
                                                 conversion_settings.export_format,
                                                 conversion_settings.unrecognised_tag_format,
                                                 conversion_settings.filename_options,
                                                 conversion_settings.keep_nimbus_row_and_column_headers,
                                                 )

    nimbus_zip_files = generate_file_list('zip', conversion_settings.source)

    for zip_file in nimbus_zip_files:
        note = initialise_new_note(zip_file, conversion_settings, processing_options)
        note.contents = extract_note_data_from_zip_file(zip_file, processing_options)
        notes.append(note)

    dict_of_notes = {}
    # key = title, value = list of links  This is used to look up notes when matching links using note titles

    for note in notes:
        note.find_tags()
        note.add_front_matter_to_content()

        if note.title not in dict_of_notes:
            dict_of_notes[note.title] = []

        dict_of_notes[note.title].append(note)

    nimbus_ids = NimbusIDs()
    match_up_file_links(dict_of_notes, notes, nimbus_ids)

    for note in notes:
        process_note_assets(note, conversion_settings.attachment_folder_name, processing_options)

        write_note_to_file(note)



# TODO getting 3 links to test note instead of 2
#  an exmaple here of test 1 - it is in test folder but is also linked to my notes
#  that does not have a file Test-1.md  |[Test 1](../My-Notes/Test-1.md) [Test 1](../test/Test-1.md)


# TODO quoted tect - lines after shift return are nit indented no > symbol i think  <br> is replaced by \n

# TODO write tests
# TODO refactor anything?
# TODO docstrings
# TODO logging - all logging but also add all unrecognised html objects to warning log

if __name__ == '__main__':
    main()
