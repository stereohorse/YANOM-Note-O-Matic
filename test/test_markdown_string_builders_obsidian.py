from pathlib import Path

from bs4 import BeautifulSoup
import pytest

import helper_functions
import html_data_extractors
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



@pytest.mark.parametrize(
    'html, target_path, expected_result_markdown', [
        (
                '<img src="image.png" alt="alt text" width="100" height="200">',
                Path('image.png'),
                '![alt text|100x200](image.png)\n'
                ),
        (
                '<img src="image.png" alt="alt text" height="200">',
                Path('image.png'),
                '![alt text](image.png)\n'
        ),
        (
                '<img src="image.png" alt="alt text" width="100">',
                Path('image.png'),
                '![alt text|100](image.png)\n'
        ),
        (
                '<img src="image.png" alt="alt text">',
                Path('image.png'),
                '![alt text](image.png)\n'
        ),
        (
                '<img src="image.xyz" alt="alt text" width="100" height="200">',
                Path('image.xyz'),
                '[alt text|100x200](image.xyz)\n'
        ),
        (
                '<img src="" alt="alt text" width="100" height="200">',
                None,
                '[alt text|100x200]()\n'),

    ],
)
def test_image_embed_to_obsidian_markdown(html, target_path, expected_result_markdown, processing_options):
    processing_options.export_format = 'obsidian'
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('img')
    result = html_data_extractors.extract_from_tag(tag, processing_options)

    result.target_path = target_path

    assert result.markdown() == expected_result_markdown



