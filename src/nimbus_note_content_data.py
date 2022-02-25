import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Union

import file_mover
import helper_functions
import html_string_builders
import markdown_string_builders
from note_content_data import FileAttachment
from note_content_data import NoteData, NoteDataWithMultipleContents, NotePaths
from note_content_data import Paragraph
from processing_options import ProcessingOptions


@dataclass
class NimbusIDs:
    workspaces: Dict = field(default_factory=dict)
    folders: Dict = field(default_factory=dict)
    notes: Dict = field(default_factory=dict)

    def add_workspace(self, workspace_id, path):
        self.workspaces[workspace_id] = path

    def add_folder(self, folder_id, path: Union[Path, Set[Path]]):
        if folder_id in self.folders:
            self.folders[folder_id].add(path)
            return

        self.folders[folder_id] = {path}

    def add_note(self, note_id, path: Path):
        if note_id in self.notes:
            self.notes[note_id].add(path)
            return

        self.notes[note_id] = {path}


@dataclass
class NimbusProcessingOptions(ProcessingOptions):
    keep_abc_123_columns: bool


@dataclass
class FileEmbedNimbusHTML(FileAttachment):
    def __post_init__(self):
        self.source_path = Path(self.href)

        # correct the source extension as it is wrong in nimbus html for mp3 files
        if self.source_path.suffix == '.mp3':
            self.source_path = Path(self.href).with_suffix('.mpga')

        if not self.target_filename:
            self.target_filename = self.source_path.name

    def html(self):
        target_path_text = str(self.target_path.as_posix()) if self.target_path else ''
        if target_path_text:
            target_path_text = urllib.parse.quote(target_path_text)

        display_text = self.contents.html()
        if display_text:
            return f'<a href="{target_path_text}">{display_text} - {self.target_filename}</a>'

        return f'<a href="{target_path_text}">{self.target_filename}</a>'

    def markdown(self):
        caption = self.contents.markdown().strip()

        return markdown_string_builders.embed_file(self.processing_options, caption, self.target_path, caption)


@dataclass
class Mention(NoteData, ABC):
    contents: str


@dataclass
class MentionUser(Mention):

    def html(self):
        if helper_functions.is_valid_email(self.contents):
            return f'<a href="mailto:{self.contents}">{self.contents}</a>'

        return f'<a href="">{self.contents}</a>'

    def markdown(self):
        return markdown_string_builders.mail_to_link(self.contents)


@dataclass
class MentionLink(Mention, ABC):
    workspace_id: str
    target_path: Path = field(default=None, init=False)

    @abstractmethod
    def try_to_set_target_path(self, note_paths, nimbus_ids: NimbusIDs, *args, **kwargs):
        """Method to attempt to assign a target path to the link"""


@dataclass
class MentionWorkspace(MentionLink):
    def html(self):
        path = self.target_path if self.target_path else ''

        return html_string_builders.hyperlink(f"{self.contents} ", path)

    def markdown(self):
        path = self.target_path.as_uri() if self.target_path else ''
        return markdown_string_builders.link(self.contents, path)

    def try_to_set_target_path(self, note_paths: NotePaths, nimbus_ids: NimbusIDs, *args, **kwargs):
        self.match_link_to_existing_matched_id(nimbus_ids)

    def match_link_to_existing_matched_id(self, nimbus_ids: NimbusIDs):
        if self.workspace_id in nimbus_ids.workspaces:
            self.target_path = nimbus_ids.workspaces[self.workspace_id]


@dataclass
class MentionFolder(MentionLink):
    folder_id: str
    target_path: set = field(default_factory=set, init=False)
    target_path_absolute: set = field(default_factory=set, init=False)

    def html(self):
        link_text = ''
        if self.target_path:
            for path in sorted(list(self.target_path)):
                path = path if path else ''
                hyper_link = html_string_builders.hyperlink(f"{self.contents} ", path)
                link_text = f'{link_text}{hyper_link}'

        return link_text

    def markdown(self):
        link_text = ''
        if self.target_path_absolute:
            for path in sorted(list(self.target_path_absolute)):
                uri_path = path.as_uri()
                path_link = markdown_string_builders.link(self.contents, uri_path)
                link_text = f"{link_text}{path_link} "

        return f"{link_text}"

    def try_to_set_target_path(self, note_paths, nimbus_ids, *args, **kwargs):
        self.set_target_paths_by_matching_ids(nimbus_ids, note_paths)

        self.match_link_to_mention_text(nimbus_ids, note_paths)

    def set_target_paths_by_matching_ids(self, nimbus_ids, note_paths):
        """
        Set the target_folder paths to paths already matched to by using the folder-ids.

        Match this MentionFolder to an folder-id value that has already been matched to a folder target_path and use
        that id's target_folder to set this links target folder values.

        After text based matched are made between the mention text and the folder names in the source of the notes.
        This second match matched links to folders that were made before a folder was renamed, this allows renamed
        folders to be linked to as long as there was one link to the folder using it's current (new) name in the
        exported data set.

        Parameters
        ----------
        nimbus_ids : NimbusIds
            The nimbus IDs object holds the name of the folder that has been matched to allowing the ID to be used to
            match a folder where the text has not been matched to a folder.
        note_paths : NotePaths
            NotePath object for the note the link being processed is from.  This contains path information required
            to build the path to the mentioned folder.

        """
        if self.folder_id in nimbus_ids.folders:
            target_folders = nimbus_ids.folders[self.folder_id]
            path_to_this_note_folder = Path(note_paths.path_to_note_target)
            for path in target_folders:
                # relative_path = helper_functions.get_relative_path_to_target(path_to_this_note_folder, path)
                relative_path = helper_functions.get_relative_path_to_target(path, path_to_this_note_folder)
                if relative_path:
                    self.target_path.add(relative_path)
                    self.target_path_absolute.add(path)

    def match_link_to_mention_text(self, nimbus_ids, note_paths):
        """
        Set the target_folder paths to paths by matching the text to a folder in the source path.

        Parameters
        ----------
        nimbus_ids : NimbusIds
            The nimbus IDs object holds the name of the folder that has been matched to allowing the ID to be used to
            match a folder where the text has not been matched to a folder.
        note_paths : NotePaths
            NotePath object for the note the link being processed is from.  This contains path information required
            to build the path to the mentioned folder.

        """
        matching_paths = helper_functions.list_directory_paths(note_paths.path_to_source_workspace,
                                                               recursive=True,
                                                               matching_name=self.contents)

        for path in matching_paths:
            dirty_matching_path_relative_to_source = helper_functions.get_relative_path_to_target(
                path,
                note_paths.path_to_source_folder,
            )

            clean_matching_path_relative_to_source = helper_functions.generate_clean_directory_path(
                str(dirty_matching_path_relative_to_source),
                self.processing_options.filename_options,
            )

            this_note_relative_to_target = helper_functions.get_relative_path_to_target(
                note_paths.path_to_note_target,
                note_paths.path_to_target_folder,
            )

            mention_path_relative_to_this_note_folder = helper_functions.get_relative_path_to_target(
                Path(clean_matching_path_relative_to_source),
                this_note_relative_to_target,
            )

            absolute_mention_path = Path(note_paths.path_to_target_folder, clean_matching_path_relative_to_source)

            self.target_path.add(mention_path_relative_to_this_note_folder)

            self.target_path_absolute.add(absolute_mention_path)

        if self.target_path_absolute:
            for path in self.target_path_absolute:
                nimbus_ids.add_folder(self.folder_id, path)


@dataclass
class MentionNote(MentionLink):
    note_id: str
    filename: str = field(default='')
    target_path: set = field(default_factory=set, init=False)

    def html(self):
        link_text = ''
        if self.target_path:
            for path in sorted(list(self.target_path)):
                in_note_folder = ''
                if len(self.target_path) > 1:
                    if path.parent.name:
                        in_note_folder = f' in {path.parent.name}'
                path = urllib.parse.quote(str(path.as_posix())) if path else ''
                hyper_link = html_string_builders.hyperlink(f"{self.contents}{in_note_folder}, ", path)
                link_text = f'{link_text}{hyper_link}'

            return f"{link_text} "

        return html_string_builders.hyperlink(f"{self.contents} - Unable to link to note. ", "")

    def markdown(self):
        link_text = ''
        if self.target_path:
            for path in sorted(list(self.target_path)):
                in_note_folder = ''
                if len(self.target_path) > 1:
                    if path.parent.name:
                        in_note_folder = f' in {path.parent.name}'

                path = urllib.parse.quote(str(path.as_posix()))
                path_link = markdown_string_builders.link(f"{self.contents}{in_note_folder}", path)
                link_text = f"{link_text}{path_link}, "

            return f"{link_text}"

        return markdown_string_builders.link(f'{self.contents} - Unable to link to note', "")

    def try_to_set_target_path(self, note_paths, nimbus_ids: NimbusIDs, dict_of_notes=None, *args, **kwargs):
        self.set_target_paths_by_matching_ids(nimbus_ids, note_paths)

        self.match_link_to_mention_text(nimbus_ids, dict_of_notes, note_paths)

    def set_target_paths_by_matching_ids(self, nimbus_ids, note_paths):
        if self.note_id in nimbus_ids.notes:
            mention_targets = nimbus_ids.notes[self.note_id]

            path_to_this_note = Path(note_paths.path_to_note_target, note_paths.note_target_file_name)

            for mention_target in mention_targets:

                if mention_target.parent == path_to_this_note.parent:
                    self.target_path.add(Path(mention_target.name))  # name is from already cleaned names in nimbus id's
                else:
                    target_folder = helper_functions.get_relative_path_to_target(mention_target.parent,
                                                                                 path_to_this_note.parent,)

                    if target_folder:
                        self.target_path.add(Path(target_folder, mention_target.name))
                        # name is from already cleaned names in nimbus id's are cleaned before being added

    def match_link_to_mention_text(self, nimbus_ids, dict_of_notes, note_paths):

        if self.contents in dict_of_notes:
            notes_to_link_to = dict_of_notes[self.contents]

            for note in notes_to_link_to:
                path_to_mention_note = note.note_paths.path_to_note_target
                where_this_note_is = Path(note_paths.path_to_note_target)

                relative_path_to_mention = helper_functions.get_relative_path_to_target(path_to_mention_note,
                                                                                        where_this_note_is)

                clean_filename = self.get_clean_file_name()

                self.target_path.add(Path(relative_path_to_mention, clean_filename))

                # Now add the note id to nimbus_ids to allow matching of renamed notes
                nimbus_ids.add_note(self.note_id, Path(path_to_mention_note, clean_filename))

                # Now add the workspace id to nimbus_ids
                # we have to check 'if self.workspace_id' is not empty as table mentions do not have a workspace id
                if self.workspace_id and self.workspace_id not in nimbus_ids.workspaces and self.target_path:
                    self.add_workspace_id_to_nimbus_ids(note_paths, nimbus_ids)

    def get_clean_file_name(self):
        target_suffix = file_mover.get_file_suffix_for(self.processing_options.export_format)
        dirty_name = f'{self.contents}{target_suffix}'
        clean_filename = helper_functions.generate_clean_filename(dirty_name,
                                                                  self.processing_options.filename_options)
        return clean_filename

    def add_workspace_id_to_nimbus_ids(self, note_paths, nimbus_ids):
        dirty_note_path_relative_to_source = note_paths.path_to_note_source.relative_to(
            note_paths.path_to_source_folder)

        clean_note_path_relative_to_source = \
            Path(
                helper_functions.generate_clean_directory_path(str(dirty_note_path_relative_to_source),
                                                               self.processing_options.filename_options)
            )

        workspace_path = Path(note_paths.path_to_target_folder,
                              clean_note_path_relative_to_source.parts[0])  # first part is always the workspace name
        nimbus_ids.add_workspace(self.workspace_id, workspace_path)


@dataclass
class NimbusDateItem(NoteData):
    contents: str
    unix_time_seconds: float

    def html(self):
        return f"{self.contents}"

    def markdown(self):
        return f"{self.contents}"


@dataclass
class TableCheckItem(NoteData):
    contents: bool

    def html(self):
        if self.contents:
            return '<input type="checkbox" checked>'

        return '<input type="checkbox">'

    def markdown(self):
        # note return inline HTML because markdown does not support block level items in tables
        inline_html = self.html()
        return f"{inline_html}|"


@dataclass
class TableCollaborator(NoteData):
    contents: str

    def html(self):
        return f'<a href="mailto:{self.contents}">Collaborator - {self.contents}</a>'

    def markdown(self):
        return f"Collaborator - {markdown_string_builders.mail_to_link(self.contents)}"


@dataclass
class EmbedNimbus(NoteData):
    embed_caption: Optional[Paragraph]

    def html(self):
        return f'<p>{self.contents.html()}/p>{self.embed_caption.html()}'

    def markdown(self):
        return f"{self.contents.markdown()}\n{self.embed_caption.markdown()}\n"


@dataclass
class NimbusToggle(NoteDataWithMultipleContents):

    def html(self):
        return html_string_builders.wrap_items_in_tag(self.contents, 'p')

    def markdown(self):
        markdown_text = ''
        for item in self.contents:
            markdown_text = f"{markdown_text}{item.markdown()}"

        return f"{markdown_text}\n"
