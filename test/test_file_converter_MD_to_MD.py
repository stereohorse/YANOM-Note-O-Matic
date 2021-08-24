from pathlib import Path
import unittest

from testfixtures import TempDirectory

from content_link_management import get_attachment_paths
from src.conversion_settings import ConversionSettings
from src.file_converter_MD_to_MD import MDToMDConverter
import file_mover
from src.metadata_processing import MetaDataProcessor


class TestMDToMDConverter(unittest.TestCase):

    def setUp(self):
        self.conversion_settings = ConversionSettings()
        self.conversion_settings.set_quick_setting('gfm')
        files_to_convert = [Path('not_existing.md'),
                            Path('some_markdown-old-1.md'),
                            Path('renaming source file failed')]
        self.file_converter = MDToMDConverter(self.conversion_settings, files_to_convert)
        self.file_converter._metadata_processor = MetaDataProcessor(self.conversion_settings)

    def test_add_meta_data_if_required(self):
        test_data_sets = [
            ('Hello',
             {},
             'gfm',
             'Hello',
             'no meta data, content was incorrect'
             ),
            ('Hello',
             {'excerpt': 'tl;dr', 'layout': 'post', 'title': 'Hello, world!'},
             'gfm',
             '---\nexcerpt: tl;dr\nlayout: post\ntitle: Hello, world!\n---\n\nHello',
             'good meta string and content failed'
             ),
            ('Hello',
             {'excerpt': 'tl;dr', 'layout': 'post', 'title': 'Hello, world!'},
             'pandoc_markdown',
             '---\nexcerpt: tl;dr\nlayout: post\ntitle: Hello, world!\n---\n\nHello',
             'good meta string and content failed'
             )
        ]

        for test_set in test_data_sets:
            with self.subTest(msg=f'Testing {test_set}'):
                self.file_converter._post_processed_content = test_set[0]
                self.file_converter._metadata_processor._metadata = test_set[1]
                self.file_converter._conversion_settings.markdown_conversion_input = test_set[2]
                self.file_converter.add_meta_data_if_required()
                self.assertEqual(test_set[3],
                                 self.file_converter._post_processed_content,
                                 test_set[4])

    def test_parse_metadata_if_required(self):
        test_data_sets = [
            ('---\nexcerpt: tl;dr\nlayout: post\ntitle: Hello, world!\n---\n\nHello',
             'gfm',
             {'title': 'Hello, world!'},
             'good meta string failed',
             'Hello',
             'good meta string failed'
             ),
            ('Hello',
             'gfm',
             {},
             'no meta string failed',
             'Hello',
             'no meta string failed'
             ),
            ('---\nthis :is:nonsense\nmore\nnonsense\n---\n\nHello',
             'gfm',
             {},
             'bad meta data failed',
             'Hello',
             'bad meta data failed'
             ),
            ('---\nexcerpt: tl;dr\nlayout: post\ntitle: Hello, world!\n---\n\nHello',
             'pandoc_markdown',
             {'title': 'Hello, world!'},
             'good meta failed with pandoc_markdown',
             'Hello',
             'good meta with pandoc_markdown failed'
             )
        ]
        for test_set in test_data_sets:
            with self.subTest(msg=f'Testing {test_set}'):
                self.file_converter._pre_processed_content = test_set[0]
                self.file_converter._conversion_settings.markdown_conversion_input = test_set[1]
                self.file_converter.parse_metadata_if_required()
                self.assertEqual(test_set[2], self.file_converter._metadata_processor.metadata, test_set[3])
                self.assertEqual(test_set[4], self.file_converter._pre_processed_content, test_set[5])

    def test_rename_target_file_if_already_exists(self):
        test_strings = [
            ('some_markdown.md',
             'not_existing.md',
             'some_markdown-old-1.md',
             'renaming source file failed'),
            ('some_markdown.md',
             'some_markdown-old-1.md',
             'some_markdown-old-2.md',
             'renaming for existing old file failed'),
        ]
        for test_set in test_strings:
            with self.subTest(msg=f'Testing when existing old set to {test_set[0]}'):
                with TempDirectory() as d:
                    # the order here is a little messy but it has to be like this not have the export folder renamed
                    # as if it is renamed then the new folder is empty and the rename existing file never runs

                    # set source to an existing folder
                    self.file_converter._conversion_settings.source = Path(d.path)
                    # set export folder to non-existing folder so is an empty folder
                    self.file_converter._conversion_settings.export_folder = Path(d.path, 'export')
                    # make the export folder
                    Path(d.path, 'export').mkdir(exist_ok=True)
                    # change the source to the export folder to where the source file will be
                    self.file_converter._conversion_settings.source = Path(d.path, 'export')
                    # put the source file in the folder
                    source_file = Path(d.path, 'export', test_set[0])
                    source_file.touch()
                    source_file_old_exists = Path(d.path, 'export', test_set[1])
                    source_file_old_exists.touch()
                    self.assertTrue(source_file.exists())
                    self.assertTrue(source_file_old_exists.exists())
                    self.file_converter._file = source_file
                    self.file_converter.rename_target_file_if_it_already_exists()
                    self.assertTrue(Path(d.path, 'export', test_set[2]).exists(), test_set[3])

        with TempDirectory() as d:
            self.file_converter._file = Path('does_not_exist.md')
            self.file_converter._conversion_settings.source = Path(d.path)
            self.file_converter._conversion_settings.export_folder = Path(d.path)
            self.file_converter.rename_target_file_if_it_already_exists()
            self.assertFalse(Path(d.path,
                             'does_not_exist.md').exists(),
                             'failed to manage a not existing file name',
                             )
            self.assertFalse(Path(d.path,
                             'does_not_exist-old.md').exists(),
                             'failed to manage a not existing file name',
                             )
            self.assertFalse(Path(d.path,
                             'does_not_exist-old-1.md').exists(),
                             'failed to manage a not existing file name',
                             )

    def test_pre_process_obsidian_image_links_if_required(self):
        test_strings = [
            ('obsidian',
             '![|600](filepath/image.png)',
             '<img src="filepath/image.png" width="600" />',
             'obsidian link to gfm failed'),
            ('obsidian',
             '![](filepath/image.png)',
             '![](filepath/image.png)',
             'markdown std link not left unchanged'),
            ('obsidian',
             '![|some-text](filepath/image.png)',
             '![|some-text](filepath/image.png)',
             'markdown std with pipe and text link not left unchanged',),
            ('commonmark',
             '![](filepath/image.png)',
             '![](filepath/image.png)',
             'non obsidian input image incorrectly changed')
        ]

        for test_set in test_strings:
            with self.subTest(msg=f'Testing image link format {test_set[1]} conversion'):
                self.conversion_settings.markdown_conversion_input = test_set[0]
                self.file_converter._pre_processed_content = test_set[1]
                self.file_converter.pre_process_obsidian_image_links_if_required()
                self.assertEqual(test_set[2],
                                 self.file_converter._pre_processed_content,
                                 test_set[3])

    def test_pre_process_content(self):
        test_strings = [
            ('obsidian',
             '![|600](filepath/image.png)',
             '<img src="filepath/image.png" width="600" />',
             'obsidian link to gfm failed'),
            ('obsidian',
             '![](filepath/image.png)',
             '![](filepath/image.png)',
             'markdown std link not left unchanged'),
            ('obsidian',
             '![|some-text](filepath/image.png)',
             '![|some-text](filepath/image.png)',
             'markdown std with pipe and text link not left unchanged',),
            ('commonmark',
             '![](filepath/image.png)',
             '![](filepath/image.png)',
             'non obsidian input image incorrectly changed')
        ]

        for test_set in test_strings:
            with self.subTest(msg=f'Testing image link format {test_set[1]} conversion'):
                with TempDirectory() as d:
                    source_file = Path(d.path, 'some_markdown.md')
                    source_file.touch()
                    self.assertTrue(source_file.exists())
                    self.file_converter._file = source_file

                    self.conversion_settings.markdown_conversion_input = test_set[0]
                    self.file_converter._file_content = test_set[1]
                    self.file_converter._conversion_settings.source = Path(d.path)
                    self.file_converter._conversion_settings.export_folder = Path(d.path)
                    self.file_converter.pre_process_content()
                    self.assertEqual(test_set[2],
                                     self.file_converter._pre_processed_content,
                                     test_set[3])

    def test_pre_process_content2_rename_existing_file_and_its_link_in_content(self):
        self.file_converter._file_content = '[existing_md](a-file.md)'
        self.file_converter._metadata_schema = ['title']
        self.file_converter._file = Path('a-file.md')
        self.file_converter._conversion_settings.export_format = 'gfm'
        self.file_converter._conversion_settings.conversion_input = 'markdown'
        with TempDirectory() as d:
            self.file_converter._conversion_settings.source = Path(d.path)
            self.file_converter._conversion_settings.export_folder = Path(d.path)
            Path(d.path, 'a-file.md').touch()

            self.file_converter.pre_process_content()
            assert Path(d.path, 'a-file-old-1.md').exists()

            self.assertTrue('a-file-old-1.md'
                            in self.file_converter._pre_processed_content,
                            'Failed to rename existing file link placeholders',
                            )

    def test_post_process_obsidian_image_links_if_required(self):
        test_strings = [
            ('<img src="filepath/image.png" width="600">',
             '![|600](filepath/image.png)',
             'link not converted to obsidian correctly'
             ),
            ('<img src="filepath/image.png" width="600"/>',
             '![|600](filepath/image.png)',
             'link with closing forward slash not converted to obsidian correctly'
             ),
            ('![](filepath/image.png)',
             '![](filepath/image.png)',
             'std markdown image link not left alone'
             )
        ]
        self.conversion_settings.export_format = 'obsidian'

        for test_set in test_strings:
            with self.subTest(msg=f'Testing image link format {test_set[0]} conversion'):
                self.file_converter._post_processed_content = test_set[0]
                self.file_converter.post_process_obsidian_image_links_if_required()
                self.assertEqual(test_set[1],
                                 self.file_converter._post_processed_content,
                                 test_set[2])

    def test_read_file(self):
        with TempDirectory() as d:
            source_file = Path(d.path, 'some_markdown.md')
            source_file.write_text('hello\nworld!')
            self.file_converter._file = source_file

            self.file_converter.read_file()
            self.assertEqual('hello\nworld!', self.file_converter._file_content, 'failed to read file content')

    def test_convert_content(self):
        self.file_converter._pre_processed_content = '<h1>Header 1</h1>'
        self.file_converter.convert_content()
        self.assertEqual('# Header 1\n', self.file_converter._converted_content, 'failed to convert content')

    def test_write_post_processed_content(self):
        with TempDirectory() as d:
            self.file_converter._file = Path(d.path, 'test.txt')
            self.file_converter._post_processed_content = '# Header 1\n'
            self.file_converter._conversion_settings.source = Path(d.path)
            self.file_converter._conversion_settings.export_folder = Path(d.path)
            self.file_converter.write_post_processed_content()
            output_path = Path(d.path, 'test.md')
            read_text = output_path.read_text()
            self.assertEqual('# Header 1\n', read_text, 'Failed to write content')

    def test_post_process_content(self):
        self.file_converter._pre_processed_content = 'Hello'
        self.file_converter._metadata_processor._metadata = {'test': 'data'}
        self.file_converter._conversion_settings.markdown_conversion_input = 'gfm'
        self.file_converter.post_process_content()

        self.assertEqual('---\ntest: data\n---\n\nHello',
                         self.file_converter._post_processed_content,
                         'failed to post process content 1')

        self.file_converter._pre_processed_content = '---\ntest: data\n---\n\nHello'
        self.file_converter._metadata_processor._metadata = {'title': 'My Title'}
        self.file_converter._conversion_settings.markdown_conversion_input = 'pandoc_markdown'
        self.file_converter.post_process_content()

        self.assertEqual('---\ntitle: My Title\n---\n\nHello',
                         self.file_converter._post_processed_content,
                         'failed to post process content 2')

        self.file_converter._pre_processed_content = '---\ntest: data\n---\n\nHello'
        self.file_converter._metadata_processor._metadata = {'title': 'My Title'}
        self.file_converter._conversion_settings.markdown_conversion_input = 'gfm'
        self.file_converter.post_process_content()

        self.assertEqual('---\ntitle: My Title\n---\n\nHello',
                         self.file_converter._post_processed_content,
                         'failed to post process content 3')

    def test_set_out_put_extension(self):
        extension = file_mover.get_file_suffix_for(self.file_converter._conversion_settings.export_format)
        self.assertEqual('.md', extension, 'failed to select correct md extension')

        self.file_converter._conversion_settings = ConversionSettings()
        self.file_converter._conversion_settings.set_quick_setting('html')
        extension = file_mover.get_file_suffix_for(self.file_converter._conversion_settings.export_format)
        self.assertEqual('.html', extension, 'failed to select correct html extension')

    def test_convert(self):
        self.file_converter._conversion_settings = ConversionSettings()
        self.file_converter._conversion_settings.set_quick_setting('obsidian')
        with TempDirectory() as d:
            self.file_converter._conversion_settings.source = Path(d.path)
            self.file_converter._conversion_settings.export_folder = Path(d.path, 'export')
            Path(d.path, 'export').mkdir()
            source_file = Path(d.path, 'some_markdown.md')
            source_file.write_text('<img src="filepath/image.png" width="600">')

            self.file_converter.convert_note(source_file)

            result = self.file_converter._post_processed_content
            self.assertEqual('![|600](filepath/image.png)', result, 'failed to convert file')


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
              f'[a web link](https://www.google.com "google")\n' \
              f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'
    #
    # expected_content = f'![copyable|600]({str(tmp_path)}/some_folder/data/my_notebook/attachments/one.png)\n' \
    #                    f'![non-existing|600]({str(tmp_path)}/some_folder/two.png)\n' \
    #                    f'![non-copyable|600]({str(tmp_path)}/some_folder/three.png)\n' \
    #                    f'![non-existing|600](attachments/three.pdf)\n' \
    #                    f'![copyable|600](attachments/eight.pdf)\n' \
    #                    f'![copyable](../attachments/two.csv)\n' \
    #                    f'![non-copyable](../attachments/four.csv)\n' \
    #                    f'![non-existing](../my_notebook/seven.csv)\n' \
    #                    f'![copyable](../my_notebook/six.csv)\n' \
    #                    f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
    #                    f'![note link](nine.md)\n' \
    #                    f'[a web link](https://www.google.com "google")\n' \
    #                    f'<img src="attachments/ten.png" />\n' \
    #                    f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
    #                    f'![copyable](attachments/file%20twelve.pdf)\n' \
    #                    f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
    #                    f'<img src="attachments/file%20fourteen.png" />'

    conversion_settings = ConversionSettings()
    conversion_settings.source = Path(tmp_path, 'some_folder/data')
    conversion_settings.export_folder = Path(tmp_path, 'some_folder/export')
    conversion_settings.export_format = 'obsidian'
    file_converter = MDToMDConverter(conversion_settings, 'files_to_convert')
    file_converter._file = file_path
    file_converter._files_to_convert = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md')}
    attachment_links = get_attachment_paths(file_converter._conversion_settings.source_absolute_root,
                                            file_converter._conversion_settings.export_format,
                                            file_converter._file,
                                            file_converter._files_to_convert, content)

    assert Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/one.png') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path,
                'some_folder/data/my_notebook/six.csv') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/attachments/two.csv') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/eight.pdf') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png') \
           in attachment_links.copyable_absolute

    assert len(attachment_links.copyable_absolute) == 9

    assert Path(tmp_path, 'some_folder/two.png') in attachment_links.non_existing

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/three.pdf') \
           in attachment_links.non_existing

    assert Path(tmp_path, 'some_folder/data/my_notebook/seven.csv') in attachment_links.non_existing

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file thirteen.pdf') \
           in attachment_links.non_existing

    assert len(attachment_links.non_existing) == 4

    # NOTE for the "some_folder/attachments/four.csv" attachment the content should be updated to a new relative link
    # assert Path(tmp_path, 'some_folder/attachments/four.csv') in file_converter._non_copyable_attachment_path_set
    assert Path('../../attachments/four.csv') in attachment_links.non_copyable_relative
    assert Path(tmp_path, 'some_folder/three.png') in attachment_links.non_copyable_absolute
    assert len(attachment_links.non_copyable_relative) == 1
    assert len(attachment_links.non_copyable_absolute) == 1


def test_generate_set_of_attachment_paths_html_export_format(tmp_path):
    Path(tmp_path, 'some_folder/data/my_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments').mkdir(parents=True)
    Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/nine.md').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf').touch()
    Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png').touch()

    file_path = Path(tmp_path, 'some_folder/data/my_notebook/note.md')
    content = f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
              f'![note link](nine.md)\n' \
              f'[a web link](https://www.google.com "google")\n' \
              f'<img src="attachments/ten.png" />\n' \
              f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
              f'![copyable](attachments/file%20twelve.pdf)\n' \
              f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
              f'<img src="attachments/file%20fourteen.png" />'

    # expected_content = f'![copyable](../my_other_notebook/attachments/five.pdf "test tool tip text")\n' \
    #                    f'![note link](nine.md)\n' \
    #                    f'[a web link](https://www.google.com "google")\n' \
    #                    f'<img src="attachments/ten.png" />\n' \
    #                    f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
    #                    f'![copyable](attachments/file%20twelve.pdf)\n' \
    #                    f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
    #                    f'<img src="attachments/file%20fourteen.png" />'

    conversion_settings = ConversionSettings()
    conversion_settings.source = Path(tmp_path, 'some_folder/data')
    conversion_settings.export_folder = Path(tmp_path, 'some_folder/export')
    conversion_settings.export_format = 'html'
    file_converter = MDToMDConverter(conversion_settings, 'files_to_convert')
    file_converter._file = file_path
    file_converter._files_to_convert = {Path(tmp_path, 'some_folder/data/my_notebook/nine.md')}
    attachment_links = get_attachment_paths(file_converter._conversion_settings.source_absolute_root,
                                            file_converter._conversion_settings.conversion_input,
                                            file_converter._file,
                                            file_converter._files_to_convert, content)

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/ten.png') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/eleven.pdf') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file fourteen.png') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf') \
           in attachment_links.copyable_absolute

    assert len(attachment_links.copyable_absolute) == 5

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file thirteen.pdf') \
           in attachment_links.non_existing

    assert len(attachment_links.non_existing) == 1
