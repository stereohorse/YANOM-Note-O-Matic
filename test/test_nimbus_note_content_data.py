
"""Property based testing for note_content_data classes"""
from dataclasses import dataclass, field
from pathlib import Path

import helper_functions
import html_nimbus_extractors
from bs4 import BeautifulSoup
import pytest

import html_data_extractors
from nimbus_note_content_data import EmbedNimbus, FileEmbedNimbusHTML, MentionFolder, MentionNote, MentionUser, \
    MentionWorkspace, \
    NimbusDateItem, NimbusIDs, NimbusToggle, TableCheckItem, TableCollaborator
from note_content_data import BlockQuote, Body, BulletList, Head, HeadingItem, Hyperlink, ImageEmbed, \
    NimbusNote, NotePaths, NumberedList, Paragraph, \
    SectionContent, \
    TextColorItem, \
    TextFormatItem, TextItem, Title
from embeded_file_types import EmbeddedFileTypes
from processing_options import ProcessingOptions


@pytest.fixture
def processing_options() -> ProcessingOptions:
    embed_these_document_types = ['md', 'pdf']
    embed_these_image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
    embed_these_audio_types = ['mp3', 'webm', 'wav', 'm4a', 'ogg', '3gp', 'flac']
    embed_these_video_types = ['mp4', 'webm', 'ogv']
    embed_files = EmbeddedFileTypes(embed_these_document_types, embed_these_image_types,
                                    embed_these_audio_types, embed_these_video_types)

    filename_options = helper_functions.FileNameOptions(max_length=255,
                                                        allow_unicode=True,
                                                        allow_uppercase=True,
                                                        allow_non_alphanumeric=True,
                                                        allow_spaces=False,
                                                        space_replacement='-')
    export_format = 'obsidian'
    unrecognised_tag_format = 'html'

    return ProcessingOptions(embed_files,
                             export_format,
                             unrecognised_tag_format,
                             filename_options,
                             )


@pytest.fixture
def conversion_settings():
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

    conversion_setting = ConversionSettings()

    return conversion_setting


class TestNimbusIDs:
    def test_add_workspace(self):
        my_ids = NimbusIDs()

        my_ids.add_workspace('1234', Path('my_path'))

        assert my_ids.workspaces['1234'] == Path('my_path')

    def test_add_folder(self):
        my_ids = NimbusIDs()

        my_ids.add_folder('1234', Path('my_path'))
        my_ids.add_folder('1234', Path('my_2nd_path'))

        assert my_ids.folders['1234'] == {Path('my_path'), Path('my_2nd_path')}

    def test_add_mpte(self):
        my_ids = NimbusIDs()

        my_ids.add_note('1234', Path('my_path'))
        my_ids.add_note('1234', Path('my_2nd_path'))

        assert my_ids.notes['1234'] == {Path('my_path'), Path('my_2nd_path')}


class TestFileEmbedNimbusHTML:
    def test_post_init(self, processing_options):
        file = FileEmbedNimbusHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.mp3',
                                       'target_filename.mp3',
                                       )

        assert file.source_path == Path('href_folder/file.mpga')
        assert file.target_filename == 'target_filename.mp3'

    def test_html_output_no_contents(self, processing_options):
        file = FileEmbedNimbusHTML(processing_options,
                                       TextItem(processing_options, ''),
                                       'href_folder/file.pdf',
                                       )

        file.update_target(Path('new_folder/new_name.pdf'))

        expected = '<a href="new_folder/new_name.pdf">new_name.pdf</a>'
        result = file.html()
        assert result == expected

    def test_html_output(self, processing_options):
        file = FileEmbedNimbusHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       )

        file.update_target(Path('new_folder/new_name.pdf'))

        expected = '<a href="new_folder/new_name.pdf">my_contents - new_name.pdf</a>'
        result = file.html()
        assert result == expected

    def test_markdown_output(self, processing_options):
        file = FileEmbedNimbusHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       )

        file.update_target(Path('new_folder/new_name.pdf'))

        expected = '![my_contents](new_folder/new_name.pdf)\n*my_contents*\n'
        result = file.markdown()
        assert result == expected


class TestMentionUser:
    @pytest.mark.parametrize(
        'email, expected', [
            (
                    'hello',
                    'Mention hello',
            ),
            (
                    'hello.user@gmail.com',
                    'Mention [hello.user@gmail.com](mailto:hello.user@gmail.com)',
            ),
        ],
    )
    def test_mention_user_markdown_output(self, email, expected, processing_options):
        mention = MentionUser(processing_options, email)

        assert mention.markdown() == expected

    @pytest.mark.parametrize(
        'email, expected', [
            (
                    'hello',
                    '<a href="">hello</a>',
            ),
            (
                    'hello.user@gmail.com',
                    '<a href="mailto:hello.user@gmail.com">hello.user@gmail.com</a>',
            ),
        ],
    )
    def test_mention_user_html_output(self, email, expected, processing_options):
        mention = MentionUser(processing_options, email)

        assert mention.html() == expected


class TestMentionWorkspace:
    def test_mention_workspace_markdown_output_target_not_set(self, processing_options):
        mention = MentionWorkspace(processing_options, 'my_contents', '1234')
        expected = '[my_contents]()'
        assert mention.markdown() == expected

    def test_mention_workspace_markdown_output_target_set(self, processing_options):
        mention = MentionWorkspace(processing_options, 'my_contents', '1234')
        mention.target_path = Path('/my target')
        expected = '[my_contents](file:///my%20target)'
        assert mention.markdown() == expected

    def test_try_to_set_target_path(self, processing_options):
        mention = MentionWorkspace(processing_options, 'my_contents', '1234')
        note_paths = NotePaths()
        nimbus_ids = NimbusIDs()
        nimbus_ids.add_workspace('1234', Path('my_target_path'))
        mention.try_to_set_target_path(note_paths, nimbus_ids)

        assert mention.target_path == Path('my_target_path')

    def test_try_to_set_target_path_id_not_in_nimbus_ids(self, processing_options):
        mention = MentionWorkspace(processing_options, 'my_contents', '1234')
        note_paths = NotePaths()
        nimbus_ids = NimbusIDs()
        nimbus_ids.add_workspace('5678', Path('my_target_path'))
        mention.try_to_set_target_path(note_paths, nimbus_ids)

        assert mention.target_path is None

    def test_mention_workspace_html_output_target_not_set(self, processing_options):
        mention = MentionWorkspace(processing_options, 'my_contents', '1234')
        expected = '<a href="">my_contents </a>'
        assert mention.html() == expected

    def test_mention_workspace_html_output_target_set(self, processing_options):
        mention = MentionWorkspace(processing_options, 'my_contents', '1234')
        mention.target_path = Path('/my target')
        expected = '<a href="/my target">my_contents </a>'
        assert mention.html() == expected


class TestMentionFolder:
    def test_mention_folder_markdown_output_target_not_set(self, processing_options):
        mention = MentionFolder(processing_options, 'my_contents', '1234', '5678')
        expected = ''
        assert mention.markdown() == expected

    def test_mention_workspace_markdown_output_target_set(self, processing_options):
        mention = MentionFolder(processing_options, 'my_contents', '1234', '5678')
        mention.target_path_absolute = {Path('/my target_1'), Path('/my target_2')}
        expected = '[my_contents](file:///my%20target_1) [my_contents](file:///my%20target_2) '
        assert mention.markdown() == expected

    def test_set_target_paths_by_matching_ids(self, processing_options):
        mention = MentionFolder(processing_options, 'my_contents', '1234', '5678')
        note_paths = NotePaths()
        note_paths.path_to_note_target = Path('target path/this_note_folder')
        nimbus_ids = NimbusIDs()
        nimbus_ids.add_folder('5678', Path('target path/my target path'))
        mention.set_target_paths_by_matching_ids(nimbus_ids, note_paths)

        assert mention.target_path == {Path('../my target path')}

    def test_match_link_to_mention_text(self, processing_options, tmp_path):
        Path(tmp_path, 'source/workspace/my mention folder').mkdir(parents=True)

        mention = MentionFolder(processing_options, 'my mention folder', '1234', '5678')

        note_paths = NotePaths()
        note_paths.path_to_source_workspace = Path(tmp_path, 'source/workspace')
        note_paths.path_to_target_folder = Path(tmp_path, 'target')
        note_paths.path_to_source_folder = Path(tmp_path, 'source')
        note_paths.path_to_note_target = Path(tmp_path, 'target/workspace/this_note_folder')

        nimbus_ids = NimbusIDs()

        mention.match_link_to_mention_text(nimbus_ids, note_paths)

        assert mention.target_path == {Path('../my-mention-folder')}

    def test_try_to_set_target_path(self, processing_options, tmp_path):
        Path(tmp_path, 'source/workspace/my mention folder').mkdir(parents=True)

        mention = MentionFolder(processing_options, 'my mention folder', '1234', '5678')

        note_paths = NotePaths()
        note_paths.path_to_source_workspace = Path(tmp_path, 'source/workspace')
        note_paths.path_to_target_workspace = Path(tmp_path, 'target/workspace')
        note_paths.path_to_target_folder = Path(tmp_path, 'target')
        note_paths.path_to_source_folder = Path(tmp_path, 'source')
        note_paths.path_to_note_target = Path(tmp_path, 'target/workspace/this_note_folder')

        nimbus_ids = NimbusIDs()
        nimbus_ids.add_folder('5678', Path(tmp_path, 'target/workspace/my-mention-folder'))

        mention.try_to_set_target_path(note_paths, nimbus_ids)

        assert mention.target_path == {Path('../my-mention-folder')}

    def test_try_to_set_target_path_when_same_folder_as_note_is_in(self, processing_options, tmp_path):
        Path(tmp_path, 'source/workspace/my mention folder').mkdir(parents=True)

        mention = MentionFolder(processing_options, 'my mention folder', '1234', '5678')

        note_paths = NotePaths()
        note_paths.path_to_source_workspace = Path(tmp_path, 'source/workspace')
        note_paths.path_to_target_workspace = Path(tmp_path, 'target/workspace')
        note_paths.path_to_target_folder = Path(tmp_path, 'target')
        note_paths.path_to_source_folder = Path(tmp_path, 'source')
        note_paths.path_to_note_target = Path(tmp_path, 'target/workspace/my-mention-folder')

        nimbus_ids = NimbusIDs()
        nimbus_ids.add_folder('5678', Path(tmp_path, 'target/workspace/my-mention-folder'))

        mention.try_to_set_target_path(note_paths, nimbus_ids)

        assert mention.target_path == {Path('.')}

    def test_mention_folder_html_output_target_not_set(self, processing_options):
        mention = MentionFolder(processing_options, 'my_contents', '1234', '5678')
        expected = ''
        assert mention.html() == expected

    def test_mention_workspace_html_output_target_set(self, processing_options):
        mention = MentionFolder(processing_options, 'my_contents', '1234', '5678')
        mention.target_path = {Path('/my target_1'), Path('/my target_2')}
        expected = '<a href="/my target_1">my_contents </a><a href="/my target_2">my_contents </a>'
        assert mention.html() == expected


class TestMentionNote:
    def test_mention_note_markdown_output_target_not_set(self, processing_options):
        mention = MentionNote(processing_options, 'my_contents', 'ws-1234', 'note-5678')
        expected = '[my_contents - Unable to link to note]()'
        assert mention.markdown() == expected

    def test_mention_workspace_markdown_output_target_set(self, processing_options):
        mention = MentionNote(processing_options, 'my_contents', 'ws-1234', 'note-5678')
        mention.target_path = {Path('folder1/note.md'), Path('folder2/note.md')}
        expected = '[my_contents in folder1](folder1/note.md), [my_contents in folder2](folder2/note.md), '
        mention_markdown = mention.markdown()
        assert mention_markdown == expected

    def test_set_target_paths_by_matching_ids_target_note_in_same_folder_as_this_note(self, processing_options):
        mention = MentionNote(processing_options, 'my_contents', 'ws-1234', 'note-5678')

        note_paths = NotePaths()
        note_paths.path_to_note_target = Path('target-path/same_note_folder')
        note_paths.note_target_file_name = 'my-note.md'

        nimbus_ids = NimbusIDs()
        nimbus_ids.add_note('note-5678', Path('target-path/same_note_folder/my-note.md'))

        mention.set_target_paths_by_matching_ids(nimbus_ids, note_paths)

        assert mention.target_path == {Path('my-note.md')}

    def test_set_target_paths_by_matching_ids_target_note_in_different_folder_from_this_note(self, processing_options):
        mention = MentionNote(processing_options, 'my_contents', 'ws-1234', 'note-5678')

        note_paths = NotePaths()
        note_paths.path_to_note_target = Path('target-path/different_note_folder')
        note_paths.note_target_file_name = 'different-note.md'

        nimbus_ids = NimbusIDs()
        nimbus_ids.add_note('note-5678', Path('target-path/mention_note_folder/mention-note.md'))

        mention.set_target_paths_by_matching_ids(nimbus_ids, note_paths)

        assert mention.target_path == {Path('../mention_note_folder/mention-note.md')}

    def test_match_link_to_mention_text_same_folder_as_note(self, processing_options, conversion_settings):
        mention = MentionNote(processing_options, 'my-mention-note', 'ws-1234', 'note-5678')

        # Mention note is the note this link links to
        mention_note = NimbusNote(processing_options, contents=[], conversion_settings=conversion_settings)
        mention_note.title = 'my-mention-note'

        mention_note_paths = NotePaths()
        # mention_note_paths.path_to_source_workspace = Path('source/workspace')
        # mention_note_paths.path_to_target_folder = Path('target')
        mention_note_paths.path_to_source_folder = Path('source')
        mention_note_paths.path_to_note_target = Path('target/workspace/mention_note_folder')

        mention_note.note_paths = mention_note_paths

        dict_of_notes = {'my-mention-note': [mention_note]}

        # this is the note the mention link is in
        this_note_note_paths = NotePaths()
        this_note_note_paths.path_to_source_folder = Path('source')
        this_note_note_paths.path_to_target_folder = Path('target')
        this_note_note_paths.path_to_note_source = Path('source/workspace/mention_note_folder')
        this_note_note_paths.path_to_note_target = Path('target/workspace/mention_note_folder')

        nimbus_ids = NimbusIDs()

        mention.match_link_to_mention_text(nimbus_ids, dict_of_notes, this_note_note_paths)

        assert mention.target_path == {Path('my-mention-note.md')}
        assert len(nimbus_ids.notes) == 1
        assert len(nimbus_ids.workspaces) == 1

    def test_match_link_to_mention_text_different_folder_as_note(self, processing_options, conversion_settings):
        mention = MentionNote(processing_options, 'my-mention-note', 'ws-1234', 'note-5678')

        # Mention note is the note this link links to
        mention_note = NimbusNote(processing_options, contents=[], conversion_settings=conversion_settings)
        mention_note.title = 'my-mention-note'

        mention_note_paths = NotePaths()
        # mention_note_paths.path_to_source_workspace = Path('source/workspace')
        # mention_note_paths.path_to_target_folder = Path('target')
        mention_note_paths.path_to_source_folder = Path('source')
        mention_note_paths.path_to_note_target = Path('target/workspace/mention_note_folder')

        mention_note.note_paths = mention_note_paths

        dict_of_notes = {'my-mention-note': [mention_note]}

        # this is the note the mention link is in
        this_note_note_paths = NotePaths()
        this_note_note_paths.path_to_source_folder = Path('source')
        this_note_note_paths.path_to_target_folder = Path('target')
        this_note_note_paths.path_to_note_source = Path('source/workspace/this_note_folder')
        this_note_note_paths.path_to_note_target = Path('target/workspace/this_note_folder')

        nimbus_ids = NimbusIDs()

        mention.match_link_to_mention_text(nimbus_ids, dict_of_notes, this_note_note_paths)

        assert mention.target_path == {Path('../mention_note_folder/my-mention-note.md')}
        assert len(nimbus_ids.notes) == 1
        assert len(nimbus_ids.workspaces) == 1

    def test_try_to_set_target_path_no_id_exists(self, processing_options):
        mention = MentionNote(processing_options, 'my-mention-note', 'ws-1234', 'note-5678')

        # Mention note is the note this link links to
        mention_note = NimbusNote(processing_options, contents=[], conversion_settings=conversion_settings)
        mention_note.title = 'my-mention-note'

        mention_note_paths = NotePaths()
        # mention_note_paths.path_to_source_workspace = Path('source/workspace')
        # mention_note_paths.path_to_target_folder = Path('target')
        mention_note_paths.path_to_source_folder = Path('source')
        mention_note_paths.path_to_note_target = Path('target/workspace/mention_note_folder')

        mention_note.note_paths = mention_note_paths

        dict_of_notes = {'my-mention-note': [mention_note]}

        # this is the note the mention link is in
        this_note_note_paths = NotePaths()
        this_note_note_paths.path_to_source_folder = Path('source')
        this_note_note_paths.path_to_target_folder = Path('target')
        this_note_note_paths.path_to_note_source = Path('source/workspace/this_note_folder')
        this_note_note_paths.path_to_note_target = Path('target/workspace/this_note_folder')

        nimbus_ids = NimbusIDs()

        mention.try_to_set_target_path(this_note_note_paths, nimbus_ids, dict_of_notes)

        assert mention.target_path == {Path('../mention_note_folder/my-mention-note.md')}
        assert len(nimbus_ids.notes) == 1
        assert len(nimbus_ids.workspaces) == 1

    def test_try_to_set_target_path_when_different_folder_as_note_and_id_exists(self, processing_options):
        mention = MentionNote(processing_options, 'my_contents', 'ws-1234', 'note-5678')

        note_paths = NotePaths()
        note_paths.path_to_note_target = Path('target-path/different_note_folder')
        note_paths.note_target_file_name = 'different-note.md'

        dict_of_notes = {'a-different-note': []}

        nimbus_ids = NimbusIDs()
        nimbus_ids.add_note('note-5678', Path('target-path/mention_note_folder/mention-note.md'))

        mention.try_to_set_target_path(note_paths, nimbus_ids, dict_of_notes)

        assert mention.target_path == {Path('../mention_note_folder/mention-note.md')}

    def test_mention_folder_html_output_target_not_set(self, processing_options):
        mention = MentionNote(processing_options, 'my_contents', 'ws-1234', 'note-5678')
        expected = '<a href="">my_contents - Unable to link to note. </a>'
        assert mention.html() == expected

    def test_mention_workspace_html_output_target_set(self, processing_options):
        mention = MentionNote(processing_options, 'my_contents', '1234', '5678')
        mention.target_path = {Path('folder1/note.md'), Path('folder2/note.md')}
        expected = '<a href="folder1/note.md">my_contents in folder1, </a><a href="folder2/note.md">my_contents in folder2, </a> '
        assert mention.html() == expected


class TestNimbusDateItem:
    def test_date_item_html_output(self, processing_options):
        date_item = NimbusDateItem(processing_options, '2022-01-05 23:20:07', 1641424807.59)
        expected = '2022-01-05 23:20:07'
        result = date_item.html()
        assert result == expected

    def test_date_item_markdown_output(self, processing_options):
        date_item = NimbusDateItem(processing_options, '2022-01-05 23:20:07', 1641424807.59)
        expected = '2022-01-05 23:20:07'
        result = date_item.markdown()
        assert result == expected


class TestTableCheckItem:
    @pytest.mark.parametrize(
        'contents, expected', [
            (
                    True,
                    '<input type="checkbox" checked>',
            ),
            (
                    False,
                    '<input type="checkbox">',
            ),
        ],
    )
    def test_table_check_item_html_output(self, contents, expected, processing_options):
        item = TableCheckItem(processing_options, contents)
        result = item.html()
        assert result == expected

    @pytest.mark.parametrize(
        'contents, expected', [
            (
                    True,
                    '<input type="checkbox" checked>',
            ),
            (
                    False,
                    '<input type="checkbox">',
            ),
        ],
    )
    def test_date_item_markdown_output(self, contents, expected, processing_options):
        item = TableCheckItem(processing_options, contents)
        result = item.markdown()
        assert result == expected


class TestTableCollaborator:
    @pytest.mark.parametrize(
        'contents, expected', [
            (
                    'user.user@gmail.com',
                    '<a href="mailto:user.user@gmail.com">Collaborator - user.user@gmail.com</a>',
            ),
        ],
    )
    def test_table_check_item_html_output(self, contents, expected, processing_options):
        item = TableCollaborator(processing_options, contents)
        result = item.html()
        assert result == expected

    @pytest.mark.parametrize(
        'contents, expected', [
            (
                    'user.user@gmail.com',
                    'Collaborator - Mention [user.user@gmail.com](mailto:user.user@gmail.com)',
            ),
        ],
    )
    def test_date_item_markdown_output(self, contents, expected, processing_options):
        item = TableCollaborator(processing_options, contents)
        result = item.markdown()
        assert result == expected


class TestEmbedNimbus:
    def test_embed_nimbus_html_output(self, processing_options):
        embed_caption = Paragraph(processing_options, [TextItem(processing_options, 'caption')])
        contents = BlockQuote(processing_options, [TextItem(processing_options, 'some html')])
        item = EmbedNimbus(processing_options, contents, embed_caption)
        result = item.html()
        assert result == '<p><blockquote>some html</blockquote>/p><p>caption</p>'

    def test_embed_nimbus_markdown_output(self, processing_options):
        embed_caption = Paragraph(processing_options, [TextItem(processing_options, 'caption')])
        contents = BlockQuote(processing_options, [TextItem(processing_options, 'some html')])
        item = EmbedNimbus(processing_options, contents, embed_caption)
        result = item.markdown()
        assert result == '> some html\n\ncaption\n\n'


class TestNimbusToggle:
    def test_embed_nimbus_html_output(self, processing_options):
        contents = [TextItem(processing_options, 'some text')]
        item = NimbusToggle(processing_options, contents)
        result = item.html()
        assert result == '<p>some text</p>'

    def test_embed_nimbus_markdown_output(self, processing_options):
        contents = [TextItem(processing_options, 'some text')]
        item = NimbusToggle(processing_options, contents)
        result = item.markdown()
        assert result == 'some text\n'


class TestExtractFromTag:

    @pytest.mark.parametrize(
        'html, tag_name, expected_type, expected_result_html', [
            ('<head><title>My Title</title></head>', 'head', Head,
             """<head><title>My Title</title><style>
    table, th, td {
      border: 1px solid black;
      border-collapse: collapse;
    }
    </style></head>"""),
            ('<body><title>My Title</title></body>', 'body', Body, '<body><title>My Title</title></body>'),
            ('<h2>My heading</h2>', 'h2', HeadingItem, '<h2>My heading</h2>'),
            ('<span class="font-color" style="color: rgb(237, 84, 84);">This is coloured.</span>',
             'span',
             TextColorItem,
             '<span style="color: rgb(237, 84, 84);">This is coloured.</span>'
             ),
            ('<strong>bold text</strong>', 'strong', TextFormatItem, '<strong>bold text</strong>'),
            ('<div><title>My Title</title></div>', 'div', Paragraph, '<p><title>My Title</title></p>'),
            ('<section><title>My Title</title></section>', 'section', SectionContent, '<title>My Title</title>'),
            ('<blockquote cite="my-citation">My Quote</blockquote>',
             'blockquote',
             BlockQuote,
             '<blockquote cite="my-citation">My Quote</blockquote>'
             ),
            ('<title>My Title</title>', 'title', Title, '<title>My Title</title>'),
    #         ('<p>Some Text</p>', 'p', list, '<p>Some Text</p>'),
    #         ('<i>Some Text</i>', 'i', list, '<i>Some Text</i>'),
            ('<img src="image.png" alt="alt text" width="100" height="200">',
             'img',
             ImageEmbed,
             '<img src="" alt="alt text" width="100" height="200">',
             # NOTE at this point target_path is not set so src will be empty
             ),
            ('<a href="image.png">link display text</a>', 'a', Hyperlink, '<a href="image.png">link display text</a>'),
            ('<iframe>My iframe</iframe>', 'iframe', TextItem, '<iframe>My iframe</iframe>'),
            # ('<span>a span</span>', 'span', list, ''),
        ],
    )
    def test_property_test_html_input_to_output(self, html, tag_name, expected_type,
                                                expected_result_html, processing_options):

        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find(tag_name)
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert isinstance(result, expected_type)
        result_html = result.html()
        assert result_html == expected_result_html

    @pytest.mark.parametrize(
        'html, tag_name, expected_type, expected_result_html', [
            ('<p>Some Text</p>', 'p', list, 'Some Text'),
            ('<i>Some Text</i>', 'i', list, 'Some Text'),
            ('<span>a span</span>', 'span', list, 'a span'),
        ],
    )
    def test_property_test_html_input_to_output_where_result_is_list(self, html, tag_name, expected_type,
                                                expected_result_html, processing_options):

        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find(tag_name)
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert isinstance(result, expected_type)
        result_html = result[0].html()
        assert result_html == expected_result_html


class TestGenerateHTMLList:
    def test_generate_html_list_via_ol_tags(self):
        html = '<ol><li>number one</li><li>number two</li><ol><li>number <strong>bold</strong> 2-1</li><li>number <em>Italic</em> 2-2</li></ol><li>number <strong><em>bold italic</em></strong> 3 below is an empty numbered item</li><li><br></li></ol>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find()

        result = html_data_extractors.extract_numbered_list_from_ol_tag(tag, processing_options,
                                                                        html_nimbus_extractors.extract_from_nimbus_tag)

        assert isinstance(result, NumberedList)
        assert result.html() == html

    def test_generate_html_list_via_ul_tags(self):
        html = '<ul><li>bullet 1</li><ul><li>sub <strong>bullet</strong> two, below is an empty bullet</li><li><br></li></ul><li>bullet 2</li></ul>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find()

        result = html_data_extractors.extract_bullet_list_from_ul_tag(tag, processing_options,
                                                                        html_nimbus_extractors.extract_from_nimbus_tag)

        assert isinstance(result, BulletList)
        assert result.html() == html


