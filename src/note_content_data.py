from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, Union

import frontmatter

import config
import helper_functions
import html_string_builders
import markdown_string_builders
import markdown_string_builders_obsidian
from processing_options import ProcessingOptions


logger = logging.getLogger(f'{config.yanom_globals.app_name}.{__name__}')
logger.setLevel(config.yanom_globals.logger_level)


@dataclass
class NoteData(ABC):
    processing_options: ProcessingOptions
    contents: Any

    @abstractmethod
    def html(self):
        """Generate html content"""

    @abstractmethod
    def markdown(self):
        """Generate markdown content"""

    def find_items(self, class_):
        """
        Return list with self in if instance Type matched the types searched for.  Returns empty list if self does not
        match the Types being searched for. For example find_items(TextItem) or find_items((TextItem, BulletList)),
        for clarity it may be clearer to use  named arguments for example find_items(class_=TextItem)
        or find_items(class_=(TextItem, BulletList))

        Parameters
        ----------
        class_ : single NoteData type or tuple containing NoteData types.
            A single NoteData class type or a tuple containing one or more NoteData types to search for.

        Returns
        -------
        list
            list of NoteData objects, or empty list if no matches found.

        """
        items_found = []
        if isinstance(self, class_):
            items_found.append(self)
        return items_found


@dataclass
class NoteDataContentsString(NoteData, ABC):
    contents: str


@dataclass
class NoteDataWithMultipleContents(NoteData, ABC):
    contents: Iterable[NoteData]

    def find_items(self, class_: Union[Type[NoteData], Tuple[NoteData]]):
        """
        Search the documents contents for objects that match the provided class or classes. return the matching objects
        in a list.  Returns empty list if no objects are found.
        For example find_items(TextItem) or find_items((TextItem, BulletList)), for clarity it may be clearer to use
        named arguments for example find_items(class_=TextItem) or find_items(class_=(TextItem, BulletList))

        Parameters
        ----------
        class_ : single NoteData type or tuple containing NoteData types.
            A single NoteData class type or a tuple containing one or more NoteData types to search for.

        Returns
        -------
        list
            list of NoteData objects, or empty list if no matches found.

        """
        items_found = []

        # search contents of self
        for item in self.contents:
            if isinstance(item, NoteData):
                items_found.extend(item.find_items(class_))
                # .extend as always returns a list even if it is an empty list or single item

        # add self if matching search request
        if isinstance(self, class_):
            items_found.append(self)
        return items_found


@dataclass
class NotePaths:
    path_to_note_source: Path = field(default=None, init=False)  # path to folder where nimbus zip file is found
    path_to_source_folder: Path = field(default=None, init=False)  # conversion_settings.source
    path_to_source_workspace: Path = field(default=None, init=False)  # path to source workspace folder
    path_to_target_workspace: Path = field(default=None, init=False)
    path_to_target_folder: Path = field(default=None, init=False)
    path_to_attachment_folder: Path = field(default=None, init=False)
    path_to_note_target: Path = field(default=None, init=False)
    note_source_file_name: str = field(default=None, init=False)
    note_target_file_name: str = field(default=None, init=False)
    note_target_suffix: str = field(default=None, init=False)

    def set_note_target_path(self, processing_options: ProcessingOptions):
        dirty_relative_path = self.path_to_note_source.relative_to(self.path_to_source_folder)
        clean_relative_path = helper_functions.generate_clean_directory_path(str(dirty_relative_path),
                                                                             processing_options.filename_options)

        self.path_to_note_target = Path(self.path_to_target_folder, clean_relative_path)

    def set_path_to_attachment_folder(self, attachment_folder_name, processing_options):
        if not self.path_to_note_target:
            self.set_note_target_path(processing_options)

        self.path_to_attachment_folder = Path(self.path_to_note_target, attachment_folder_name)


@dataclass
class Note(NoteDataWithMultipleContents):
    conversion_settings: None
    title: str = ''
    tags: List[str] = field(default_factory=list)
    note_paths: NotePaths = field(default_factory=NotePaths)

    def html(self):
        html_text = html_string_builders.join_multiple_items_of_html(self.contents)
        return f'<!doctype html><html lang="en">{html_text}</html>'

    def markdown(self):
        return markdown_string_builders.join_multiple_items(self.contents)

    def find_tags(self):
        tag_text_set = self.get_tags_from_contents()
        self.remove_tags_from_start_of_contents(tag_text_set)
        self.tags = sorted(list(tag_text_set), key=str.lower)
        self.split_tags_if_required()
        self.clean_hash_from_tags()

    def get_tags_from_contents(self):
        """
        Search content for hash tags, #a-tag etc, that are at the start of a line and return a set of those tags.

        Returns
        =======
        set[str]
            Set of #tags identified in the content

        """
        text_items = self.find_items(TextItem)
        tag_text_set = set()

        regex = r"^[#][^#\s]\S+"  # this only finds tags at the start of a line with nothing else on the line

        tag_text_items = [tag_text_item
                          for tag_text_item in text_items
                          if re.fullmatch(regex, tag_text_item.contents)
                          ]

        if tag_text_items:
            tag_text_set = {tag.contents for tag in tag_text_items}

        return tag_text_set

    def remove_tags_from_start_of_contents(self, tag_text_set):
        """
        Remove, by making TextItem contents an empty string, lines of the beginning of the note that are tags.  The
        tags being removed will be the first lines of content, excluding a Title, until the first non-Paragraph object
        or the first Paragraph with a TextItem that does not match one of the tags.

        Parameters
        ==========
        tag_text_set : set

        """
        for item in self.contents[1].contents:
            if not isinstance(item, (Paragraph, Title)):
                break

            # #tags are in a TextItem wrapped in Paragraph, item contents = 1 means only the #tag text is on the line
            if len(item.contents) == 1 and isinstance(item.contents[0], TextItem):

                if item.contents[0].contents in tag_text_set:
                    item.contents[0].contents = ''
                else:
                    break  # if not matching a #tag we must have gone past the first few tag lines

    def split_tags_if_required(self):
        if self.conversion_settings.split_tags:
            set_tags = {tag for tag_split in self.tags for tag in tag_split.split('/')}
            self.tags = [tag for tag in set_tags]

    def clean_hash_from_tags(self):
        self.tags = [tag.lstrip('#') for tag in self.tags]

    def add_front_matter_to_content(self):
        front_matter = FrontMatter(self.processing_options)
        front_matter.format = self.conversion_settings.front_matter_format
        front_matter.tag_prefix = self.conversion_settings.tag_prefix

        if self.title:
            front_matter.contents['title'] = self.title

        if self.tags:
            front_matter.contents['tag'] = self.tags

        front_matter.contents['generator'] = 'YANOM'

        self.contents = [front_matter, *self.contents]


@dataclass
class Head(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.head(self.contents)

    def markdown(self):
        return markdown_string_builders.join_multiple_items(self.contents)


@dataclass
class Body(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.wrap_items_in_tag(self.contents, 'body')

    def markdown(self):
        return markdown_string_builders.join_multiple_items(self.contents)


@dataclass
class SectionContent(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.join_multiple_items_of_html(self.contents)

    def markdown(self):
        markdown_text = markdown_string_builders.join_multiple_items(self.contents)

        return f'{markdown_text}'


@dataclass
class Paragraph(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.wrap_items_in_tag(self.contents, 'p')

    def markdown(self):
        markdown_text = markdown_string_builders.join_multiple_items(self.contents)
        return f"{markdown_text}\n"


@dataclass
class TextItem(NoteDataContentsString):
    contents: str

    def html(self):
        return self.contents

    def markdown(self):
        return self.contents


@dataclass
class HeadingItem(NoteDataWithMultipleContents):
    contents: [NoteData]
    level: int
    id: str

    def html(self):
        return html_string_builders.heading(self.contents, self.id, self.level)

    def markdown(self):
        return markdown_string_builders.heading(self.contents, self.level)


@dataclass
class Title(NoteDataContentsString):
    contents: str

    def html(self):
        return f'<title>{self.contents}</title>'

    def markdown(self):
        return f"# {self.contents}\n"


@dataclass
class ListItem(NoteDataWithMultipleContents, ABC):
    contents: [NoteData]


@dataclass
class BulletListItem(ListItem):
    indent: int

    def html(self):
        return html_string_builders.wrap_items_in_tag(self.contents, 'li')

    def markdown(self):
        return markdown_string_builders.bullet_item(self.contents, self.indent)


@dataclass
class BulletList(NoteDataWithMultipleContents):
    contents: [BulletListItem]

    def html(self):
        return html_string_builders.generate_html_list(self.contents, ordered=False)

    def markdown(self):
        return markdown_string_builders.bullet_list(self.contents)


@dataclass
class NumberedListItem(ListItem):
    indent: int

    def html(self):
        return html_string_builders.wrap_items_in_tag(self.contents, 'li')

    def markdown(self):
        return markdown_string_builders.numbered_list_item(self.contents)


@dataclass
class NumberedList(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.generate_html_list(self.contents, ordered=True)

    def markdown(self):
        return markdown_string_builders.numbered_list(self.contents)


@dataclass
class OutlineItem(NoteData):
    contents: TextItem
    indent: int
    link_id: str

    def html(self):
        link = html_string_builders.anchor_link(self.contents, self.link_id)
        return html_string_builders.wrap_string_in_tag(link, 'li')

    def markdown(self):
        return markdown_string_builders.markdown_anchor_tag_link(self.contents)


@dataclass
class Outline(NoteDataWithMultipleContents):
    contents: [NoteData]
    outline_items: NumberedList

    def html(self):
        return html_string_builders.table_of_contents(self.contents, self.outline_items)

    def markdown(self):
        title_text = markdown_string_builders.join_multiple_items(self.contents)

        title_text = f'## {title_text}\n'
        outline_list_items_text = self.outline_items.markdown()

        return f"{title_text}{outline_list_items_text}\n\n"


@dataclass
class ChecklistItem(ListItem):
    indent: int
    checked: bool

    def html(self):
        return html_string_builders.checklist_item(self.contents, self.checked, self.indent)

    def markdown(self):
        return markdown_string_builders.checklist_item(self.contents, self.checked, self.indent)


@dataclass
class Checklist(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.join_multiple_items_of_html(self.contents)

    def markdown(self):
        return markdown_string_builders.checklist(self.contents)


@dataclass
class ImageAttachment(NoteDataContentsString, ABC):
    contents: str
    href: str
    source_path: Path
    width: str
    height: str
    # processing_options: ProcessingOptions
    filename: str = field(default='', init=False)
    target_path: Path = field(default=None, init=False)
    target_set: bool = field(default=False, init=False)

    def __post_init__(self):
        self.filename = self.source_path.name

    def set_target_path(self, attachment_folder_name: str):
        self.target_path = Path(attachment_folder_name, self.filename)

    def update_target(self, new_target_path: Path):
        self.target_path = new_target_path
        self.filename = new_target_path.name


@dataclass
class ImageEmbed(ImageAttachment):  # img tag

    def html(self):
        return html_string_builders.image_tag(self.contents, self.width, self.height, self.target_path)

    def markdown(self):
        if self.processing_options.markdown_format == 'obsidian':
            return markdown_string_builders_obsidian.embed_image(self.processing_options, self.contents,
                                                                 self.width, self.height, self.target_path)

        return markdown_string_builders.embed_image(self.processing_options, self.contents,
                                                    self.width, self.height, self.target_path)


@dataclass
class FileAttachment(NoteData):
    contents: NoteData
    href: str
    target_filename: str = field(default='')
    source_path: Path = field(default=None)
    target_path: Path = field(default=None)

    def __post_init__(self):
        self.source_path = Path(self.href)
        if not self.target_filename:
            self.target_filename = self.source_path.name

    @abstractmethod
    def html(self):
        """Method to generate HTML content"""

    @abstractmethod
    def markdown(self):
        """Method to generate Markdown content"""

    def set_target_path(self, attachment_folder_name: str):
        self.target_path = Path(attachment_folder_name, self.target_filename)

    def update_target(self, new_target_path):
        self.target_path = new_target_path
        self.target_filename = new_target_path.name


@dataclass
class FileAttachmentCleanHTML(FileAttachment):

    def html(self):
        return html_string_builders.hyperlink(self.contents, self.target_path)

    def markdown(self):
        return markdown_string_builders.link(self.contents, self.target_path)


@dataclass
class Hyperlink(NoteDataContentsString):
    contents: str
    href: str

    def html(self):
        return html_string_builders.hyperlink(self.contents, self.href)

    def markdown(self):
        return markdown_string_builders.link(self.contents, self.href)


@dataclass
class TableHeader(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.build_table_row(self.contents, 'th')

    def markdown(self):
        return markdown_string_builders.pipe_table_header(self.contents)


@dataclass
class TableRow(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.build_table_row(self.contents, 'td')

    def markdown(self):
        return markdown_string_builders.pipe_table_row(self.contents)


@dataclass
class Table(NoteDataWithMultipleContents):
    contents: List[Union[TableHeader, TableRow]]

    def html(self):
        html_text = html_string_builders.wrap_items_in_tag(self.contents, 'table')
        html_text = html_text.replace('<table>', '<table border="1">')
        # add order="1" because if html is later converted in pandoc the table will be kept, else it is lost
        return html_text

    def markdown(self):
        markdown_text = markdown_string_builders.join_multiple_items(self.contents)
        return f'{markdown_text}\n'


@dataclass
class TableItem(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.join_multiple_items_of_html(self.contents)

    def markdown(self):
        return markdown_string_builders.join_multiple_items(self.contents)


@dataclass
class CodeItem(NoteDataContentsString):
    contents: str
    language: str

    def html(self):
        return html_string_builders.pre_code_block(self.contents, self.language)

    def markdown(self):
        return markdown_string_builders.code_block(self.contents, self.language)


@dataclass
class Break(NoteData):
    def html(self):
        return html_string_builders.line_break()

    def markdown(self):
        return '\n'


@dataclass
class BlockQuote(NoteDataWithMultipleContents):
    cite: str = field(default='')

    def html(self):
        return html_string_builders.block_quote(self.contents, self.cite)

    def markdown(self):
        quote_text = markdown_string_builders.block_quote(self.contents, self.cite)
        quote_text = quote_text.replace('\n', '\n> ')
        quote_text = quote_text.rstrip('> ')
        return quote_text


@dataclass
class FrontMatter(NoteData):
    contents: Dict = field(default_factory=dict)
    format: str = field(default='yaml')
    tag_prefix: str = field(default='#')

    def html(self):
        return html_string_builders.meta_tags_from_dict(self.contents)

    def markdown(self):
        return f"{self.create_front_matter()}\n\n"

    def create_front_matter(self):
        if not self.format or self.format == 'none':
            return ''

        if len(self.contents) == 0:  # if there is no meta data do not create an empty header
            return ''

        # if frontmatter.checks(content):
        #     _, content = frontmatter.parse(content)  # remove metadata if pandoc has added it (pandoc v2.13 and above)

        if self.format == 'text':
            return self.generate_plain_text_front_matter()

        front_matter_post = frontmatter.Post('')

        # iterate metadata items rather than using "frontmatter.Post(content, **self._metadata)"
        # because POST init can not accept a meta data field that has a key of 'content' which is common in html
        # and likely in other files as well
        for key, value in self.contents.items():
            front_matter_post[key] = value

        if self.format == 'yaml':
            return frontmatter.dumps(front_matter_post, handler=frontmatter.YAMLHandler())
        if self.format == 'toml':
            return frontmatter.dumps(front_matter_post, handler=frontmatter.TOMLHandler())
        if self.format == 'json':
            return frontmatter.dumps(front_matter_post, handler=frontmatter.JSONHandler())

    def generate_plain_text_front_matter(self):
        text_front_matter = ''
        for key, value in self.contents.items():
            if key == 'tag' or key == 'tags':
                if value is None:  # empty tag metadata
                    continue
                list_of_tags = self.add_tag_prefix(value)
                text_front_matter = f"{text_front_matter}{key}: {', '.join(list_of_tags)}"
                continue

            text_front_matter = f'{text_front_matter}{key}: {value}\n'

        return f'{text_front_matter}'

    def add_tag_prefix(self, tags):
        tags = [f'{self.tag_prefix}{tag}' for tag in tags]

        return tags


@dataclass
class TextColorItem(NoteDataContentsString):
    contents: str
    plain_text: str

    def html(self):
        return self.contents

    def markdown(self):
        return self.contents


@dataclass
class TextFormatItem(NoteDataWithMultipleContents):
    contents: []
    format: str

    def html(self):
        if self.format == 'b':  # replace deprecated b with strong
            self.format = 'strong'
        return html_string_builders.format_text(self.contents, self.format)

    def markdown(self):
        return markdown_string_builders.formatted_text(self.contents, self.format)


@dataclass
class UnrecognisedTag(NoteDataContentsString):
    contents: str  # html version
    text: str  # plain text version

    def __post_init__(self):
        logger.warning(f"unrecognised HTML\n{self.contents}\n")

    def html(self):
        if self.processing_options.unrecognised_tag_format == 'html':
            return self.contents

        return f'<p>{self.text}</p>'

    def markdown(self):
        if self.processing_options.unrecognised_tag_format == 'html':
            return f'\n {self.contents}\n'

        # if not html then just return plain text
        return f'\n {self.text}\n'


@dataclass
class Caption(NoteDataWithMultipleContents):
    contents: [NoteData]

    def html(self):
        return html_string_builders.join_multiple_items_of_html(self.contents)

    def markdown(self):
        return markdown_string_builders.caption(self.contents)


@dataclass
class Figure(NoteDataWithMultipleContents):
    contents: Tuple[ImageAttachment, Optional[Caption]]

    def html(self):
        return html_string_builders.figure(self.contents)

    def markdown(self):
        final_contents = [item for item in self.contents if item is not None]
        if final_contents:
            return markdown_string_builders.join_multiple_items(list(final_contents))

        return ''
