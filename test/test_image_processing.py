from bs4 import BeautifulSoup
from pathlib import Path

import pytest

import image_processing


class ImageNSAttachment:
    """Fake class to allow testing of ImageTag class"""

    def __init__(self):
        self.image_ref = 'MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n'
        self.path_relative_to_notebook = Path('attachments/12345678.png')


@pytest.mark.parametrize(
    'raw_html, proved_path, expected', [
        ("""<div><img class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" width=\"600\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>""",
         'attachments/12345678.png',
         {'src': 'attachments/12345678.png', 'width': '600'},
         ),
        ("""<div><img class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>""",
         'attachments/12345678.png',
         {'src': 'attachments/12345678.png'},
         ),
        ("""<div><img alt=\"Some alt text\" class=\" syno-notestation-image-object\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>""",
         'attachments/12345678.png',
         {'alt': 'Some alt text', 'src': 'attachments/12345678.png'},
         ),
        ("""<div><img class=\" syno-notestation-image-object\" alt=\"Some alt text\" src=\"webman/3rdparty/NoteStation/images/transparent.gif\" border=\"0\" width=\"600\" ref=\"MTYxMzQwNDM0NDczN25zX2F0dGFjaF9pbWFnZV83ODc0OTE2MTM0MDQzNDQ2ODcucG5n\" adjust=\"true\" /></div>""",
         'attachments/12345678.png',
         {'alt': 'Some alt text', 'src': 'attachments/12345678.png', 'width': '600'},
         ),
        ("""<div><img src="my_image.gif" alt="Some alt text" width="600"/></div>""",
         'attachments/12345678.png',
         {'alt': 'Some alt text', 'src': 'attachments/12345678.png', 'width': '600'},
         ),
        ("""<div><img src="" alt="Some alt text" width="600"/></div>""",
         None,
         {'alt': 'Some alt text', 'src': '', 'width': '600'},
         ),
        ("""<div><img alt="Some alt text" width="600"/></div>""",
         None,
         {'alt': 'Some alt text', 'src': '', 'width': '600'},
         ),
        ("""<div><img width="600"/></div>""",
         None,
         {'src': '', 'width': '600'},
         ),
        ("""<div><img width="600" height="300" /></div>""",
         None,
         {'src': '', 'width': '600', 'height': '300'},
         ),
        ("""<div><img /></div>""",
         None,
         {'src': ''},
         ),
        ("""<div><img /></div>""",
         'attachments/12345678.png',
         {'src': 'attachments/12345678.png'},
         ),
    ],
)
def test_clean_html_image_tag(raw_html, proved_path, expected):
    soup = BeautifulSoup(raw_html, 'html.parser')

    image_tag = soup.findAll('img')

    result = image_processing.clean_html_image_tag(image_tag[0], proved_path)

    assert result == expected


@pytest.mark.parametrize(
    'raw_html, expected', [
        ("""<div><img src="attachments/12345678.png" width="600"/></div>""",
         """![|600](attachments/12345678.png)""",
         ),
        ("""<div><img alt="Some alt text" src="attachments/12345678.png"/></div>""",
         None,
         ),
        ("""<div><img alt="Some alt text" src="attachments/12345678.png" width="600"/></div>""",
         """![Some alt text|600](attachments/12345678.png)""",
         ),
        ("""<div><img src="my_image.gif" alt="Some alt text" width="600"/></div>""",
         """![Some alt text|600](my_image.gif)""",
         ),
        ("""<div><img src="my_image.gif" alt="Some alt text" width="600" height="300" /></div>""",
         """![Some alt text|600x300](my_image.gif)""",
         ),
        ("""<div><img src="my_image.gif" alt="Some alt text" height="300" /></div>""",
         None,
         ),
        ("""<div><img src="" alt="Some alt text" width="600"/></div>""",
         """![Some alt text|600]()""",
         ),
        ("""<div><img alt="Some alt text" width="600"/></div>""",
         """![Some alt text|600]()""",
         ),
        ("""<div><img width="600"/></div>""",
         """![|600]()""",
         ),
        ("""<div><img /></div>""",
         None,
         ),
        ("""<div><img width=''/></div>""",
         None,
         ),
        ("""<div><img alt=''/></div>""",
         None,
         ),
        ("""<div><img src=''/></div>""",
         None,
         ),
    ],
)
def test_generate_obsidian_image_markdown_link(raw_html, expected):
    soup = BeautifulSoup(raw_html, 'html.parser')

    image_tag = soup.findAll('img')

    result = image_processing.generate_obsidian_image_markdown_link(image_tag[0])

    assert result == expected


def test_generate_obsidian_image_markdown_link_with_height():
    soup = BeautifulSoup('<div><img src="my_image.gif" alt="Some alt text" width="600" height="300" /></div>', 'html.parser')
    expected = '![Some alt text|600x300](my_image.gif)'
    image_tag = soup.findAll('img')

    result = image_processing.generate_obsidian_image_markdown_link(image_tag[0])

    assert result == expected

@pytest.mark.parametrize(
    'expected, obsidian', [
        ("""<img src="attachments/12345678.png" width="600" />""",
         """![|600](attachments/12345678.png)""",
         ),
        ("""<img alt="alt text [with] brackets" src="attachments/12345678.png" width="600" />""",
         """![alt text [with] brackets|600](attachments/12345678.png)""",
         ),
        ("""![Some alt text](attachments/12345678.png)""",
         """![Some alt text](attachments/12345678.png)""",
         ),
        ("""<img alt="Some alt text with | a pipe" src="attachments/12345678.png" />""",
         """![Some alt text with | a pipe](attachments/12345678.png)""",
         ),
        ("""<img alt="Some alt text with | a pipe and a width" src="attachments/12345678.png" width="400" />""",
         """![Some alt text with | a pipe and a width|400](attachments/12345678.png)""",
         ),
        (
                """<img alt="Some alt text with | a pipe and a width [and] brackets" src="attachments/12345678.png" width="400" />""",
                """![Some alt text with | a pipe and a width [and] brackets|400](attachments/12345678.png)""",
        ),
        ("""<img alt="Some alt text" src="attachments/12345678.png" width="600" />""",
         """![Some alt text|600](attachments/12345678.png)""",
         ),
        ("""<img alt="Some alt text" src="my_image.gif" width="600" />""",
         """![Some alt text|600](my_image.gif)""",
         ),
        ("""<img alt="Some alt text" src="" width="600" />""",
         """![Some alt text|600]()""",
         ),
        ("""<img alt="Some alt text" src="" width="600" />""",
         """![Some alt text|600]()""",
         ),
        ("""<img src="" width="600" />""",
         """![|600]()""",
         ),
        ("""![]()""",
         """![]()""",
         ),
        ("""hello world""",
         """hello world""",
         ),
        ("""
        a line with no images
        <img alt="text" src="filepath/image(23).png" width="600" height="300" /> more text <img alt="text" src="filepath/image(23).png" width="600" /> more more text
        <img alt="text" src="filepath/image(23).png" width="600" />
        ![alt text](filepath/image(23).png)
        ![alt text](filepath/image((23,hello)).png)
        ![alt text](filepath/image((23 hello)).png)
        <img alt="alt text" src="filepath/image.png" width="600" />
        ![alt text](filepath/image.png)
        pre text ![alt text](filepath/image(23)).png) more text
        ![alt text](filepath/image.png) more text
        ![alt text](filepath/ima ge.png)
        ![alt text](filepath\ima.ge.png)
        <img src="filepath/image(23).png" width="600" />
        """,
        """
        a line with no images
        ![text|600x300](filepath/image(23).png) more text ![text|600](filepath/image(23).png) more more text
        ![text|600](filepath/image(23).png)
        ![alt text](filepath/image(23).png)
        ![alt text](filepath/image((23,hello)).png)
        ![alt text](filepath/image((23 hello)).png)
        ![alt text|600](filepath/image.png)
        ![alt text](filepath/image.png)
        pre text ![alt text](filepath/image(23)).png) more text
        ![alt text](filepath/image.png) more text
        ![alt text](filepath/ima ge.png)
        ![alt text](filepath\\ima.ge.png)
        ![|600](filepath/image(23).png)
        """,
         ),
    ],
)
def test_replace_obsidian_image_links_with_html_img_tag(expected, obsidian):
    result = image_processing.replace_obsidian_image_links_with_html_img_tag(obsidian)

    assert result == expected


@pytest.mark.parametrize(
    'html, expected', [
        ("""<img src="attachments/12345678.png" width="600" />""",
         """![|600](attachments/12345678.png)""",
         ),
        ("""<img alt="alt text [with] brackets" src="attachments/12345678.png" width="600" />""",
         """![alt text with brackets|600](attachments/12345678.png)""",
         ),
        ("""<img alt="Some alt text" src="attachments/12345678.png" />""",
         """<img alt="Some alt text" src="attachments/12345678.png"/>""",
         ),
        ("""<img alt="Some alt text with | a pipe" src="attachments/12345678.png" />""",
         """<img alt="Some alt text with | a pipe" src="attachments/12345678.png"/>""",
         ),
        ("""<img alt="Some alt text with | a pipe and a width" src="attachments/12345678.png" width="400" />""",
         """![Some alt text with | a pipe and a width|400](attachments/12345678.png)""",
         ),
        (
                """<img alt="Some alt text with | a pipe and a width [and] brackets" src="attachments/12345678.png" width="400" />""",
                """![Some alt text with | a pipe and a width and brackets|400](attachments/12345678.png)""",
        ),
        ("""<img alt="Some alt text" src="attachments/12345678.png" width="600"/>""",
         """![Some alt text|600](attachments/12345678.png)""",
         ),
        ("""<img alt="Some alt text" src="my_image.gif" width="600"/>""",
         """![Some alt text|600](my_image.gif)""",
         ),
        ("""<img alt="Some alt text" src="" width="600"/>""",
         """![Some alt text|600]()""",
         ),
        ("""<img alt="Some alt text" src="" width="600"/>""",
         """![Some alt text|600]()""",
         ),
        ("""<img src="" width="600"/>""",
         """![|600]()""",
         ),
        ("""![]()""",
         """![]()""",
         ),
    ],
)
def test_replace_markdown_html_img_tag_with_obsidian_image_links(html, expected):
    result = image_processing.replace_markdown_html_img_tag_with_obsidian_image_links(html)

    assert result == expected



@pytest.mark.parametrize(
    'text_line, expected', [
        ('![text|600x300](filepath/image(23).png)', 'filepath/image(23).png'),
        ('![text|600x300](filepath/image((23,hello)).png)', 'filepath/image((23,hello)).png'),
        ('pre text ![alt text](filepath/image(23)).png) more text', 'filepath/image(23)'),
        ('![alt text](filepath\\ima.ge.png)', 'filepath\\ima.ge.png'),
    ]
)
def test_find_markdown_path(text_line, expected):
    result = image_processing.find_markdown_path(text_line)
    assert result == expected


@pytest.mark.parametrize(
    'text_line, expected_alt, expected_width, expected_height, expected_alt_box_original', [
        ('![text|600x300](filepath/image(23).png)',
         'text', '600', '300', '![text|600x300]'),
        ('![text|600](filepath/image((23,hello)).png)',
         'text', '600', '', '![text|600]',),
        ('![alt text|x600](filepath/image((23,hello)).png)',
         'alt text|x600', '', '', '![alt text|x600]',),
        ('![|600](filepath/image(23).png)',
         '', '600', '', '![|600]',),
        ('![|some-text](filepath/image.png))',
         '|some-text', '', '', '![|some-text]',),
        ('![|hello world](filepath/image.png))',
         '|hello world', '', '', '![|hello world]',),

    ]
)
def test_find_alt_box_details(text_line, expected_alt, expected_width, expected_height, expected_alt_box_original):
    alt_text, width, height, original_alt_box = image_processing.find_alt_box_details(text_line)

    assert alt_text == expected_alt
    assert width == expected_width
    assert height == expected_height
    assert original_alt_box == expected_alt_box_original


@pytest.mark.parametrize(
    'alt_text, img_width, img_height, path, expected', [
        ('some alt text', '600', '300', 'folder/file.ext',
         '<img alt="some alt text" src="folder/file.ext" width="600" height="300" />'),
        ('some alt text', '', '300', 'folder/file.ext',
         '<img alt="some alt text" src="folder/file.ext" height="300" />'),
        ('some alt text', '600', '', 'folder/file.ext',
         '<img alt="some alt text" src="folder/file.ext" width="600" />'),
        ('some alt text', '', '', 'folder/file.ext',
         '<img alt="some alt text" src="folder/file.ext" />'),
        ('', '', '', 'folder/file.ext',
         '<img src="folder/file.ext" />'),
    ],
)
def test_create_image_autolink(alt_text, img_width, img_height, path, expected):
    result = image_processing.create_image_autolink(alt_text, img_width, img_height, path)
    assert result == expected


# def test_replace_obsidian_image_links_with_html_img_tag():
#     markdown = """
#             ![text|600x300](filepath/image(23).png) more text ![text|600](filepath/image(23).png) more more text
#             ![text|600](filepath/image(23).png)
#             ![alt text](filepath/image(23).png)
#             ![alt text](filepath/image((23,hello)).png)
#             ![alt text](filepath/image((23 hello)).png)
#             ![alt text|600](filepath/image.png)
#             ![alt text](filepath/image.png)
#             pre text ![alt text](filepath/image(23)).png) more text
#             ![alt text](filepath/image.png) more text
#             ![alt text](filepath/ima ge.png)
#             ![alt text](filepath\\ima.ge.png)
#             ![|600](filepath/image(23).png)
#             """
#
#     expected ="""
#             <img alt="text" src="filepath/image(23).png" width="600" height="300" /> more text <img alt="text" src="filepath/image(23).png" width="600" /> more more text
#             <img alt="text" src="filepath/image(23).png" width="600" />
#             ![alt text](filepath/image(23).png)
#             ![alt text](filepath/image((23,hello)).png)
#             ![alt text](filepath/image((23 hello)).png)
#             <img alt="alt text" src="filepath/image.png" width="600" />
#             ![alt text](filepath/image.png)
#             pre text ![alt text](filepath/image(23)).png) more text
#             ![alt text](filepath/image.png) more text
#             ![alt text](filepath/ima ge.png)
#             ![alt text](filepath\ima.ge.png)
#             <img src="filepath/image(23).png" width="600" />
#             """
#     result = image_processing.replace_obsidian_image_links_with_html_img_tag(markdown)
#
#     assert result == expected