from pathlib import Path

import pytest
from bs4 import BeautifulSoup

import helper_functions
import html_data_extractors
import markdown_format_styling
from note_content_data import BlockQuote, Body, Break, BulletList, Caption, NumberedList
from note_content_data import Head, HeadingItem, Hyperlink, ImageEmbed
from embeded_file_types import EmbeddedFileTypes
from note_content_data import Paragraph, SectionContent
from processing_options import ProcessingOptions
from note_content_data import TextColorItem,  TextFormatItem, TextItem, Title, UnrecognisedTag


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



class TestIsATag:

    @pytest.fixture
    def a_tag(self):
        html = '<p>hello</p>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('p')

        return tag

    def test_is_a_tag_real_tag(self, a_tag):
        result = html_data_extractors.is_a_tag(a_tag)

        assert result

    def test_is_a_tag_not_a_tag(self):
        result = html_data_extractors.is_a_tag(1)

        assert result is False


class TestProcessChildItems:
    def test_process_child_items(self, processing_options):
        html = '<head><title>My Title</title></head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_data_extractors.process_child_items(tag, processing_options, None)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], Title)

    def test_process_child_items_mulitple_child_levels(self, processing_options):
        html = '<head><title>My Title</title><p>paragraph</p><p>paragraph2<p>paragraph3</p></p></head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_data_extractors.process_child_items(tag, processing_options, None)

        assert isinstance(result, list)
        assert len(result) == 4
        assert isinstance(result[0], Title)
        assert isinstance(result[1], TextItem)

    def test_process_child_items_with_navigable_strings(self, processing_options):
        html = '<head>\n<title>My Title</title>\nI know it is very unlikely to have text here</head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_data_extractors.process_child_items(tag, processing_options, None)

        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], Title)
        assert isinstance(result[1], TextItem)
        assert result[1].contents == 'I know it is very unlikely to have text here'

    def test_process_child_items_with_navigable_strings2(self, processing_options):
        html = '<head>I know it is very unlikely to have text here</head>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('head')
        result = html_data_extractors.process_child_items(tag, processing_options, None)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextItem)
        assert result[0].contents == 'I know it is very unlikely to have text here'

    def test_process_child_items_with_note_specific_tag_cleaning(self, processing_options, mocker):
        """Test to confirm the note_specific_tag_cleaning function is called when provided"""
        html = '<body><p><p>Some Text</p></p></body>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('body')

        # patch the function to give us a known return value that we would not get from the provided tag
        # the three hashed out patches also work
        # mocker.patch('html_data_extractors.extract_from_hyperlink', return_value='correct function was called')
        # mocker.patch.object(html_data_extractors, 'extract_from_hyperlink')
        # mocker.patch.object(html_data_extractors, 'extract_from_hyperlink', return_value='correct function was called')
        mocker.patch('html_data_extractors.extract_from_hyperlink')
        result = html_data_extractors.process_child_items(
            tag, processing_options,
            note_specific_tag_cleaning=html_data_extractors.extract_from_hyperlink
        )

        html_data_extractors.extract_from_hyperlink.assert_called_once()


class TestExtractFromTag:

    @pytest.mark.parametrize(
        'html, tag_name, expected', [
            ('<head><title>My Title</title></head>', 'head', Head),
            ('<body><title>My Title</title></body>', 'body', Body),
            ('<h2>My heading</h2>', 'h2', HeadingItem),
            ('<span class="font-color" style="color: rgb(237, 84, 84);">This is coloured.</span>',
             'span',
             TextColorItem,
             ),
            ('<strong>bold text</strong>', 'strong', TextFormatItem),
            ('<div><title>My Title</title></div>', 'div', Paragraph),
            ('<section><title>My Title</title></section>', 'section', SectionContent),
            ('<blockquote cite="my-citation">My Quote</blockquote>', 'blockquote', BlockQuote),
            ('<title>My Title</title>', 'title', Title),
            ('<p>Some Text</p>', 'p', list),
            ('<i>Some Text</i>', 'i', list),
            ('<img src="image.png" alt="alt text", width="100" height="200">', 'img', ImageEmbed),
            ('<a href="image.png">link display text</a>', 'a', Hyperlink),
            ('<iframe>My iframe</iframe>', 'iframe', TextItem),
            ('<span>a span</span>', 'span', list),
            ('<ol><li>number one</li><li>number two</li><ol><li>number <strong>bold</strong> 2-1</li><li>number <em>Italic</em> 2-2</li></ol><li>number <strong><em>bold italic</em></strong> 3 below is an empty numbered item</li><li><br></li></ol>',
             'ol', NumberedList),
            ('<ul><li>bullet 1</li><ul><li>sub <strong>bullet</strong> two, below is an empty bullet</li><li><br></li></ul><li>bullet 2</li></ul>',
             'ul', BulletList),
            ('<li>sub <strong>bullet</strong> two, below is an empty bullet</li>',
             'li', list),
        ]
    )
    def test_extract_from_tag_confirm_correct_data_type_returned(self, html, tag_name, expected, processing_options):
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find(tag_name)
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert isinstance(result, expected)

    @pytest.mark.parametrize(
        'html, tag_name, function_to_be_called', [
            ('<head><title>My Title</title></head>', 'head', html_data_extractors.extract_from_head_tag),
            ('<body><title>My Title</title></body>', 'body', html_data_extractors.extract_from_body),
            ('<h2>My heading</h2>', 'h2', html_data_extractors.extract_from_heading),
            ('<span class="font-color" style="color: rgb(237, 84, 84);">This is coloured.</span>',
             'span',
             html_data_extractors.extract_from_coloured_text_span,
             ),
            ('<strong>bold text</strong>', 'strong', html_data_extractors.extract_text_formatting),
            ('<div><title>My Title</title></div>', 'div', html_data_extractors.extract_from_div),
            ('<section><title>My Title</title></section>', 'section', html_data_extractors.extract_from_section),
            ('<blockquote cite="my-citation">My Quote</blockquote>',
             'blockquote',
             html_data_extractors.extract_from_blockquote,
             ),
            ('<title>My Title</title>', 'title', html_data_extractors.extract_from_title),
            ('<p>Some Text</p>', 'p', html_data_extractors.extract_from_p_or_i_tag),
            ('<i>Some Text</i>', 'i', html_data_extractors.extract_from_p_or_i_tag),
            ('<img src="image.png" alt="alt text", width="100" height="200">',
             'img',
             html_data_extractors.extract_from_img_tag,
             ),
            ('<a href="image.png">link display text</a>', 'a', html_data_extractors.extract_from_hyperlink),
            ('<iframe>My iframe</iframe>', 'iframe', html_data_extractors.extract_from_iframe),
            ('<span>a span</span>', 'span', html_data_extractors.extract_from_unknown_span),
            ('<ol><li>number one</li><li>number two</li><ol><li>number <strong>bold</strong> 2-1</li><li>number <em>Italic</em> 2-2</li></ol><li>number <strong><em>bold italic</em></strong> 3 below is an empty numbered item</li><li><br></li></ol>',
             'ol', html_data_extractors.extract_numbered_list_from_ol_tag),
            ('<ul><li>bullet 1</li><ul><li>sub <strong>bullet</strong> two, below is an empty bullet</li><li><br></li></ul><li>bullet 2</li></ul>',
             'ul', html_data_extractors.extract_bullet_list_from_ul_tag),
            ('<li>sub <strong>bullet</strong> two, below is an empty bullet</li>',
             'li', html_data_extractors.extract_from_li_tag),
        ]
    )
    def test_extract_from_tag_confirm_correct_functions_called(self, html, tag_name, function_to_be_called, processing_options, mocker):
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find(tag_name)

        function_to_be_called_as_string = f'{function_to_be_called.__module__}.{function_to_be_called.__name__}'
        mocker.patch(function_to_be_called_as_string, return_value='correct function was called')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert result == 'correct function was called'

    def test_extract_from_tag_break_tag(self, processing_options):
        html = '<br>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('br')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert isinstance(result, Break)

    def test_extract_from_tag_link_tag(self, processing_options):
        html = '<link></link>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('link')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert result is None

    def test_extract_from_tag_meta_tag(self, processing_options):
        html = '<meta></meta>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('meta')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert result is None

    def test_extract_from_tag_with_coloured_text_span_no_color_in_style(self, processing_options):
        """Test passing correct tag"""
        html = '<span class="font-color" style="">This is coloured.</span>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        result = html_data_extractors.extract_from_tag(tag, processing_options)
        assert isinstance(result, list)
        assert result[0].contents == 'This is coloured.'

    def test_extract_from_tag_unrecognised_tag(self, processing_options, caplog):
        html = '<jdsflksjdhf><title>My Title</title></jdsflksjdhf>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('jdsflksjdhf')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert isinstance(result, UnrecognisedTag)
        assert result.contents == '<jdsflksjdhf><title>My Title</title></jdsflksjdhf>'
        assert result.text == 'My Title'
        result.processing_options.unrecognised_tag_format = 'html'
        assert result.html() == '<jdsflksjdhf><title>My Title</title></jdsflksjdhf>'
        assert result.markdown() == '\n <jdsflksjdhf><title>My Title</title></jdsflksjdhf>\n'
        result.processing_options.unrecognised_tag_format = 'text'
        assert result.html() == '<p>My Title</p>'
        assert result.markdown() == '\n My Title\n'
        assert len(caplog.records) == 1



    def test_extract_from_tag_navigable_string(self, processing_options):
        html = '<html>\n<head></head></html>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('html').next_element
        result = html_data_extractors.extract_from_tag(tag, processing_options)
        assert result is None

    def test_extract_from_tag_passing_none(self, processing_options):
        result = html_data_extractors.extract_from_tag(None, processing_options)
        assert result is None

    def test_extract_from_tag_passing_note_specific_tag_cleaning_function(self, processing_options, mocker):
        """Test to confirm the note_specific_tag_cleaning function is called when provided"""
        html = '<title>My Title</title>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('title')

        # patch the function to give us a known return value that we would not get from the provided tag
        mocker.patch('html_data_extractors.extract_from_hyperlink', Head)
        result = html_data_extractors.extract_from_tag(
            tag, processing_options,
            note_specific_tag_cleaning=html_data_extractors.extract_from_hyperlink
        )

        assert isinstance(result, Head)


class TestExtractFromHeadTag:
    def test_extract_from_head_tag(self, processing_options):
        """Test passing correct tag"""
        html = "<head><title>My Title</title></head>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('head')
        assert tag.name == 'head'

        result = html_data_extractors.extract_from_head_tag(tag, processing_options)
        assert isinstance(result, Head)
        assert len(result.contents) == 1
        assert isinstance(result.contents[0], Title)
        assert result.contents[0].contents == 'My Title'

    def test_extract_from_head_tag_empty_head(self, processing_options):
        """Test passing correct tag"""
        html = "<head></head>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('head')
        assert tag.name == 'head'

        result = html_data_extractors.extract_from_head_tag(tag, processing_options)
        assert result is None

    def test_extract_from_head_tag_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_head_tag(tag, processing_options)
        assert result == expected


class TestExtractFromBody:
    def test_extract_from_body(self, processing_options):
        """Test passing correct tag"""
        html = "<body><title>My Title</title></body>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('body')
        assert tag.name == 'body'

        result = html_data_extractors.extract_from_body(tag, processing_options)
        assert isinstance(result, Body)
        assert len(result.contents) == 1
        assert isinstance(result.contents[0], Title)
        assert result.contents[0].contents == 'My Title'

    def test_extract_from_body_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_body(tag, processing_options)
        assert result == expected


class TestExtractFromHeading:

    @pytest.mark.parametrize(
        'html, tag_name, expected_level, expected_id', [
            ('<h2 id="1234">My heading</h2>', 'h2', 2, '1234'),
            ('<h0 id="abcd">My heading</h0>', 'h0', 1, 'abcd'),
            ('<h7 id="">My heading</h7>', 'h7', 6, ''),
            ('<h7>My heading</h7>', 'h7', 6, ''),
        ]
    )
    def test_extract_from_heading(self, html, tag_name, expected_level, expected_id, processing_options):
        """Test passing correct tag, confirm heading levels are restricted to 1-6"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_name)
        assert tag.name == tag_name

        result = html_data_extractors.extract_from_heading(tag, processing_options, None)
        assert isinstance(result, HeadingItem)
        assert len(result.contents) == 1
        assert result.level == expected_level
        assert result.id == expected_id
        assert isinstance(result.contents[0], TextItem)
        assert result.contents[0].contents == 'My heading'

    @pytest.mark.parametrize(
        'html, tag_name', [
            ("<title>My Title</title>", 'title'),
            ('<hh>My Title</hh>', 'hh'),
            ('<x1>My Title</x1>', 'x1'),
        ]
    )
    def test_extract_from_heading_incorrect_tag(self, html, tag_name, processing_options):
        """Test passing incorrect tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_name)
        assert tag.name == tag_name

        expected = None
        result = html_data_extractors.extract_from_heading(tag, processing_options, None)
        assert result == expected


class TestExtractFromColouredTextSpan:
    def test_extract_from_coloured_text_span(self, processing_options):
        """Test passing correct tag"""
        html = '<span class="font-color" style="color: rgb(237, 84, 84);">This is coloured.</span>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        result = html_data_extractors.extract_from_coloured_text_span(tag, processing_options)
        assert isinstance(result, TextColorItem)
        assert result.contents == '<span style="color: rgb(237, 84, 84);">This is coloured.</span>'
        assert result.plain_text == 'This is coloured.'
        assert result.processing_options == processing_options

    def test_extract_from_coloured_text_span_no_class(self, processing_options):
        """Test passing correct tag"""
        html = '<span style="color: rgb(237, 84, 84);">This is coloured.</span>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        result = html_data_extractors.extract_from_coloured_text_span(tag, processing_options)
        assert isinstance(result, TextColorItem)
        assert result.contents == '<span style="color: rgb(237, 84, 84);">This is coloured.</span>'
        assert result.plain_text == 'This is coloured.'
        assert result.processing_options == processing_options

    def test_extract_from_coloured_text_span_no_style(self, processing_options):
        """Test passing correct tag"""
        html = '<span>This is coloured.</span>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        expected = None
        result = html_data_extractors.extract_from_coloured_text_span(tag, processing_options)
        assert result == expected

    def test_extract_from_coloured_text_span_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_coloured_text_span(tag, processing_options)
        assert result == expected


class TestExtractTextFormatting:
    def test_extract_text_formatting(self, processing_options):
        """Test passing correct tag"""
        html = "<strong>bold text</strong>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('strong')
        assert tag.name == 'strong'

        result = html_data_extractors.extract_text_formatting(tag,
                                                              markdown_format_styling.format_styling,
                                                              processing_options
                                                              )

        assert isinstance(result, TextFormatItem)
        assert result.format == 'strong'
        assert result.contents[0].contents == 'bold text'
        assert result.processing_options == processing_options

    def test_extract_text_formatting_multiple_formats(self, processing_options):
        """Test passing correct tag"""
        html = "<strong><em>bold and italic</em> bold text</strong>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('strong')
        assert tag.name == 'strong'

        result = html_data_extractors.extract_text_formatting(tag,
                                                              markdown_format_styling.format_styling,
                                                              processing_options
                                                              )

        assert isinstance(result, TextFormatItem)
        assert result.format == 'strong'
        assert isinstance(result.contents, list)

        assert result.contents[0].format == 'em'
        assert isinstance(result.contents[0].contents, list)
        assert isinstance(result.contents[0].contents[0], TextItem)
        assert result.contents[0].contents[0].contents == 'bold and italic'
        assert isinstance(result.contents[1], TextItem)
        assert result.contents[1].contents == ' bold text'

        assert result.processing_options == processing_options

    def test_extract_text_formatting_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_text_formatting(tag,
                                                              markdown_format_styling.format_styling,
                                                              processing_options
                                                              )

        assert result == expected


class TestExtractFromDiv:
    def test_extract_from_div(self, processing_options):
        """Test passing correct tag"""
        html = "<div><title>My Title</title></div>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_data_extractors.extract_from_div(tag, processing_options)
        assert isinstance(result, Paragraph)
        assert len(result.contents) == 1
        assert isinstance(result.contents[0], Title)
        assert result.contents[0].contents == 'My Title'

    def test_extract_from_div_first_child_is_div(self, processing_options):
        """Test passing correct tag"""
        html = "<div><div>My Div</div></div>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('div')
        assert tag.name == 'div'

        result = html_data_extractors.extract_from_div(tag, processing_options)
        assert isinstance(result, list)
        assert len(result[0].contents) == 1
        assert isinstance(result[0], Paragraph)
        assert isinstance(result[0].contents[0], TextItem)
        assert result[0].contents[0].contents == "My Div"

    def test_extract_from_div_two_child_divs(self, processing_options):
            """Test passing correct tag"""
            # html = "<div><div><div>My Div</div></div></div>"
            html = "<div><div><div><br></div></div></div>"
            soup = helper_functions.make_soup_from_html(html)
            tag = soup.find('div')
            assert tag.name == 'div'

            result = html_data_extractors.extract_from_div(tag, processing_options)
            assert isinstance(result, list)
            assert len(result[0].contents) == 1
            assert isinstance(result[0], Paragraph)

    def test_extract_from_div_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_div(tag, processing_options)
        assert result == expected


class TestExtractFromSection:
    def test_extract_from_body(self, processing_options):
        """Test passing correct tag"""
        html = "<section><title>My Title</title></section>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('section')
        assert tag.name == 'section'

        result = html_data_extractors.extract_from_section(tag, processing_options)
        assert isinstance(result, SectionContent)
        assert len(result.contents) == 1
        assert isinstance(result.contents[0], Title)
        assert result.contents[0].contents == 'My Title'

    def test_extract_from_body_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_section(tag, processing_options)
        assert result == expected


class TestExtractFromBlockQuote:
    def test_extract_from_blockquote(self, processing_options):
        """Test passing correct tag"""
        html = '<blockquote cite="my-citation">My Quote</blockquote>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('blockquote')
        assert tag.name == 'blockquote'

        result = html_data_extractors.extract_from_blockquote(tag, processing_options)
        assert isinstance(result, BlockQuote)
        assert len(result.contents) == 1
        assert isinstance(result.contents[0], TextItem)
        assert result.contents[0].contents == 'My Quote'

    def test_extract_from_blockquote_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_blockquote(tag, processing_options)
        assert result == expected


class TestExtractFromTitle:
    def test_extract_from_title(self, processing_options):
        """Test passing correct tag"""
        html = '<title>My Title</title>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        result = html_data_extractors.extract_from_title(tag, processing_options)
        assert isinstance(result, Title)
        assert result.contents == 'My Title'

    def test_extract_from_title_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<body>My Body</body>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('body')
        assert tag.name == 'body'

        expected = None
        result = html_data_extractors.extract_from_title(tag, processing_options)
        assert result == expected


class TestExtractFromPOrITag:

    @pytest.mark.parametrize(
        'html, tag_name, expected', [
            ('<p>Some Text</p>', 'p', TextItem),
            ('<i>Some Text</i>', 'i', TextItem),
        ]
    )
    def test_extract_from_p_or_i_tag(self, html, tag_name, expected, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find(tag_name)
        assert tag.name == tag_name

        result = html_data_extractors.extract_from_p_or_i_tag(tag, processing_options)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], expected)
        assert result[0].contents == 'Some Text'

    def test_extract_from_p_or_i_tag_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_p_or_i_tag(tag, processing_options)
        assert result == expected


class TestExtractFromImgTag:

    @pytest.mark.parametrize(
        'html, src, alt, width, height', [
            ('<img src="image.png" alt="alt text", width="100" height="200">', "image.png", "alt text", "100", "200"),
            ('<img src="image.png" alt="", width="100" height="200">', "image.png", "", "100", "200"),
            ('<img src="image.png" alt="", width="100" height="">', "image.png", "", "100", ""),
            ('<img src="image.png" alt="", width="100">', "image.png", "", "100", ""),
            ('<img src="image.png" alt="alt text", width="" height="200">', "image.png", "alt text", "", "200"),
            ('<img src="image.png" alt="alt text", height="200">', "image.png", "alt text", "", "200"),
            ('<img src="image.png">', "image.png", "", "", ""),
        ]
    )
    def test_extract_from_image_tag(self, html, src, alt, width, height, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('img')
        assert tag.name == 'img'

        result = html_data_extractors.extract_from_img_tag(tag, processing_options)
        assert isinstance(result, ImageEmbed)

        assert result.href == src
        assert result.contents == alt
        assert result.width == width
        assert result.height == height
        assert result.source_path == Path(src)
        assert result.filename == Path(src).name

    def test_extract_from_image_tag_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_img_tag(tag, processing_options)
        assert result == expected


class TestExtractFromHyperlink:

    @pytest.mark.parametrize(
        'html, href, display_text', [
            ('<a href="image.png">link display text</a>', 'image.png', 'link display text'),
            ('<a href="image.png"></a>', 'image.png', ''),
            ('<a href="">link display text</a>', '', 'link display text'),
            ('<a href=""></a>', '', ''),
        ]
    )
    def test_extract_from_hyperlink(self, html, href, display_text, processing_options):
        """Test passing correct tag"""
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('a')
        assert tag.name == 'a'

        result = html_data_extractors.extract_from_hyperlink(tag, processing_options)
        assert isinstance(result, Hyperlink)
        assert result.href == href
        assert result.contents == display_text

    def test_extract_from_hyperlink_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<title>My Title</title>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('title')
        assert tag.name == 'title'

        expected = None
        result = html_data_extractors.extract_from_hyperlink(tag, processing_options)
        assert result == expected


class TestExtractFromIframe:
    def test_extract_from_iframe(self, processing_options):
        """Test passing correct tag"""
        html = '<iframe>My iframe</iframe>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('iframe')
        assert tag.name == 'iframe'

        result = html_data_extractors.extract_from_iframe(tag, processing_options)
        assert isinstance(result, TextItem)
        assert result.contents == '<iframe>My iframe</iframe>'

    def test_extract_from_iframe_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<body>My Body</body>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('body')
        assert tag.name == 'body'

        expected = None
        result = html_data_extractors.extract_from_iframe(tag, processing_options)
        assert result == expected


class TestExtractFromUnknownSpan:
    def test_extract_from_unknown_span(self, processing_options):
        """Test passing correct tag"""
        html = '<span>a span</span>'
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('span')
        assert tag.name == 'span'

        result = html_data_extractors.extract_from_unknown_span(tag, processing_options, None)
        assert isinstance(result, list)
        assert isinstance(result[0], TextItem)
        assert result[0].contents == 'a span'

    def test_extract_from_unknown_span_incorrect_tag(self, processing_options):
        """Test passing incorrect tag"""
        html = "<body>My Body</body>"
        soup = helper_functions.make_soup_from_html(html)
        tag = soup.find('body')
        assert tag.name == 'body'

        expected = None
        result = html_data_extractors.extract_from_unknown_span(tag, processing_options, None)
        assert result == expected


@pytest.mark.parametrize(
    'function_to_be_called', [
        (html_data_extractors.extract_numbered_list_from_ol_tag),
        (html_data_extractors.extract_bullet_list_from_ul_tag),
        (html_data_extractors.extract_from_li_tag),
    ]
)
def test_test_functions_return_none_on_invalid_tag(function_to_be_called, processing_options):
    html = '<jhksadjha>Rubbish</jhksadjha>'
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('jhksadjha')
    assert tag.name == 'jhksadjha'

    def fake_note_specific_cleaning():
        pass

    result = function_to_be_called(tag, processing_options, fake_note_specific_cleaning)

    assert result is None


class TestExtractFromFigure:
    def test_extract_from_figure_property_testing(self, processing_options):
        """Test round tripping html string"""
        html = f'<figure><img src="image.png" alt="an image" width="200" height="300"><figcaption>A caption</figcaption></figure>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('figure')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        result.contents[0].target_path = Path('image.png')

        assert result.html() == html

    def test_extract_from_figure_no_image_tag(self, processing_options):
        """Test round tripping html string"""
        html = f'<figure><figcaption>A caption</figcaption></figure>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('figure')
        result = html_data_extractors.extract_from_tag(tag, processing_options)

        assert result.html() == html

    def test_extract_from_figure_no_caption(self, processing_options):
        """Test round tripping html string"""
        html = f'<figure><img src="image.png" alt="an image" width="200" height="300"></figure>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('figure')

        expected = '<img src="image.png" alt="an image" width="200" height="300">'

        result = html_data_extractors.extract_from_tag(tag, processing_options)

        result.contents[0].target_path = Path('image.png')

        assert result.html() == expected

    def test_extract_from_figure_invalid_tag(self, processing_options):
        html = '<title>My title</title>'
        soup = BeautifulSoup(html, 'html.parser')
        tag = soup.find('title')

        result = html_data_extractors.extract_from_figure(tag, processing_options)

        assert result is None


def test_extract_from_figure_caption(processing_options):
    """Test round tripping html string"""
    html = f'<figcaption>A caption</figcaption>'
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('figcaption')
    result = html_data_extractors.extract_from_tag(tag, processing_options)

    assert isinstance(result, Caption)
    assert result.html() == 'A caption'