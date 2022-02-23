from pathlib import Path

import helper_functions
import html_nimbus_extractors
import markdown_string_builders
from bs4 import BeautifulSoup
import pytest

from embeded_file_types import EmbeddedFileTypes
import html_data_extractors
from note_content_data import BlockQuote, Body
from note_content_data import Checklist, ChecklistItem
from note_content_data import Head, HeadingItem, Hyperlink
from note_content_data import ImageEmbed
from note_content_data import Paragraph
from note_content_data import SectionContent
from note_content_data import TableHeader, TableRow, TextColorItem
from note_content_data import TextFormatItem, TextItem, Title
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


class TestExtractFromTag:

    @pytest.mark.parametrize(
        'html, tag_name, expected_type, expected_result_markdown', [
            ('<head><title>My Title</title></head>', 'head', Head,
             """# My Title\n"""),
            ('<body><title>My Title</title></body>', 'body', Body, '# My Title\n'),
            ('<h2>My heading</h2>', 'h2', HeadingItem, '## My heading\n'),
            ('<span class="font-color" style="color: rgb(237, 84, 84);">This is coloured.</span>',
             'span',
             TextColorItem,
             '<span style="color: rgb(237, 84, 84);">This is coloured.</span>'
             ),
            ('<strong>bold text</strong>', 'strong', TextFormatItem, '**bold text**'),
            ('<div><title>My Title</title></div>', 'div', Paragraph, '# My Title\n\n'),
            ('<section><title>My Title</title></section>', 'section', SectionContent, '# My Title\n'),
            ('<blockquote cite="my-citation">My Quote</blockquote>',
             'blockquote',
             BlockQuote,
             '> My Quote\n> [source](my-citation)\n'
             ),
            ('<title>My Title</title>', 'title', Title, '# My Title\n'),
            ('<img src="image.png" alt="alt text" width="100" height="200">',
             'img',
             ImageEmbed,
             '<img src="" alt="alt text" width="100" height="200">\n',
                # NOTE at this point target_path is not set so src will be empty
                # also there can be no ! in front of the link as the target suffix is needed for that to be set
             ),
            ('<a href="image.png">link display text</a>', 'a', Hyperlink, '[link display text](image.png)'),
            ('<iframe>My iframe</iframe>', 'iframe', TextItem, '<iframe>My iframe</iframe>'),
        ],
    )
    def test_property_test_html_input_to_markdown_output(self, html, tag_name, expected_type,
                                                         expected_result_markdown, processing_options):
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find(tag_name)
        processing_options.export_format = 'md'
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert isinstance(result, expected_type)
        assert result.markdown() == expected_result_markdown

    @pytest.mark.parametrize(
        'html, target_path, expected_result_markdown', [
            ('<img src="image.png" alt="alt text" width="100" height="200">',
             Path('image.png'),
             '<img src="image.png" alt="alt text" width="100" height="200">\n',
             ),
            ('<img src="image.png" alt="alt text" width="100">',
             Path('image.png'),
             '<img src="image.png" alt="alt text" width="100">\n',
             ),
            ('<img src="image.png" alt="alt text" height="200">',
             Path('image.png'),
             '<img src="image.png" alt="alt text" height="200">\n',
             ),
            ('<img src="image.png" alt="alt text">\n',
             Path('image.png'),
             '![alt text](image.png)\n',
             ),
            ('<img src="image.xyz" alt="alt text" width="100" height="200">',
             Path('image.xyz'),
             '<img src="image.xyz" alt="alt text" width="100" height="200">\n',
             ),
            ('<img src="image.xyz" alt="alt text" width="100">',
             Path('image.xyz'),
             '<img src="image.xyz" alt="alt text" width="100">\n',
             ),
            ('<img src="image.xyz" alt="alt text" height="200">',
             Path('image.xyz'),
             '<img src="image.xyz" alt="alt text" height="200">\n',
             ),
            ('<img src="image.xyz" alt="alt text">',
             Path('image.xyz'),
             '[alt text](image.xyz)\n',
             ),
            ('<img src="" alt="alt text" width="100" height="200">',
             None,
             '<img src="" alt="alt text" width="100" height="200">\n',
             ),
            ('<img src="" alt="alt text" width="100" >',
             None,
             '<img src="" alt="alt text" width="100">\n',
             ),
            ('<img src="" alt="alt text"  height="200">',
             None,
             '<img src="" alt="alt text" height="200">\n',
             ),
            ('<img src="" alt="alt text">',
             None,
             '[alt text]()\n',
             ),
        ],
    )
    def test_image_embed_to_markdown(self, html, target_path, expected_result_markdown, processing_options):
        processing_options.export_format = 'md'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('img')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        result.target_path = target_path

        assert result.markdown() == expected_result_markdown

    @pytest.mark.parametrize(
        'html, expected_result_markdown', [
            ('<a href="http://www.google.com">google</a>',
             '[google](http://www.google.com)',
             ), ('<a href="image.pdf">A file link</a>',
                 '[A file link](image.pdf)',
                 ),
            ('<a href="">A file link</a>',
             '[A file link]()',
             ),
            ('<a href=""></a>',
             '[]()',
             ),
        ],
    )
    def test_link(self, html, expected_result_markdown, processing_options):
        processing_options.export_format = 'md'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('a')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert result.markdown() == expected_result_markdown


@pytest.mark.parametrize(
    'alt_text, target_path, caption, expected_result_markdown', [
        ('A file link that should embed',
         Path('image.pdf'),
         'A caption\n',
         '![A file link that should embed](image.pdf)\n*A caption*\n'
         ),
        ('A file link that should embed',
         Path('image.pdf'),
         'A caption',
         '![A file link that should embed](image.pdf)\n*A caption*\n'
         ),
        ('A file link that should embed',
         Path('image.pdf'),
         '',
         '![A file link that should embed](image.pdf)\n'
         ),
        ('A file link that should not embed',
         Path(''),
         '',
         '[A file link that should not embed](.)\n'
         ),
        ('A file link that should not embed',
         None,
         '',
         '[A file link that should not embed]()\n'
         ),
        ('A file link that should not embed',
         Path('image.xyz'),
         'A caption',
         '[A file link that should not embed](image.xyz)\n*A caption*\n'
         ),
    ],
)
def test_embed_file(alt_text, target_path, caption, expected_result_markdown, processing_options):
    result = markdown_string_builders.embed_file(processing_options, alt_text, target_path, caption)

    assert result == expected_result_markdown


@pytest.mark.parametrize(
    'email, expected, ', [
        ('user@gmail.com',
         "Mention [user@gmail.com](mailto:user@gmail.com)"),
        ('user-gmail.com',
         "Mention user-gmail.com"),

    ],
)
def test_mail_to_link(email, expected):
    result = markdown_string_builders.mail_to_link(email)

    assert result == expected


@pytest.mark.parametrize(
    'text, expected, ', [
        ('1989. was a good year',
         '1989\\. was a good year'),
        ('1989 was a good year',
         '1989 was a good year'),
    ],
)
def test_escape_leading_number_if_required(text, expected):
    result = markdown_string_builders.escape_leading_number_if_required(text)

    assert result == expected


def test_bullet_list(processing_options):
    html = """<ul><li>bullet 1</li><ul><li>sub <strong>bullet</strong> two, below is an empty bullet</li><li><br></li></ul><li>bullet 2</li></ul>"""
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('ul')

    expected = "- bullet 1\n\t- sub **bullet** two, below is an empty bullet\n\t- \n\n- bullet 2\n\n"

    result = html_data_extractors.extract_bullet_list_from_ul_tag(tag, processing_options,
                                                                  html_nimbus_extractors.extract_from_nimbus_tag)

    assert result.markdown() == expected


def test_bullet_item(processing_options):
    contents = [TextItem(processing_options, "Bullet")]
    indent_level = 1

    expected = "\t- Bullet"

    result = markdown_string_builders.bullet_item(contents, indent_level)

    assert result == expected


def test_numbered_list(processing_options):
    html = """<ol><li>Number 1</li><ol><li>sub <strong>Number</strong> 1-2, below is an empty number</li><li></li></ol><li>Number 2</li></ol>"""
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('ol')

    expected = """1. Number 1\n\t1. sub **Number** 1-2, below is an empty number\n\t2. \n2. Number 2\n"""

    result = html_data_extractors.extract_numbered_list_from_ol_tag(tag, processing_options,
                                                                    html_nimbus_extractors.extract_from_nimbus_tag)

    assert result.markdown() == expected


def test_numbered_list_item(processing_options):
    contents = [TextItem(processing_options, "1989. was a good year")]

    expected = "1989\\. was a good year"

    result = markdown_string_builders.numbered_list_item(contents)

    assert result == expected


@pytest.mark.parametrize(
    'heading, link_id, link_format, expected', [
        (
                'This is a heading ',
                '1234',
                'gfm',
                "[This is a heading](#this-is-a-heading)",
        ),
        (
                'This is a heaçding ',
                '1234',
                'gfm',
                "[This is a heaçding](#this-is-a-hea-ding)",
        ),
        (
                '1.2.3. This is a heading ',
                '1234',
                'gfm',
                "[1.2.3. This is a heading](#123-this-is-a-heading)",
        ),
        (
                'This is a heading ',
                '1234',
                'obsidian',
                "[This is a heading](#^1234)",
        ),
        (
                'This is a heading ',
                '#1234',
                'obsidian',
                "[This is a heading](#^1234)",
        ),
        (
                'This is a heading ',
                '1234_567',
                'obsidian',
                "[This is a heading](#^1234567)",
        ),
        (
                'This is a heading ',
                '1234_567',
                'q_own_notes',
                "[This is a heading](#1234567)",
        ),
        (
                'This is a heading ',
                '#1234_567',
                'q_own_notes',
                "[This is a heading](#1234567)",
        ),
    ],
)
def test_markdown_anchor_tag_link(heading, link_id, link_format, expected, processing_options):
    contents = TextItem(processing_options, heading)

    result = markdown_string_builders.markdown_anchor_tag_link(contents, link_id, link_format)

    assert result == expected


@pytest.mark.parametrize(
    'checked, indent, expected, ', [
        (True, 1,
         "\t- [x] This is check one"),
        (False, 2,
         "\t\t- [ ] This is check one"),
    ],
)
def test_checklist_item_item(checked, indent, expected, processing_options):
    contents = [TextItem(processing_options, "This is "), TextItem(processing_options, "check"),
                TextItem(processing_options, " one")]

    result = markdown_string_builders.checklist_item(contents, checked, indent)

    assert result == expected


def test_checklist(processing_options):
    contents = [
        ChecklistItem(processing_options, [TextItem(processing_options, 'Check 1')], 1, True),
        ChecklistItem(processing_options, [TextItem(processing_options, 'Check 2')], 2, False),
    ]

    checklist = Checklist(processing_options, contents)

    expected = "\t- [x] Check 1\n\t\t- [ ] Check 2\n\n"

    result = checklist.markdown()

    assert result == expected


def test_pipe_table_header(processing_options):
    contents = [
        TextItem(processing_options, 'Column 1'),
        TextItem(processing_options, 'Column 2'),
    ]

    header_row = TableHeader(processing_options, contents)

    expected = "\n|Column 1|Column 2|\n|--|--|\n"

    result = header_row.markdown()

    assert result == expected


def test_pipe_table_row(processing_options):
    contents = [
        TextItem(processing_options, 'Row Item 1'),
        TextItem(processing_options, 'Row Item 2'),
    ]

    table_row = TableRow(processing_options, contents)

    expected = "|Row Item 1|Row Item 2|\n"

    result = table_row.markdown()

    assert result == expected


def test_code_block():
    contents = 'print("hello")\nprint("world")'
    language = 'python'

    expected = '```python\nprint("hello")\nprint("world")\n```\n'

    result = markdown_string_builders.code_block(contents, language)

    assert result == expected


@pytest.mark.parametrize(
    'heading, heading_id, id_format, expected', [
        (
                'This is a heading',
                '1234',
                'gfm',
                "# This is a heading\n",
        ),
        (
                'This is a heading',
                '1234',
                'obsidian',
                "# This is a heading ^1234\n",
        ),
        (
                'This is a heading',
                '1234_567',
                'obsidian',
                "# This is a heading ^1234567\n",
        ),
        (
                'This is a heading',
                '1234_567',
                'q_own_notes',
                "# This is a heading (#1234567)\n",
        ),
        (
                'This is a heading',
                '#1234_567',
                'pandoc_markdown_strict',
                "# This is a heading (#1234567)\n",
        ),
        (
                'This is a heading',
                '#1234_567',
                'commonmark',
                "# This is a heading\n",
        ),
        (
                'This is a heading',
                '#1234_567',
                'multimarkdown',
                "# This is a heading [#1234567]\n",
        ),
    ],
)
def test_heading(heading, heading_id, id_format, expected, processing_options):
    content_item = TextItem(processing_options, heading)
    items = [content_item]

    result = markdown_string_builders.heading(items, 1, heading_id, id_format)

    assert result == expected


def test_caption(processing_options):
    contents = [TextItem(processing_options, '')]
    result = markdown_string_builders.caption(contents)

    assert result == ''
