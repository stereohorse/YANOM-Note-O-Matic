import unittest
from conversion_settings import ConversionSettings
from file_converter_MD_to_HTML import MDToHTMLConverter
from pathlib import Path
from testfixtures import TempDirectory

from content_link_management import get_attachment_paths, update_href_link_suffix_in_content
import file_mover
from metadata_processing import MetaDataProcessor



class TestMDToHTMLConverter(unittest.TestCase):
    def setUp(self):
        self.conversion_settings = ConversionSettings()
        self.conversion_settings.set_quick_setting('gfm')
        files_to_convert = [Path('not_existing.md'),
                            Path('some_markdown-old-1.md'),
                            Path('renaming source file failed'),
                            Path('a_folder/test_md_file.md'),
                            ]
        self.file_converter = MDToHTMLConverter(self.conversion_settings, files_to_convert)
        self.file_converter._metadata_processor = MetaDataProcessor(self.conversion_settings)

    def test_pre_process_obsidian_image_links_if_required(self):
        test_strings = [
            ('obsidian',
             '![|600](filepath/image.png)',
             '<img src="filepath/image.png" width="600" />',
             'obsidian link to gfm failed',
             ),
            ('obsidian',
             '![](filepath/image.png)',
             '![](filepath/image.png)',
             'markdown std link not left unchanged',
             ),
            ('obsidian',
             '![|some-text](filepath/image.png)',
             '![|some-text](filepath/image.png)',
             'markdown std with pipe and text link not left unchanged',
             ),
            ('commonmark',
             '![](filepath/image.png)',
             '![](filepath/image.png)',
             'non obsidian input image incorrectly changed',
             ),
        ]

        for test_set in test_strings:
            with self.subTest(msg=f'Testing image link format {test_set[1]} conversion'):
                self.conversion_settings.markdown_conversion_input = test_set[0]
                self.file_converter._pre_processed_content = test_set[1]
                self.file_converter.pre_process_obsidian_image_links_if_required()
                self.assertEqual(test_set[2],
                                 self.file_converter._pre_processed_content,
                                 test_set[3])

    def test_parse_metadata_if_required(self):
        test_strings = [
            ('pandoc_markdown',
             '---\nexcerpt: tl;dr\nlayout: post\ntitle: TITLE\n---\n\n# Hello',
             '# Hello',
             'pandoc_markdown pre processing for meta data failed'),
            ('gfm',
             '---\nexcerpt: tl;dr\nlayout: post\ntitle: TITLE\n---\n\n# Hello',
             '# Hello',
             'pre processing for meta data failed'),
        ]
        for test_set in test_strings:
            with self.subTest(msg='testing meta data handling'):
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
                    self.assertEqual(test_set[2], self.file_converter._pre_processed_content, test_set[3])

    def test_update_note_links(self):
        self.file_converter._files_to_convert = [Path('not_existing.md'),
                                                 Path('some_markdown-old-1.md'),
                                                 Path('renaming source file failed'),
                                                 Path('a_folder/test_md_file.md'),
                                                 Path('a_folder/test_.md_file.md'),
                                                 ]

        content = '<p><a href="a_folder/test_md_file.md">md file</a></p>' \
                  '<p><a href="a_folder/test_.md_file.md">md file  with dot md in name</a></p>' \
                  '<p><a href="a_folder/test_pdf_file.pdf">non md file file</a>' \
                  '</p><p><a href="https://a_folder/test_pdf_file.md">web md file</a></p>' \
                  '<p><a href="a_folder/not_in_convert_list.md">non md file file</a></p>'

        self.file_converter._output_extension = '.html'
        new_content = update_href_link_suffix_in_content(content,
                                                         self.file_converter._output_extension,
                                                         self.file_converter._files_to_convert)

        print(content)
        print(new_content)
        self.assertTrue('<p><a href="a_folder/test_md_file.html">md file</a></p>' in new_content,
                        'clean md file extension not changed correctly',
                        )
        self.assertTrue('<p><a href="a_folder/test_.md_file.html">md file  with dot md in name</a></p>'
                        in new_content,
                        ' md file with dot md in name  not changed correctly',
                        )
        self.assertTrue('<p><a href="a_folder/test_pdf_file.pdf">non md file file</a></p>'
                        in new_content,
                        'non md file extension changed incorrectly',
                        )
        self.assertTrue('</p><p><a href="https://a_folder/test_pdf_file.md">web md file</a></p>'
                        in new_content,
                        'internet md file extension changed incorrectly',
                        )
        self.assertTrue('<p><a href="a_folder/not_in_convert_list.md">non md file file</a></p>'
                        in new_content,
                        'file with md file extension not in to be changed list changed incorrectly',
                        )

    def test_pre_process_content2_rename_existing_file_and_its_link_in_content(self):
        self.file_converter._file_content = '[existing_md](a-file.md)\n<a href="a-file.md">should change</a>'
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

            assert self.file_converter._pre_processed_content \
                   == '[existing_md](a-file-old-1.md)\n<a href="a-file-old-1.md">should change</a>'

    def test_post_process_content(self):
        self.file_converter._conversion_settings.markdown_conversion_input = 'gfm'
        self.file_converter._converted_content = '<head><title>-</title></head><p><a href="a_folder/test_md_file.md">md file</a></p>'
        self.file_converter._metadata_processor._metadata = {'title': 'My Title'}
        self.file_converter._conversion_settings.export_format = 'html'
        self.file_converter._output_extension = file_mover.get_file_suffix_for(self.file_converter._conversion_settings.export_format)
        self.file_converter._file = Path('a_folder/file.html')
        self.file_converter.post_process_content()
        self.assertEqual(
            '<head><title>My Title</title><meta title="My Title"/></head><p><a href="a_folder/test_md_file.html">md file</a></p>',
            self.file_converter._post_processed_content,
            'title and meta data inserted incorrectly',
        )

    def test_add_meta_data_if_required(self):
        self.file_converter._conversion_settings.markdown_conversion_input = 'gfm'
        self.file_converter._post_processed_content = '<head><title>-</title></head><p><a href="a_folder/test_md_file.md">md file</a></p>'
        self.file_converter._metadata_processor._metadata = {'title': 'My Title'}
        self.file_converter.add_meta_data_if_required()
        self.assertEqual(
            '<head><title>My Title</title><meta title="My Title"/></head><p><a href="a_folder/test_md_file.md">md file</a></p>',
            self.file_converter._post_processed_content,
            'title and meta data inserted incorrectly',
        )

        self.file_converter._conversion_settings.markdown_conversion_input = 'pandoc_markdown'
        self.file_converter._post_processed_content = '<head><title>-</title></head><p><a href="a_folder/test_md_file.md">md file</a></p>'
        self.file_converter._metadata_processor._metadata = {'title': 'My Title'}
        self.file_converter.add_meta_data_if_required()
        self.assertEqual(
            '<head><title>My Title</title><meta title="My Title"/></head><p><a href="a_folder/test_md_file.md">md file</a></p>',
            self.file_converter._post_processed_content,
            'title and meta data inserted incorrectly with markdown conversion input',
        )


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
    #                    f'[a web link](https:\\www.google.com "google")\n' \
    #                    f'<img src="attachments/ten.png" />\n' \
    #                    f'<a href="attachments/eleven.pdf">example-attachment.pdf</a>\n' \
    #                    f'![copyable](attachments/file%20twelve.pdf)\n' \
    #                    f'<a href="attachments/file%20thirteen.pdf">example-attachment.pdf</a>\n' \
    #                    f'<img src="attachments/file%20fourteen.png" />'

    conversion_settings = ConversionSettings()
    conversion_settings.source = Path(tmp_path, 'some_folder/data')
    conversion_settings.export_folder = Path(tmp_path, 'some_folder/export')
    conversion_settings.export_format = 'html'
    file_converter = MDToHTMLConverter(conversion_settings, 'files_to_convert')
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

    assert Path(tmp_path, 'some_folder/data/my_other_notebook/attachments/five.pdf') \
           in attachment_links.copyable_absolute

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file twelve.pdf') \
           in attachment_links.copyable_absolute

    assert len(attachment_links.copyable_absolute) == 5

    assert Path(tmp_path, 'some_folder/data/my_notebook/attachments/file thirteen.pdf') \
           in attachment_links.non_existing

    assert len(attachment_links.non_existing) == 1
