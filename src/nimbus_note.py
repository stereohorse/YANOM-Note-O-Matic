from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class NotePaths:
    path_to_note_source: Path = field(default=None, init=False)
    path_to_source_folder: Path = field(default=None, init=False)
    path_to_target_folder: Path = field(default=None, init=False)
    path_to_attachment_folder: Path = field(default=None, init=False)
    path_to_note_target: Path = field(default=None, init=False)
    note_source_file_name: str = field(default=None, init=False)
    note_target_file_name: str = field(default=None, init=False)
    target_suffix: str = field(default=None, init=False)

    def set_note_target_path(self):
        try:
            relative_path_to_note_from_source = self.path_to_note_source.relative_to(self.path_to_source_folder)
            self.path_to_note_target = Path(self.path_to_target_folder, relative_path_to_note_from_source)
        except ValueError as e:
            print(e)
            print(self)

    def set_path_to_attachment_folder(self, attachment_folder_name):
        if not self.path_to_note_target:
            self.set_note_target_path()

        self.path_to_attachment_folder = Path(self.path_to_note_target, attachment_folder_name)


@dataclass
class Document:
    conversion_settings: None
    title: str = ''
    # content: List = field(default_factory=list)
    content_as_text: str = ''
    links: List = field(default_factory=list)  # will be list of tags prob <div> with <a> in them
    tags: List[str] = field(default_factory=list)
    workspace_id: str = ''
    note_id: str = ''
    note_paths: NotePaths = field(default_factory=NotePaths)

    # def markdown(self):
    #     self.content_as_text = ''
    #     for item in self.content:
    #         self.content_as_text = f"{self.content_as_text}{item.markdown()}"
    #
    #     return self.content_as_text

    def find_tags(self):  # list should be built as we scan tags
        if not self.content_as_text:
            self.content_as_text = self.markdown()

        lines = self.content_as_text.splitlines()

        regex = r"^[#][^#\s]\S+"  # this only finds tags at the start of a line

        for count, line in enumerate(lines):
            # allow the first line to be a heading but if a later line is not a tag stop searching
            # this will mean only those tags listed after the title wil be read
            # the next line that is not a tag will stop the search
            if not re.fullmatch(regex, line) and count > 0:
                break
            if not re.fullmatch(regex, line):
                continue
            self.tags.append(re.fullmatch(regex, line).string)

        self.split_tags_if_required()
        self.clean_hash_from_tags()

    def split_tags_if_required(self):
        if self.conversion_settings.split_tags:
            set_tags = {tag for tag_split in self.tags for tag in tag_split.split('/')}
            self.tags = [tag for tag in set_tags]

    def clean_hash_from_tags(self):
        self.tags = [tag.lstrip('#') for tag in self.tags]

    def remove_tags_from_start_of_content_text(self):
        """Remove any lines #-tag from the beginning of the content"""
        lines = self.content_as_text.splitlines()
        regex = r"^[#][^#\s]\S+$"

        new_line_list = [line for line in lines if not re.match(regex, line)]

        return '\n'.join(new_line_list)

    def get_content_with_tags_removed(self):
        if not self.tags:
            self.find_tags()
        return self.remove_tags_from_start_of_content_text()

    def set_title_from_content(self):
        """Set the document object title

        If the first item or second item of content is a TitleItem use the title value.

        """
        if isinstance(self.content[0], TitleItem):
            self.title = self.content[0].title
            return

        if isinstance(self.content[1], TitleItem):
            self.title = self.content[1].title
            return

    def set_list_links_from_content(self):
        self.links = self.find_links()

    def find_links(self):
        links = []
        for item in self.content:
            result = item.get_links()
            if result:
                if isinstance(result, list):
                    links.extend(result)
                    continue
                links.append(result)

        return links

    def add_front_matter_to_content(self):
        front_matter = FrontMatter()

        if self.title:
            front_matter.data['title'] = self.title

        if self.tags:
            front_matter.data['tag'] = self.tags

        self.content = [front_matter, *self.content]