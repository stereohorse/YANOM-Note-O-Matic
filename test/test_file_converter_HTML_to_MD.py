from pathlib import Path
import unittest

from testfixtures import TempDirectory

from src.conversion_settings import ConversionSettings
from src.file_converter_HTML_to_MD import HTMLToMDConverter
from src.metadata_processing import MetaDataProcessor


class TestHTMLToMDConverter(unittest.TestCase):

    def setUp(self):
        self.conversion_settings = ConversionSettings()
        self.conversion_settings.set_quick_setting('gfm')
        files_to_convert = [Path('not_existing.md'),
                            Path('some_markdown-old-1.md'),
                            Path('renaming source file failed'),
                            Path('test_html_file.md'),
                            Path('/a_folder/test_html_file.html'),
                            ]
        self.file_converter = HTMLToMDConverter(self.conversion_settings, files_to_convert)
        self.file_converter._metadata_processor = MetaDataProcessor(self.conversion_settings)

    def test_pre_process_content(self):
        self.file_converter._file_content = '<head><meta title="this is test2"/><meta not_valid="not_in_schema"/></head><p><input checked="" type="checkbox"/>Check 1</p><p><input type="checkbox"/>Check 2</p><p><a href="/a_folder/test_html_file.html">html file</a></p>'
        self.file_converter._metadata_schema = ['title']
        self.file_converter._file = Path('a-file.html')
        self.file_converter._conversion_settings.export_format = 'obsidian'
        with TempDirectory() as d:
            self.file_converter._conversion_settings.source = Path(d.path)
            self.file_converter._conversion_settings.export_folder = Path(d.path)

            self.file_converter.pre_process_content()
            self.assertTrue('checklist-placeholder-id' in self.file_converter._pre_processed_content, 'Failed to insert checklist placeholders')
            self.assertTrue('<p><a href="/a_folder/test_html_file.md">html file</a></p>' in self.file_converter._pre_processed_content, 'Failed to change link extension placeholders')
            self.assertTrue({'title': 'this is test2'} == self.file_converter._metadata_processor.metadata, 'Failed to parse meta data')

    def test_post_process_content2(self):
        self.file_converter._file_content = '<head><meta title="this is test2"/><meta not_valid="not_in_schema"/></head><p><input checked="" type="checkbox"/>Check 1</p><p><input type="checkbox"/>Check 2</p><img src="filepath/image.png" width="600"><p><iframe allowfullscreen="" anchorhref="https://www.youtube.com/watch?v=SqdxNUMO2cg" frameborder="0" height="315" src="https://www.youtube.com/embed/SqdxNUMO2cg" width="420" youtube="true"> </iframe></p>'
        self.file_converter._metadata_schema = ['title']
        self.file_converter._file = Path('a-file.html')
        self.file_converter._conversion_settings.export_format = 'pandoc_markdown'
        with TempDirectory() as d:
            self.file_converter._conversion_settings.source = Path(d.path)
            self.file_converter._conversion_settings.export_folder = Path(d.path)
            self.file_converter.pre_process_content()
            self.file_converter.convert_content()
            self.file_converter._metadata_processor._conversion_settings.front_matter_format = 'toml'  # set toml and confirm content is forced back into yaml
            self.file_converter.post_process_content()
            self.assertEqual(
                '---\ntitle: this is test2\n---\n\n- [x] Check 1\n\n- [ ] Check 2\n\n<img src="filepath/image.png" width="600" />\n\n\n<iframe allowfullscreen="" anchorhref="https://www.youtube.com/watch?v=SqdxNUMO2cg" frameborder="0" height="315" src="https://www.youtube.com/embed/SqdxNUMO2cg" width="420" youtube="true"> </iframe>\n\n',
                self.file_converter._post_processed_content,
                'post processing failed'
                )

    def test_post_process_content3(self):
        self.file_converter._file_content = '<head><meta title="this is test2"/><meta not_valid="not_in_schema"/></head><p><input checked="" type="checkbox"/>Check 1</p><p><input type="checkbox"/>Check 2</p><img src="filepath/image.png" width="600">'
        self.file_converter._metadata_schema = ['title']
        self.file_converter._file = Path('a-file.html')
        self.file_converter._conversion_settings.export_format = 'obsidian'
        self.file_converter.pre_process_content()
        self.file_converter.convert_content()
        self.file_converter.post_process_content()
        assert self.file_converter._post_processed_content == '---\ntitle: this is test2\n---\n\n- [x] Check 1\n\n- [ ] Check 2\n\n![|600](filepath/image.png)\n'

    def test_parse_metadata_if_required(self):
        self.file_converter._conversion_settings.export_format = 'obsidian'
        self.file_converter._metadata_processor._metadata = {}
        self.file_converter._metadata_processor._metadata_schema = ['title', 'creation_time']
        self.file_converter._pre_processed_content = '<head><meta title="this is test2"/><meta creation_time="test-meta-content"/></head>'
        self.file_converter.parse_metadata_if_required()
        self.assertEqual({'title': 'this is test2'},
                         self.file_converter._metadata_processor.metadata,
                         'meta data not parsed correctly'
                         )

        self.file_converter._metadata_processor._metadata = {}
        self.file_converter._metadata_processor._metadata_schema = ['title']
        self.file_converter._pre_processed_content = '<meta title="this is test2"/><meta creation_time="test-meta-content"/>'
        self.file_converter.parse_metadata_if_required()
        self.assertEqual({},
                         self.file_converter._metadata_processor.metadata,
                         'meta data not ignored if no head section'
                         )

        self.file_converter._metadata_processor._metadata = {}
        self.file_converter._metadata_processor._metadata_schema = ['title']
        self.file_converter._pre_processed_content = '<head><meta title="this is test2"/><meta not_valid="not_in_schema"/></head>'
        self.file_converter.parse_metadata_if_required()
        self.assertEqual({'title': 'this is test2'},
                         self.file_converter._metadata_processor.metadata, 'meta data not parsed correctly')

        self.file_converter._conversion_settings.export_format = 'pandoc_markdown'
        self.file_converter._metadata_processor._metadata = {}
        self.file_converter._metadata_processor._metadata_schema = ['title', 'creation_time']
        self.file_converter._pre_processed_content = '<head><meta title="this is test2"/><meta creation_time="test-meta-content"/></head>'
        self.file_converter.parse_metadata_if_required()
        self.assertEqual({'title': 'this is test2'},
                         self.file_converter._metadata_processor.metadata,
                         'meta data not parsed correctly'
                         )


def test_generate_set_of_attachment_paths_markdown_export_format(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').touch()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').touch()
    Path(tmp_path, 'some_folder/three.png').touch()
    Path(tmp_path, 'some_folder/attachments/four.csv').touch()
    Path(tmp_path, 'some_folder/four.csv').touch()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    file_path = Path(tmp_path, 'some_folder/data/my_notebook/note.md')
    content = f'![copyable|600]({str(tmp_path)}/some_folder/data/my_notebook/attachments/one.png)\n' \
              f'![non-existing|600]({str(tmp_path)}/some_folder/two.png)\n' \
              f'![non-copyable|600]({str(tmp_path)}/some_folder/three.png)\n' \
              f'![non-existing|600](attachments/three.pdf)\n' \
              f'![copyable|600](attachments/eight.pdf)\n' \
              f'![copyable](../attachments/two.csv)\n' \
              f'![non-copyable](../../attachments/four.csv)\n' \
              f'![non-existing](../my_notebook/seven.csv)\n' \
              f'![copyable](../my_notebook/six.csv)\n' \
              f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
              f'![note link](nine.md)\n' \
              f'[a web link](https:\\www.google.com "google")\n' \
              f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'

    expected_content = f'![copyable|600]({str(tmp_path)}/some_folder/data/my_notebook/attachments/one.png)\n' \
                       f'![non-existing|600]({str(tmp_path)}/some_folder/two.png)\n' \
                       f'![non-copyable|600]({str(tmp_path)}/some_folder/three.png)\n' \
                       f'![non-existing|600](attachments/three.pdf)\n' \
                       f'![copyable|600](attachments/eight.pdf)\n' \
                       f'![copyable](../attachments/two.csv)\n' \
                       f'![non-copyable](../attachments/four.csv)\n' \
                       f'![non-existing](../my_notebook/seven.csv)\n' \
                       f'![copyable](../my_notebook/six.csv)\n' \
                       f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
                       f'![note link](nine.md)\n' \
                       f'[a web link](https:\\www.google.com "google")\n' \
                       f'<img src="attachments/ten.png" />\n' \
                       f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
                       f'![copyable](attachments/file%20twelve.pdf)\n' \
                       f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
                       f'<img src="attachments/file%20fourteen.png" />'

    conversion_settings = ConversionSettings()
    conversion_settings.source = Path(tmp_path, 'some_folder/data')
    conversion_settings.export_folder = Path(tmp_path, 'some_folder/export')
    conversion_settings.export_format = 'obsidian'
    conversion_settings.make_absolute = False
    file_converter = HTMLToMDConverter(conversion_settings, 'files_to_convert')
    file_converter._file = file_path
    file_converter._files_to_convert = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md')}
    result_content = file_converter.handle_attachment_paths(content)

    assert Path(tmp_path,
                'some_folder/data/my_other_notebook/attachments/five.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/one.png') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/six.csv') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/attachments/two.csv') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/eight.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/ten.png') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/eleven.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/file twelve.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/file fourteen.png') in file_converter._copyable_attachment_absolute_path_set
    assert len(file_converter._copyable_attachment_absolute_path_set) == 9

    assert Path(tmp_path, 'some_folder/two.png') in file_converter._non_existing_links_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/three.pdf') in file_converter._non_existing_links_set
    assert Path(tmp_path, 'some_folder/data/my_notebook/seven.csv') in file_converter._non_existing_links_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/file thirteen.pdf') in file_converter._non_existing_links_set
    assert len(file_converter._non_existing_links_set) == 4

    # NOTE for the "some_folder/attachments/four.csv" attachment the content should be updated to a new relative link
    # assert Path(tmp_path, 'some_folder/attachments/four.csv') in file_converter._non_copyable_attachment_path_set
    assert Path('../../attachments/four.csv') in file_converter._non_copyable_attachment_path_set
    assert Path(tmp_path, 'some_folder/three.png') in file_converter._non_copyable_attachment_path_set
    assert len(file_converter._non_copyable_attachment_path_set) == 2

    assert result_content == expected_content


def test_generate_set_of_attachment_paths_where_make_absolute_for_non_copyable_files(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_notebook/note.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png').touch()
    Path(tmp_path, 'some_folder/data/attachments/two.csv').touch()
    Path(tmp_path, 'some_folder/three.png').touch()
    Path(tmp_path, 'some_folder/attachments/four.csv').touch()
    Path(tmp_path, 'some_folder/four.csv').touch()
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/six.csv').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    file_path = Path(tmp_path, 'some_folder/data/my_notebook/note.md')
    content = f'![copyable|600]({str(tmp_path)}/some_folder/data/my_notebook/attachments/one.png)\n' \
              f'![non-existing|600]({str(tmp_path)}/some_folder/two.png)\n' \
              f'![non-copyable|600]({str(tmp_path)}/some_folder/three.png)\n' \
              f'![non-copyable|600](../../three.png)\n' \
              f'![non-existing|600](attachments/three.pdf)\n' \
              f'![copyable|600](attachments/eight.pdf)\n' \
              f'![copyable](../attachments/two.csv)\n' \
              f'![non-copyable](../../attachments/four.csv)\n' \
              f'![non-existing](../my_notebook/seven.csv)\n' \
              f'![copyable](../my_notebook/six.csv)\n' \
              f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
              f'![note link](nine.md)\n' \
              f'[a web link](https:\\www.google.com "google")\n' \
              f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'

    expected_content = f'![copyable|600]({str(tmp_path)}/some_folder/data/my_notebook/attachments/one.png)\n' \
                       f'![non-existing|600]({str(tmp_path)}/some_folder/two.png)\n' \
                       f'![non-copyable|600]({str(tmp_path)}/some_folder/three.png)\n' \
                       f'![non-copyable|600]({str(tmp_path)}/some_folder/three.png)\n' \
                       f'![non-existing|600](attachments/three.pdf)\n' \
                       f'![copyable|600](attachments/eight.pdf)\n' \
                       f'![copyable](../attachments/two.csv)\n' \
                       f'![non-copyable]({str(tmp_path)}/some_folder/attachments/four.csv)\n' \
                       f'![non-existing](../my_notebook/seven.csv)\n' \
                       f'![copyable](../my_notebook/six.csv)\n' \
                       f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
                       f'![note link](nine.md)\n' \
                       f'[a web link](https:\\www.google.com "google")\n' \
                       f'<img src="attachments/ten.png" />\n' \
                       f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
                       f'![copyable](attachments/file%20twelve.pdf)\n' \
                       f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
                       f'<img src="attachments/file%20fourteen.png" />'

    conversion_settings = ConversionSettings()
    conversion_settings.source = Path(tmp_path, 'some_folder/data')
    conversion_settings.export_folder = Path(tmp_path, 'some_folder/export')
    conversion_settings.export_format = 'obsidian'
    conversion_settings.make_absolute = True
    file_converter = HTMLToMDConverter(conversion_settings, 'files_to_convert')
    file_converter._file = file_path
    file_converter._files_to_convert = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md')}
    result_content = file_converter.handle_attachment_paths(content)

    assert Path(tmp_path,
                'some_folder/data/my_other_notebook/attachments/five.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/one.png') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/six.csv') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/attachments/two.csv') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/eight.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/ten.png') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/eleven.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/file twelve.pdf') in file_converter._copyable_attachment_absolute_path_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/file fourteen.png') in file_converter._copyable_attachment_absolute_path_set
    assert len(file_converter._copyable_attachment_absolute_path_set) == 9

    assert Path(tmp_path, 'some_folder/two.png') in file_converter._non_existing_links_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/three.pdf') in file_converter._non_existing_links_set
    assert Path(tmp_path, 'some_folder/data/my_notebook/seven.csv') in file_converter._non_existing_links_set
    assert Path(tmp_path,
                'some_folder/data/my_notebook/attachments/file thirteen.pdf') in file_converter._non_existing_links_set
    assert len(file_converter._non_existing_links_set) == 4

    assert Path('../../attachments/four.csv') in file_converter._non_copyable_attachment_path_set
    assert Path(tmp_path, 'some_folder/three.png') in file_converter._non_copyable_attachment_path_set
    # There is no 3rd path to test as three.png is used twice, once with relative path and once with absolute path
    assert len(file_converter._non_copyable_attachment_path_set) == 3

    assert result_content == expected_content
