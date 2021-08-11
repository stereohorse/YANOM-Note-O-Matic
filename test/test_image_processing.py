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
        ("""![Some alt text with | a pipe](attachments/12345678.png)""",
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
         """![alt text [with] brackets|600](attachments/12345678.png)""",
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
                """![Some alt text with | a pipe and a width [and] brackets|400](attachments/12345678.png)""",
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
