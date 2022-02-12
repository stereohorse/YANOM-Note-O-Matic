from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup
import pytest

from embeded_file_types import EmbeddedFileTypes
import helper_functions
import html_data_extractors
import html_nimbus_extractors
from note_content_data import Body
from note_content_data import Caption, Checklist, ChecklistItem, CodeItem
from note_content_data import Figure, FileAttachmentCleanHTML, FrontMatter
from note_content_data import Head
from note_content_data import ImageEmbed
from note_content_data import Note, NotePaths, NumberedList, NumberedListItem
from note_content_data import Outline, OutlineItem
from note_content_data import Paragraph
from note_content_data import Table, TableHeader, TableItem, TableRow, TextFormatItem, TextItem
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


class TestNoteDataWithMultipleContents:
    def test_note_data_find_items_in_contents(self):
        html = '<ol><li>number one</li><li>number two</li><ol><li>number <strong>bold</strong> 2-1</li><li>number <em>Italic</em> 2-2</li></ol><li>number <strong><em>bold italic</em></strong> 3 below is an empty numbered item</li><li><br></li></ol>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('ol')
        numbered_list = html_data_extractors.extract_from_tag(tag, processing_options)

        assert isinstance(numbered_list, NumberedList)

        result = numbered_list.find_items(class_=NumberedListItem)

        assert len(result) == 6
        for item in result:
            assert isinstance(item, NumberedListItem)


class TestNoteData:
    def test_note_data_find_self(self):
        item = TextItem(processing_options, 'Hello')

        result = item.find_items(class_=TextItem)

        assert len(result) == 1
        assert isinstance(result[0], TextItem)


class TestFigure:
    def test_figure(self, processing_options):
        image_object = ImageEmbed(processing_options, "an image", "image.png", Path("image.pdf"), "200", "300")
        image_object.target_path = Path("image.png")
        caption_object = Caption(processing_options, [TextItem(processing_options, "a caption")])

        contents = (image_object, caption_object)
        figure = Figure(processing_options, contents)

        expected = '![an image|200x300](image.png)\n*a caption*\n\n'

        result = figure.markdown()

        assert result == expected

    def test_figure_none_for_caption(self, processing_options):
        image_object = ImageEmbed(processing_options, "an image", "image.png", Path("image.pdf"), "200", "300")
        image_object.target_path = Path("image.png")
        caption_object = None

        contents = (image_object, caption_object)
        figure = Figure(processing_options, contents)

        expected = '![an image|200x300](image.png)\n'

        result = figure.markdown()

        assert result == expected

    def test_figure_none_for_image(self, processing_options):
        image_object = None

        caption_object = Caption(processing_options, [TextItem(processing_options, "a caption")])

        contents = (image_object, caption_object)
        figure = Figure(processing_options, contents)

        expected = '*a caption*\n\n'

        result = figure.markdown()
        assert result == expected

    def test_figure_none_for_image_and_caption(self, processing_options):
        image_object = None
        caption_object = None
        contents = (image_object, caption_object)
        figure = Figure(processing_options, contents)

        expected = ''

        result = figure.markdown()

        assert result == expected


class TestTextFormatItem:
    def test_html_with_b_as_format(self, processing_options):
        text_format_item = TextFormatItem(processing_options, [TextItem(processing_options, 'some text')], 'b')

        expected = '<strong>some text</strong>'
        result = text_format_item.html()

        assert result == expected


class TestOutlineItem:
    def test_markdown_deneration(self, processing_options):
        item = OutlineItem(processing_options, TextItem(processing_options, 'some text'), 2, 'my-id')

        expected = '[some text](#some-text)'
        result = item.markdown()

        assert result == expected


class TestNimbusOutline:
    def test_nimbus_outline_html_output(self, processing_options):
        """Test passing correct tag"""
        html = '<div class="outline" id="b406348235_764"><div contenteditable="false" class="outline-container"><div class="outline-content-wrapper "><div class="outline-header "><div class="outline-left"><div class="outline-expand-icon "> </div></div><div class="outline-name">Outline</div></div><div class="outline-body"><ul class="outline-list outline-numbered"><li class="outline-list-item level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1009">Testing lists</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1042">Testing inserted files</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1086">Testing a table</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1130">There are only 3 levels of heading in nimbus</a></li><li class="outline-list-item level-0"><a href="#b788977277_831">heading 1</a></li><li class="outline-list-item level-1"><a href="#b788977277_860">heading 2</a></li><li class="outline-list-item level-2"><a href="#b788977277_889">heading 3</a></li><li class="outline-list-item level-0"><a href="#b1023299123_1757">heading with italic text</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1218">Testing the horizontal line</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1266">Link and embeds</a></li><li class="outline-list-item level-1"><a href="#b992245780_93">Code Blocks</a></li><li class="outline-list-item level-1"><a href="#b992245780_132">Nimbus mentions</a></li><li class="outline-list-item level-1"><a href="#b992245780_175">Quoted text</a></li><li class="outline-list-item level-1"><a href="#b992245780_196">Hints</a></li><li class="outline-list-item level-1"><a href="#b992245780_220">Toggle block</a></li><li class="outline-list-item level-1"><a href="#b2183561539_350">Outline (effectively a linked TOC)</a></li><li class="outline-list-item level-1"><a href="#b992245780_450">Nimbus button</a></li><li class="outline-list-item level-1"><a href="#b992245780_478">Text formatting</a></li><li class="outline-list-item level-1"><a href="#b942953620_901">Testing inserted mp3</a></li><li class="outline-list-item level-1"><a href="#b942953620_1059">Test block sections - may or may not export!</a></li><li class="outline-list-item level-1"><a href="#b216345050_62">Adventures in Exporting from Nimbus Notes...</a></li><li class="outline-list-item level-0"><a href="#b942953620_969">This is the end of the file</a></li></ul></div></div></div></div>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        expected = """<h2>Outline</h2><h4><ol><li><a href="#b1023299123_950">A test note of page content</a></li><ol><li><a href="#b1023299123_1009">Testing lists</a></li><li><a href="#b1023299123_1042">Testing inserted files</a></li><li><a href="#b1023299123_1086">Testing a table</a></li><li><a href="#b1023299123_1130">There are only 3 levels of heading in nimbus</a></li></ol><li><a href="#b788977277_831">heading 1</a></li><ol><li><a href="#b788977277_860">heading 2</a></li><ol><li><a href="#b788977277_889">heading 3</a></li></ol></ol><li><a href="#b1023299123_1757">heading with italic text</a></li><ol><li><a href="#b1023299123_1218">Testing the horizontal line</a></li><li><a href="#b1023299123_1266">Link and embeds</a></li><li><a href="#b992245780_93">Code Blocks</a></li><li><a href="#b992245780_132">Nimbus mentions</a></li><li><a href="#b992245780_175">Quoted text</a></li><li><a href="#b992245780_196">Hints</a></li><li><a href="#b992245780_220">Toggle block</a></li><li><a href="#b2183561539_350">Outline (effectively a linked TOC)</a></li><li><a href="#b992245780_450">Nimbus button</a></li><li><a href="#b992245780_478">Text formatting</a></li><li><a href="#b942953620_901">Testing inserted mp3</a></li><li><a href="#b942953620_1059">Test block sections - may or may not export!</a></li><li><a href="#b216345050_62">Adventures in Exporting from Nimbus Notes...</a></li></ol><li><a href="#b942953620_969">This is the end of the file</a></li></ol></h4>"""

        result = html_nimbus_extractors.extract_from_nimbus_outline(tag, processing_options)

        assert isinstance(result, Outline)
        assert result.html() == expected

    def test_nimbus_outline_markdown_output(self, processing_options):
        """Test passing correct tag"""
        html = '<div class="outline" id="b406348235_764"><div contenteditable="false" class="outline-container"><div class="outline-content-wrapper "><div class="outline-header "><div class="outline-left"><div class="outline-expand-icon "> </div></div><div class="outline-name">Outline</div></div><div class="outline-body"><ul class="outline-list outline-numbered"><li class="outline-list-item level-0"><a href="#b1023299123_950">A test note of page content</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1009">Testing lists</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1042">Testing inserted files</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1086">Testing a table</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1130">There are only 3 levels of heading in nimbus</a></li><li class="outline-list-item level-0"><a href="#b788977277_831">heading 1</a></li><li class="outline-list-item level-1"><a href="#b788977277_860">heading 2</a></li><li class="outline-list-item level-2"><a href="#b788977277_889">heading 3</a></li><li class="outline-list-item level-0"><a href="#b1023299123_1757">heading with italic text</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1218">Testing the horizontal line</a></li><li class="outline-list-item level-1"><a href="#b1023299123_1266">Link and embeds</a></li><li class="outline-list-item level-1"><a href="#b992245780_93">Code Blocks</a></li><li class="outline-list-item level-1"><a href="#b992245780_132">Nimbus mentions</a></li><li class="outline-list-item level-1"><a href="#b992245780_175">Quoted text</a></li><li class="outline-list-item level-1"><a href="#b992245780_196">Hints</a></li><li class="outline-list-item level-1"><a href="#b992245780_220">Toggle block</a></li><li class="outline-list-item level-1"><a href="#b2183561539_350">Outline (effectively a linked TOC)</a></li><li class="outline-list-item level-1"><a href="#b992245780_450">Nimbus button</a></li><li class="outline-list-item level-1"><a href="#b992245780_478">Text formatting</a></li><li class="outline-list-item level-1"><a href="#b942953620_901">Testing inserted mp3</a></li><li class="outline-list-item level-1"><a href="#b942953620_1059">Test block sections - may or may not export!</a></li><li class="outline-list-item level-1"><a href="#b216345050_62">Adventures in Exporting from Nimbus Notes...</a></li><li class="outline-list-item level-0"><a href="#b942953620_969">This is the end of the file</a></li></ul></div></div></div></div>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        expected = """## Outline
1. [A test note of page content](#a-test-note-of-page-content)
	1. [Testing lists](#testing-lists)
	2. [Testing inserted files](#testing-inserted-files)
	3. [Testing a table](#testing-a-table)
	4. [There are only 3 levels of heading in nimbus](#there-are-only-3-levels-of-heading-in-nimbus)
2. [heading 1](#heading-1)
	1. [heading 2](#heading-2)
		1. [heading 3](#heading-3)
3. [heading with italic text](#heading-with-italic-text)
	1. [Testing the horizontal line](#testing-the-horizontal-line)
	2. [Link and embeds](#link-and-embeds)
	3. [Code Blocks](#code-blocks)
	4. [Nimbus mentions](#nimbus-mentions)
	5. [Quoted text](#quoted-text)
	6. [Hints](#hints)
	7. [Toggle block](#toggle-block)
	8. [Outline (effectively a linked TOC)](#outline-(effectively-a-linked-toc))
	9. [Nimbus button](#nimbus-button)
	10. [Text formatting](#text-formatting)
	11. [Testing inserted mp3](#testing-inserted-mp3)
	12. [Test block sections - may or may not export!](#test-block-sections---may-or-may-not-export!)
	13. [Adventures in Exporting from Nimbus Notes...](#adventures-in-exporting-from-nimbus-notes...)
4. [This is the end of the file](#this-is-the-end-of-the-file)


"""

        result = html_nimbus_extractors.extract_from_nimbus_outline(tag, processing_options)

        assert isinstance(result, Outline)
        assert result.markdown() == expected


@pytest.mark.parametrize(
    'checked, indent, expected, ', [
        (True, 1,
         '<p style= "padding-left: 30px;"><input checked type="checkbox">This is check one</p>'),
        (False, 2,
         '<p style= "padding-left: 60px;"><input type="checkbox">This is check one</p>'),
    ],
)
def test_checklist_item_for_html_output(checked, indent, expected, processing_options):
    contents = [TextItem(processing_options, "This is "), TextItem(processing_options, "check"),
                TextItem(processing_options, " one")]

    checklist_item = ChecklistItem(processing_options, contents, indent, checked)

    result = checklist_item.html()

    assert result == expected

    assert result == expected


def test_checklist_for_html_output(processing_options):
    check1 = ChecklistItem(processing_options,
                           [TextItem(processing_options, "This is "),
                            TextItem(processing_options, "check"),
                            TextItem(processing_options, " one")],
                           1, True)
    check2 = ChecklistItem(processing_options,
                           [TextItem(processing_options, "This is "),
                            TextItem(processing_options, "check"),
                            TextItem(processing_options, " two")],
                           2, False)

    checklist = Checklist(processing_options, [check1, check2])

    expected = """<p style= "padding-left: 30px;"><input checked type="checkbox">This is check one</p><p style= "padding-left: 60px;"><input type="checkbox">This is check two</p>"""
    result = checklist.html()

    assert result == expected


class TestImageAttachment:
    def test_set_target_path(self, processing_options):
        image = ImageEmbed(processing_options, 'contents', 'href_folder/filename.png',
                           Path('source_folder/filename.png'),
                           '200', '300')
        image.set_target_path('attachment_folder')

        assert image.target_path == Path('attachment_folder', image.filename)

    def test_update_target(self, processing_options):
        image = ImageEmbed(processing_options, 'contents', 'href_folder/filename.png',
                           Path('source_folder/filename.png'),
                           '200', '300')

        image.update_target(Path('new_folder/new_name.png'))

        assert image.target_path == Path('new_folder', 'new_name.png')
        assert image.filename == 'new_name.png'


class TestFileAttachment:
    def test_post_init(self, processing_options):
        file = FileAttachmentCleanHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       'target_filename.pdf',
                                       )

        assert file.source_path == Path('href_folder/file.pdf')
        assert file.target_filename == 'target_filename.pdf'

    def test_post_init_no_target_filename_provided(self, processing_options):
        file = FileAttachmentCleanHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       )

        assert file.source_path == Path('href_folder/file.pdf')
        assert file.target_filename == 'file.pdf'

    def test_set_target_path(self, processing_options):
        file = FileAttachmentCleanHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       )

        file.set_target_path('attachment_folder')

        assert file.target_path == Path('attachment_folder', 'file.pdf')

    def test_update_target(self, processing_options):
        file = FileAttachmentCleanHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       )

        file.update_target(Path('new_folder/new_name.pdf'))

        assert file.target_path == Path('new_folder', 'new_name.pdf')
        assert file.target_filename == 'new_name.pdf'

    def test_html_output(self, processing_options):
        file = FileAttachmentCleanHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       )

        file.update_target(Path('new_folder/new_name.pdf'))

        expected = '<a href="new_folder/new_name.pdf">my_contents</a>'
        result = file.html()
        assert result == expected

    def test_markdown_output(self, processing_options):
        file = FileAttachmentCleanHTML(processing_options,
                                       TextItem(processing_options, 'my_contents'),
                                       'href_folder/file.pdf',
                                       )

        file.update_target(Path('new_folder/new_name.pdf'))

        expected = '[my_contents](new_folder/new_name.pdf)'
        result = file.markdown()
        assert result == expected


class TestTableHeader:
    def test_html_output(self, processing_options):
        contents = [
            TableItem(processing_options, [TextItem(processing_options, 'Column 1')]),
            TableItem(processing_options, [TextItem(processing_options, 'Column 2')]),
        ]

        header_row = TableHeader(processing_options, contents)

        expected = "<tr><tr><th>Column 1</th><th>Column 2</th></tr>"

        result = header_row.html()

        assert result == expected


class TestTableRow:
    def test_html_output(self, processing_options):
        contents = [
            TableItem(processing_options, [TextItem(processing_options, 'Column 1')]),
            TableItem(processing_options, [TextItem(processing_options, 'Column 2')]),
        ]

        row = TableRow(processing_options, contents)

        expected = "<tr><tr><td>Column 1</td><td>Column 2</td></tr>"

        result = row.html()

        assert result == expected


class TestTable:
    def test_table_html(self, processing_options):
        contents = [
            TableItem(processing_options, [TextItem(processing_options, 'Column 1')]),
            TableItem(processing_options, [TextItem(processing_options, 'Column 2')]),
        ]

        header_row = TableHeader(processing_options, contents)

        row_contents = [
            TableItem(processing_options, [TextItem(processing_options, 'Row 1')]),
            TableItem(processing_options, [TextItem(processing_options, 'Row 2')]),
        ]

        row = TableRow(processing_options, row_contents)

        table = Table(processing_options, [header_row, row])

        expected = '<table><tr><tr><th>Column 1</th><th>Column 2</th></tr><tr><tr><td>Row 1</td><td>Row 2</td></tr></table>'

        result = table.html()

        assert result == expected

    def test_table_markdown(self, processing_options):
        contents = [
            TableItem(processing_options, [TextItem(processing_options, 'Column 1')]),
            TableItem(processing_options, [TextItem(processing_options, 'Column 2')]),
        ]

        header_row = TableHeader(processing_options, contents)

        row_contents = [
            TableItem(processing_options, [TextItem(processing_options, 'Row 1')]),
            TableItem(processing_options, [TextItem(processing_options, 'Row 2')]),
        ]

        row = TableRow(processing_options, row_contents)

        table = Table(processing_options, [header_row, row])

        expected = '\n|Column 1|Column 2|\n|--|--|\n|Row 1|Row 2|\n\n'

        result = table.markdown()

        assert result == expected


class TestTableItem:
    def test_table_item_html(self, processing_options):
        item = TableItem(processing_options, [TextItem(processing_options, 'Column 1')])

        expected = 'Column 1'

        result = item.html()

        assert result == expected

    def test_table_item_markdown(self, processing_options):
        item = TableItem(processing_options, [TextItem(processing_options, 'Column 1')])

        expected = 'Column 1'

        result = item.markdown()

        assert result == expected


class TestCodeItem:
    def test_html_output(self, processing_options):
        code = CodeItem(processing_options, 'This is code', "python")

        expected = '<pre data-python>This is code</pre>'

        result = code.html()

        assert result == expected

    def test_markdown_output(self, processing_options):
        code = CodeItem(processing_options, 'This is code', "python")

        expected = '```python\nThis is code\n```\n'

        result = code.markdown()

        assert result == expected


class TestFrontMatter:
    @pytest.mark.parametrize(
        'front_mater_format, contents, expected', [
            (
                    '',
                    {'title': 'my title', 'tag': ['tag1, tag2']},
                    '\n\n',
            ),
            (
                    'text',
                    {'title': 'my title', 'tag': ['tag1, tag2']},
                    'title: my title\ntag: $tag1, tag2\n\n',
            ),
            (
                    "yaml",
                    {'title': 'my title', 'tag': ['tag1, tag2']},
                    '---\ntag:\n- tag1, tag2\ntitle: my title\n---\n\n',
            ),
            (
                    "toml",
                    {'title': 'my title', 'tag': ['tag1, tag2']},
                    '+++\ntitle = "my title"\ntag = [ "tag1, tag2",]\n\n+++\n\n',
            ),
            (
                    "json",
                    {'title': 'my title', 'tag': ['tag1, tag2']},
                    '{\n    "title": "my title",\n    "tag": [\n        "tag1, tag2"\n    ]\n}\n\n',
            ),
            (
                    "json",
                    {},
                    '\n\n',
            ),
            (
                    "text",
                    {},
                    '\n\n',
            ),
            (
                    "text",
                    {'title': 'my title', 'tag': None},
                    'title: my title\n\n\n',
            ),
        ],
    )
    def test_front_matter_markdown_output(self, front_mater_format, contents, expected, processing_options):
        front = FrontMatter(processing_options)
        front.contents = contents
        front.format = front_mater_format
        front.tag_prefix = '$'

        result = front.markdown()

        assert result == expected

    def test_front_matter_html_output(self, processing_options):
        front = FrontMatter(processing_options)
        front.contents = {'title': 'my title', 'tag': ['tag1, tag2']}
        front.format = 'yaml'

        expected = '<meta name="title" content="my title"/><meta name="tag" content="tag1, tag2"/>'

        result = front.html()

        assert result == expected


class TestNote:
    def test_note_html(self, processing_options, conversion_settings):
        contents = [
            Paragraph(processing_options, [TextItem(processing_options, '#tag1')]),
            Paragraph(processing_options, [TextItem(processing_options, '#tag2')]),
            Paragraph(processing_options, [TextItem(processing_options, 'some text')]),
        ]
        note = Note(processing_options, contents, conversion_settings, 'My Note')

        expected = '<!doctype html><html lang="en"><p>#tag1</p><p>#tag2</p><p>some text</p></html>'

        result = note.html()

        assert result == expected

    def test_note_markdown(self, processing_options, conversion_settings):
        contents = [
            Paragraph(processing_options, [TextItem(processing_options, '#tag1')]),
            Paragraph(processing_options, [TextItem(processing_options, '#tag2')]),
            Paragraph(processing_options, [TextItem(processing_options, 'some text')]),
        ]
        note = Note(processing_options, contents, conversion_settings, 'My Note')

        expected = '#tag1\n#tag2\nsome text\n'

        result = note.markdown()

        assert result == expected

    def test_get_tags_from_contents(self, processing_options, conversion_settings):
        contents = [
            Paragraph(processing_options, [TextItem(processing_options, '#tag1')]),
            Paragraph(processing_options, [TextItem(processing_options, '#tag2')]),
            Paragraph(processing_options, [TextItem(processing_options, 'some text')]),
        ]
        note = Note(processing_options, contents, conversion_settings, 'My Note')

        expected = {'#tag1', '#tag2'}

        result = note.get_tags_from_contents()

        assert result == expected

    def test_get_tags_from_contents_no_tags_in_content(self, processing_options, conversion_settings):
        contents = [
            Paragraph(processing_options, [TextItem(processing_options, 'some text')]),
            Paragraph(processing_options, [TextItem(processing_options, 'some more text')]),
            Paragraph(processing_options, [TextItem(processing_options, 'even more text')]),
        ]
        note = Note(processing_options, contents, conversion_settings, 'My Note')

        expected = set()

        result = note.get_tags_from_contents()

        assert result == expected

    def test_find_tags_stop_when_not_a_tag(self, processing_options, conversion_settings):
        contents = [
            Head(processing_options, [TextItem(processing_options, 'title')]),
            Body(processing_options,
                 [
                     Paragraph(processing_options, [TextItem(processing_options, '#tag1/tag3')]),
                     Paragraph(processing_options, [TextItem(processing_options, '#tag2')]),
                     Paragraph(processing_options, [TextItem(processing_options, 'some text')]),
                 ]
                 )
        ]

        note = Note(processing_options, contents, conversion_settings, 'My Note')

        note.find_tags()

        assert set(note.tags) == {'tag1', 'tag2', 'tag3'}

    def test_find_tags_stop_when_not_a_paragraph_or_title_item(self, processing_options, conversion_settings):
        contents = [
            Head(processing_options, [TextItem(processing_options, 'title')]),
            Body(processing_options,
                 [
                     Paragraph(processing_options, [TextItem(processing_options, '#tag1/tag3')]),
                     Paragraph(processing_options, [TextItem(processing_options, '#tag2')]),
                     TextItem(processing_options, 'my title'),
                 ]
                 )
        ]

        note = Note(processing_options, contents, conversion_settings, 'My Note')

        note.find_tags()

        assert set(note.tags) == {'tag1', 'tag2', 'tag3'}

    def test_find_tags_keep_tag_content_with_more_than_tag_on_it(self, processing_options, conversion_settings):
        contents = [
            Head(processing_options, [TextItem(processing_options, 'title')]),
            Body(processing_options,
                 [
                     Paragraph(processing_options, [TextItem(processing_options, '#tag1/tag3')]),
                     Paragraph(processing_options,
                               [TextItem(processing_options, '#tag2'),
                                TextItem(processing_options, ' extra content on tag line')
                                ]
                               ),
                     TextItem(processing_options, 'my title'),
                 ]
                 )
        ]

        note = Note(processing_options, contents, conversion_settings, 'My Note')

        note.find_tags()

        expected = 'title\n#tag2 extra content on tag line\nmy title'

        assert note.markdown() == expected

    def test_find_tags_do_not_split_tags(self, processing_options, conversion_settings):
        contents = [
            Head(processing_options, [TextItem(processing_options, 'title')]),
            Body(processing_options,
                 [
                     Paragraph(processing_options, [TextItem(processing_options, '#tag1/tag3')]),
                     Paragraph(processing_options, [TextItem(processing_options, '#tag2')]),
                     TextItem(processing_options, 'my title'),
                 ]
                 )
        ]

        conversion_settings.split_tags = False
        note = Note(processing_options, contents, conversion_settings, 'My Note')

        note.find_tags()

        assert set(note.tags) == {'tag1/tag3', 'tag2'}

    def test_add_front_matter_to_content(self, processing_options, conversion_settings):
        contents = [
            Head(processing_options, [TextItem(processing_options, 'title')]),
            Body(processing_options,
                 [
                     Paragraph(processing_options, [TextItem(processing_options, '#tag1/tag3')]),
                     Paragraph(processing_options, [TextItem(processing_options, '#tag2')]),
                     TextItem(processing_options, 'my title'),
                 ]
                 )
        ]

        conversion_settings.split_tags = False
        note = Note(processing_options, contents, conversion_settings, 'My Note')

        note.find_tags()

        note.add_front_matter_to_content()

        expected = '---\ngenerator: YANOM\ntag:\n- tag1/tag3\n- tag2\ntitle: My Note\n---\n\ntitle\n\nmy title'
        result = note.markdown()
        assert result == expected


class NotePath:
    pass


class TestNotePaths:
    def test_set_note_target_path(self, processing_options):
        note_paths = NotePaths()
        note_paths.path_to_note_source = Path('source_folder/my folder source')
        note_paths.path_to_source_folder = Path('source_folder')
        note_paths.path_to_target_folder = Path('target_folder')
        note_paths.set_note_target_path(processing_options)
        assert note_paths.path_to_note_target == Path('target_folder/my-folder-source')

    def test_set_path_to_attachment_folder(self, processing_options):
        note_paths = NotePaths()
        note_paths.path_to_note_source = Path('source_folder/my folder source')
        note_paths.path_to_source_folder = Path('source_folder')
        note_paths.path_to_target_folder = Path('target_folder')
        note_paths.set_path_to_attachment_folder('attachment_folder', processing_options)

        assert note_paths.path_to_attachment_folder == Path('target_folder/my-folder-source/attachment_folder')
