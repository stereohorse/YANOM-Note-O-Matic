from pathlib import Path

import html_data_extractors
from bs4 import BeautifulSoup
import pytest

import helper_functions
import html_string_builders
from embeded_file_types import EmbeddedFileTypes
from note_content_data import Caption, HeadingItem, ImageEmbed, NumberedList, OutlineItem, TextItem

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


def test_wrap_string_in_tag():
    result = html_string_builders.wrap_string_in_tag('My String', 'mytag')
    assert result == '<mytag>My String</mytag>'


class TestWrapItemsInTag:
    def test_wrap_items_in_tag(self, processing_options):
        items = [TextItem(processing_options, 'item1'), TextItem(processing_options, 'item2')]
        result = html_string_builders.wrap_items_in_tag(items, 'mytag')
        assert result == '<mytag>item1item2</mytag>'

    def test_wrap_items_in_tag_empty_list_of_items(self):
        items = []
        result = html_string_builders.wrap_items_in_tag(items, 'mytag')
        assert result == ''


class TestTableOfContents:
    def test_table_of_contents(self, processing_options):
        title_contents = [TextItem(processing_options, 'My '), TextItem(processing_options, 'Title')]
        items = NumberedList(processing_options, [OutlineItem(processing_options,TextItem(processing_options, 'Item1'), 0, '1234'),
                 OutlineItem(processing_options, TextItem(processing_options, 'Item2'), 1, '2345'),
                 ])

        expected = '<h2>My Title</h2><h4><ol><li><a href="1234">Item1</a></li><ol><li><a href="2345">Item2</a></li></ol></ol></h4>'
        result = html_string_builders.table_of_contents(title_contents, items)

        assert result == expected

    def test_table_of_contents_empty_items(self, processing_options):
        title_contents = []
        items = NumberedList(processing_options, [])

        expected = '<h2></h2><h4><ol></ol></h4>'
        result = html_string_builders.table_of_contents(title_contents, items)

        assert result == expected


def test_anchor_link(processing_options):
    contents = TextItem(processing_options, 'Item1')
    link_id = '1234'

    expected = '<a href="1234">Item1</a>'
    result = html_string_builders.anchor_link(contents, link_id)

    assert result == expected

@pytest.mark.parametrize(
    'checked, indent, expected', [
        (True, 0,
         '<p><input checked type="checkbox">My Check Item</p>'),
        (False, 1,
         '<p style= "padding-left: 30px;"><input type="checkbox">My Check Item</p>'),
        (True, 2,
         '<p style= "padding-left: 60px;"><input checked type="checkbox">My Check Item</p>'),
    ],
)
def test_checklist_item(checked, indent, expected, processing_options):
    contents = [TextItem(processing_options, 'My '), TextItem(processing_options, 'Check Item')]

    result = html_string_builders.checklist_item(contents, checked, indent)

    assert result == expected


@pytest.mark.parametrize(
    'language, contents, expected', [
        ("", "This is\nSome code",
         '<pre>This is\nSome code</pre>'),
        ("python", 'Print("hello")\nPrint("world")',
         '<pre data-python>Print("hello")\nPrint("world")</pre>'),
    ],
)
def test_pre_code_block(language, contents, expected):
    result = html_string_builders.pre_code_block(contents, language)

    assert result == expected

@pytest.mark.parametrize(
    'contents, expected', [
        ({'key1': 'value1', 'key2': 'value2'},
         '<meta name="key1" content="value1"/><meta name="key2" content="value2"/>'),
        ({'key1': 'value1', 'key2': ['value2', 'value3']},
         '<meta name="key1" content="value1"/><meta name="key2" content="value2, value3"/>'),
        ({},
         ''),
    ],
)
def test_meta_tags_from_dict(contents, expected):
    result = html_string_builders.meta_tags_from_dict(contents)

    assert result == expected


@pytest.mark.parametrize(
    'row_type, expected', [
        ('th',
         '<tr><tr><th>item1</th><th>item2</th></tr>'),
        ('td',
         '<tr><tr><td>item1</td><td>item2</td></tr>'),
    ],
)
def test_build_table_row(row_type, expected, processing_options):
    items = [TextItem(processing_options, 'item1'), TextItem(processing_options, 'item2')]
    result = html_string_builders.build_table_row(items, row_type)

    assert result == expected


class TestFigure:
    def test_figure(self, processing_options):
        image_object = ImageEmbed(processing_options, "an image", "image.png", Path("image.pdf"), "200", "300" )
        image_object.target_path = Path("image.png")
        caption_object = Caption(processing_options, [TextItem(processing_options, "a caption")])

        expected = '<figure><img src="image.png" alt="an image" width="200" height="300"><figcaption>a caption</figcaption></figure>'

        result = html_string_builders.figure((image_object, caption_object))

        assert result == expected

    def test_figure_none_for_caption(self, processing_options):
        image_object = ImageEmbed(processing_options, "an image", "image.png", Path("image.pdf"), "200", "300")
        image_object.target_path = Path("image.png")
        caption_object = None

        expected = '<img src="image.png" alt="an image" width="200" height="300">'

        result = html_string_builders.figure((image_object, caption_object))

        assert result == expected

    def test_figure_none_for_image(self, processing_options):
        image_object = None

        caption_object = caption_object = Caption(processing_options, [TextItem(processing_options, "a caption")])

        expected = '<figure><figcaption>a caption</figcaption></figure>'

        result = html_string_builders.figure((image_object, caption_object))

        assert result == expected

    def test_figure_none_for_image_and_caption(self):
        image_object = None
        caption_object = None

        expected = ''

        result = html_string_builders.figure((image_object, caption_object))

        assert result == expected