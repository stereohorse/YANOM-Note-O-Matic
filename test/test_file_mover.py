from pathlib import Path

import pytest

import file_mover


@pytest.mark.parametrize(
    'file_path, source_absolute, target_root, suffix, expected', [
        ('/stuff/more_stuff/working_path/data/my_note_book/hello.md',
         '/stuff/more_stuff/working_path/data/',
         '/stuff/more_stuff/working_path/data/',
         '.html',
         '/stuff/more_stuff/working_path/data/my_note_book/hello.html'),
        ('/stuff/more_stuff/working_path/data/my_note_book/hello.md',
         '/stuff/more_stuff/working_path/data/',
         '/stuff/other_stuff',
         '.html',
         '/stuff/other_stuff/my_note_book/hello.html'),
        ('/stuff/more_stuff/working_path/data/my_note_book/hello.md',
         '/stuff/yet_more_stuff',
         '/stuff/other_stuff',
         '.html',
         '/stuff/more_stuff/working_path/data/my_note_book/hello.html'),

    ]
)
def test_create_target_path(file_path, source_absolute, target_root, suffix, expected):
    result = file_mover.create_target_absolute_file_path(file_path, source_absolute, target_root, suffix)

    assert result == Path(expected)


# @pytest.mark.parametrize(
#     'source_path, expected', [
#         (r'/stuff/more_stuff/working_path/data/my_note_book/hello.md', 'my_note_book/hello.md'),
#         (r'/stuff/more_stuff/working_path/data/my_note_book/attachments/hello.pdf', 'my_note_book/attachments/hello.pdf'),
#         (r'/stuff/more_stuff/working_path/data/hello.pdf', 'hello.pdf')
#     ]
# )
# def test_create_relative_path_to_working_dir(source_path, expected):
#     source_absolute_root = r'/stuff/more_stuff/working_path/data'
#     result = file_mover.create_relative_path_to_source_root(source_absolute_root, source_path)
#
#     assert result == Path(expected)


# def test_create_absolute_target_path():
#     target_path_route = r'/stuff/more_stuff/working_path/data/notes/'
#     source_relative_path = r'my_note_book/hello.md'
#
#     result = file_mover.create_absolute_target_path(target_path_route, source_relative_path)
#
#     assert result == Path(r'/stuff/more_stuff/working_path/data/notes/my_note_book/hello.md')

@pytest.mark.parametrize(
    'export_format, expected', [
        ('html', '.html'),
        ('anything_else', '.md'),
    ]
)
def test_get_output_file_extension_for(export_format, expected):
    result = file_mover.get_file_suffix_for(export_format)

    assert result == expected
