from pathlib import Path
from unittest.mock import patch

import config
import pytest

import config_data
from conversion_settings import ConversionSettings
import interactive_cli


@pytest.fixture
def good_config_ini() -> str:
    return """[conversion_inputs]
    # valid entries are html, markdown, nimbus, nsx
    #  nsx = synology note station export file
    #  html = simple html based notes pages, no complex css or javascript
    #  markdown =  text files in markdown format
conversion_input = nsx

[markdown_conversion_inputs]
    # valid entries are obsidian, gfm, commonmark, q_own_notes, pandoc_markdown_strict, pandoc_markdown, multimarkdown
markdown_conversion_input = gfm

[quick_settings]
    # valid entries are q_own_notes, obsidian, gfm, pandoc_markdown, commonmark, pandoc_markdown_strict, multimarkdown, html
    # use manual to use the manual settings in the sections below
    # note if an option other than - manual - is used the rest of the 
    # settings in this file will be set automatically
    #
quick_setting = obsidian
    # 
    # the following sections only apply if the above is set to manual
    #  

[export_formats]
    # valid entries are q_own_notes, obsidian, gfm, pandoc_markdown, commonmark, pandoc_markdown_strict, multimarkdown, html
export_format = obsidian

[meta_data_options]
    # note: front_matter_format sets the presence and type of the section with metadata 
    # retrieved from the source
    # valid entries are yaml, toml, json, text, none
    # no entry will result in no front matter section
front_matter_format = yaml
    # metadata schema is a comma separated list of metadata keys that you wish to 
    # restrict the retrieved metadata keys. for example 
    # title, tags    will return those two if they are found
    # if left blank any meta data found will be used
    # the useful available keys in an nsx file are title, ctime, mtime, tag
metadata_schema = title,ctime,mtime,tag
    # tag prefix is a character you wish to be added to the front of any tag values 
    # retrieved from metadata.  note use this if using front matter format "text" 
    # or use is your markdown system uses a prefix in a front matter section (most wil not use a prefix) 
tag_prefix = #
    # spaces_in_tags if true will maintain spaces in tag words, if false spaces are replaced by a dash -
spaces_in_tags = False
    # split tags will split grouped tags into individual tags if true
    # "tag1", "tag1/sub tag2"  will become "tag1", "sub tag2"
    # grouped tags are only split where a "/" character is found
split_tags = False
    # meta data time format used for nsx only - enter a valid strftime date and time format with 
    # additional % signs to escape the first % sign
    # 3 examples are %%y-%%m-%%d %%h:%%m:%%s%%z    %%y-%%m-%%d %%h:%%m:%%s   %%y%%m%%d%%h%%m
    # for formats see https://strftime.org/
    # if left blank will default to %%y-%%m-%%d %%h:%%m:%%s%%z
metadata_time_format = %%Y-%%m-%%d %%H:%%M:%%S%%Z

[table_options]
  #  these two table options apply to nsx files only
first_row_as_header = True
first_column_as_header = True

[chart_options]
  #  these three chart options apply to nsx files only
chart_image = True
chart_csv = True
chart_data_table = True

[file_options]
source = 
export_folder = notes-15
attachment_folder_name = attachments
    # the following options apply to directory names, and currently only apply filenames in nsx conversions.
allow_spaces_in_filenames = True
filename_spaces_replaced_by = -
allow_unicode_in_filenames = True
allow_uppercase_in_filenames = True
allow_non_alphanumeric_in_filenames = True
creation_time_in_exported_file_name = True
    # if true creation time as `yyyymmddhhmm-` will be added as prefix to file name
max_file_or_directory_name_length = 255
    # the following options apply to directory names, and currently only apply to html and markdown conversions.
orphans = copy
    # orphans are files that are not linked to any notes.  valid values are
    # ignore - orphan files are left where they are and are not moved to an export folder.
    # copy - orphan files are coppied to the export folder in the same relative locations as the source.
    # orphan - orphan files are moved to a directory named orphan in the export folder.
make_absolute = False
    # links to files that are not in the path forwards of the source directory will be 
    # changed to absolute links if set to true.  for example "../../someplace/some_file.pdf"
    # becomes /root/path/to/someplace/some_file.pdf"
    # false will leave these links unchanged as relative links

[nimbus_options]
    # the following options apply to nimbus notes conversions
embed_these_document_types = md,pdf
embed_these_image_types = png,jpg,jpeg,gif,bmp,svg
embed_these_audio_types = mp3,webm,wav,m4a,ogg,3gp,flac
embed_these_video_types = mp4,webm,ogv
keep_nimbus_row_and_column_headers = False
    # for unrecognised html tags use either html or plain text
    # html = inline html in markdown and html in html files
    # text = extract any text and display as plain text in markdown and html
unrecognised_tag_format = html
"""


@pytest.fixture
def good_config_ini_no_notes_or_attachment_folder() -> str:
    return """[conversion_inputs]
    # valid entries are html, markdown, nimbus, nsx
    #  nsx = synology note station export file
    #  html = simple html based notes pages, no complex css or javascript
    #  markdown =  text files in markdown format
conversion_input = nsx

[markdown_conversion_inputs]
    # valid entries are obsidian, gfm, commonmark, q_own_notes, pandoc_markdown_strict, pandoc_markdown, multimarkdown
markdown_conversion_input = gfm

[quick_settings]
    # valid entries are q_own_notes, obsidian, gfm, pandoc_markdown, commonmark, pandoc_markdown_strict, multimarkdown, html
    # use manual to use the manual settings in the sections below
    # note if an option other than - manual - is used the rest of the 
    # settings in this file will be set automatically
    #
quick_setting = obsidian
    # 
    # the following sections only apply if the above is set to manual
    #  

[export_formats]
    # valid entries are q_own_notes, obsidian, gfm, pandoc_markdown, commonmark, pandoc_markdown_strict, multimarkdown, html
export_format = obsidian

[meta_data_options]
    # note: front_matter_format sets the presence and type of the section with metadata 
    # retrieved from the source
    # valid entries are yaml, toml, json, text, none
    # no entry will result in no front matter section
front_matter_format = yaml
    # metadata schema is a comma separated list of metadata keys that you wish to 
    # restrict the retrieved metadata keys. for example 
    # title, tags    will return those two if they are found
    # if left blank any meta data found will be used
    # the useful available keys in an nsx file are title, ctime, mtime, tag
metadata_schema = title,ctime,mtime,tag
    # tag prefix is a character you wish to be added to the front of any tag values 
    # retrieved from metadata.  note use this if using front matter format "text" 
    # or use is your markdown system uses a prefix in a front matter section (most wil not use a prefix) 
tag_prefix = #
    # spaces_in_tags if true will maintain spaces in tag words, if false spaces are replaced by a dash -
spaces_in_tags = False
    # split tags will split grouped tags into individual tags if true
    # "tag1", "tag1/sub tag2"  will become "tag1", "sub tag2"
    # grouped tags are only split where a "/" character is found
split_tags = False
    # meta data time format used for nsx only - enter a valid strftime date and time format with 
    # additional % signs to escape the first % sign
    # 3 examples are %%y-%%m-%%d %%h:%%m:%%s%%z    %%y-%%m-%%d %%h:%%m:%%s   %%y%%m%%d%%h%%m
    # for formats see https://strftime.org/
    # if left blank will default to %%y-%%m-%%d %%h:%%m:%%s%%z
metadata_time_format = %%Y-%%m-%%d %%H:%%M:%%S%%Z

[table_options]
  #  these two table options apply to nsx files only
first_row_as_header = True
first_column_as_header = True

[chart_options]
  #  these three chart options apply to nsx files only
chart_image = True
chart_csv = True
chart_data_table = True

[file_options]
source = 
export_folder = 
attachment_folder_name = 
    # the following options apply to directory names, and currently only apply filenames in nsx conversions.
allow_spaces_in_filenames = True
filename_spaces_replaced_by = -
allow_unicode_in_filenames = True
allow_uppercase_in_filenames = True
allow_non_alphanumeric_in_filenames = True
creation_time_in_exported_file_name = True
    # if true creation time as `yyyymmddhhmm-` will be added as prefix to file name
max_file_or_directory_name_length = 255
    # the following options apply to directory names, and currently only apply to html and markdown conversions.
orphans = copy
    # orphans are files that are not linked to any notes.  valid values are
    # ignore - orphan files are left where they are and are not moved to an export folder.
    # copy - orphan files are coppied to the export folder in the same relative locations as the source.
    # orphan - orphan files are moved to a directory named orphan in the export folder.
make_absolute = False
    # links to files that are not in the path forwards of the source directory will be 
    # changed to absolute links if set to true.  for example "../../someplace/some_file.pdf"
    # becomes /root/path/to/someplace/some_file.pdf"
    # false will leave these links unchanged as relative links

[nimbus_options]
    # the following options apply to nimbus notes conversions
embed_these_document_types = md,pdf
embed_these_image_types = png,jpg,jpeg,gif,bmp,svg
embed_these_audio_types = mp3,webm,wav,m4a,ogg,3gp,flac
embed_these_video_types = mp4,webm,ogv
keep_nimbus_row_and_column_headers = False
    # for unrecognised html tags use either html or plain text
    # html = inline html in markdown and html in html files
    # text = extract any text and display as plain text in markdown and html
unrecognised_tag_format = html
"""


def test_initialisation(tmp_path):
    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    assert isinstance(cd, config_data.ConfigData)


def test_read_config_file_file_missing(tmp_path, caplog):
    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    caplog.clear()

    cd.read_config_file()

    assert cd.conversion_settings.export_format == 'gfm'

    assert len(caplog.records) > 0

    for record in caplog.records:
        if record.levelname == "WARNING":
            assert 'config.ini missing at' in record.message


@pytest.mark.parametrize(
    'silent, expected', [
        (True, ''),
        (False, 'config.ini missing, generating new file.\n')
    ], ids=['silent-mode', 'not-silent']
)
def test_read_config_missing_file(tmp_path, caplog, capsys, silent, expected):

    config.yanom_globals.is_silent = silent

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.read_config_file()

    assert len(caplog.records) > 0

    assert caplog.records[0].levelname == "WARNING"

    captured = capsys.readouterr()
    assert captured.out == expected


def test_validate_config_file_good_file(tmp_path, good_config_ini):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.read_config_file()
    valid_config = cd.validate_config_file()
    assert valid_config


def test_validate_good_config_ini_no_notes_or_attachment_folder(tmp_path, good_config_ini_no_notes_or_attachment_folder):
    Path(f'{str(tmp_path)}/data').mkdir()
    Path(f'{str(tmp_path)}/data/config.ini').write_text(good_config_ini_no_notes_or_attachment_folder, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/data/config.ini", 'gfm', allow_no_value=True)
    cd.conversion_settings.working_directory = Path(tmp_path)

    cd.parse_config_file()
    assert cd.conversion_settings.export_folder == Path('notes')
    assert cd.conversion_settings.attachment_folder_name == Path('attachments')


@pytest.mark.parametrize(
    'key1, key2, bad_value', [
        ('conversion_inputs', 'conversion_input', 'bad-value-1234'),
        ('markdown_conversion_inputs', 'markdown_conversion_input', 'bad-value-1234'),
        ('quick_settings', 'quick_setting', 'bad-value-1234'),
        ('export_formats', 'export_format', 'bad-value-1234'),
        ('meta_data_options', 'front_matter_format', 'bad-value-1234'),
        ('meta_data_options', 'spaces_in_tags', 'bad-value-1234'),
        ('meta_data_options', 'split_tags', 'bad-value-1234'),
        ('table_options', 'first_row_as_header', 'bad-value-1234'),
        ('table_options', 'first_column_as_header', 'bad-value-1234'),
        ('chart_options', 'chart_image', 'bad-value-1234'),
        ('chart_options', 'chart_csv', 'bad-value-1234'),
        ('chart_options', 'chart_data_table', 'bad-value-1234'),
        ('file_options', 'creation_time_in_exported_file_name', 'bad-value-1234'),
        ('file_options', 'orphans', 'invalid-value'),
        ('file_options', 'make_absolute', 'invalid-value'),
    ]
)
def test_validate_config_file_bad_values(tmp_path, good_config_ini, key1, key2, bad_value):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.read_config_file()
    cd[key1][key2] = bad_value
    valid_config = cd.validate_config_file()
    assert valid_config is False


@pytest.mark.parametrize(
    'replace_this, with_this', [
        ('[quick_settings]', ''),
        ('quick_setting = obsidian', '')
    ],
    ids=['missing-section', 'missing-key']
)
def test_validate_config_file_missing_keys_and_sections(tmp_path, good_config_ini, replace_this, with_this):

    good_config_ini = good_config_ini.replace(replace_this, with_this)

    Path(tmp_path, 'data').mkdir()
    Path(f'{str(tmp_path)}/data/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/data/config.ini", 'gfm', allow_no_value=True)

    cd.read_config_file()
    valid_config = cd.validate_config_file()
    assert valid_config is False


@pytest.mark.parametrize(
    'key1, key2, start_value, end_value, expected', [
        ('conversion_inputs', 'conversion_input', 'nsx', 'html', 'html'),
        ('markdown_conversion_inputs', 'markdown_conversion_input', 'obsidian', 'gfm', 'gfm'),
        ('quick_settings', 'quick_setting', 'obsidian', 'commonmark', 'commonmark'),
        ('export_formats', 'export_format', 'obsidian', 'multimarkdown', 'multimarkdown'),
        ('meta_data_options', 'front_matter_format', 'yaml', 'toml', 'toml'),
        ('meta_data_options', 'metadata_schema', 'title,ctime,mtime,tag', 'something_different',
         ['something_different']),
        ('meta_data_options', 'tag_prefix', '#', '@', '@'),
        ('meta_data_options', 'spaces_in_tags', 'False', 'True', True),
        ('meta_data_options', 'split_tags', 'False', 'True', True),
        ('table_options', 'first_row_as_header', 'True', 'False', False),
        ('table_options', 'first_column_as_header', 'True', 'False', False),
        ('chart_options', 'chart_image', 'True', 'False', False),
        ('chart_options', 'chart_csv', 'True', 'False', False),
        ('chart_options', 'chart_data_table', 'True', 'False', False),
        ('file_options', 'export_folder', 'export_orig', 'export_new', Path('export_new')),
        ('file_options', 'attachment_folder_name', 'attachment_orig', 'attachment_new', Path('attachment_new')),
        ('file_options', 'creation_time_in_exported_file_name', 'True', 'False', False),
        ('file_options', 'orphans', 'copy', 'ignore', 'ignore'),
        ('file_options', 'make_absolute', 'True', 'False', False),
        ('nimbus_options', 'embed_these_document_types', 'pdf,docx', 'something_different',
         ['something_different']),
        ('nimbus_options', 'embed_these_image_types', 'pdf,docx', 'something_different',
         ['something_different']),
        ('nimbus_options', 'embed_these_audio_types', 'pdf,docx', 'something_different',
         ['something_different']),
        ('nimbus_options', 'embed_these_video_types', 'pdf,docx', 'something_different',
         ['something_different']),
        ('nimbus_options', 'unrecognised_tag_format', 'html', 'text', 'text'),
    ]
)
def test_generate_conversion_settings_from_parsed_config_file_data(good_config_ini, tmp_path, key1, key2, start_value,
                                                                   end_value, expected):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.read_config_file()

    # empty the source entry for config data as will cause error when generating conversion settings
    cd['file_options']['source'] = ''

    # set start value for conversion setting
    setattr(cd.conversion_settings, key2, start_value)
    # change value as if read from another file
    cd[key1][key2] = end_value
    # convert config parser object to conversion settings
    cd.generate_conversion_settings_from_parsed_config_file_data()
    # confirm conversion setting has changed
    assert getattr(cd.conversion_settings, key2) == expected


def test_generate_conversion_settings_from_parsed_config_file_data_test_markdown_pandoc_front_matter_setting(good_config_ini, tmp_path):
    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.read_config_file()

    cd['export_formats']['export_format'] = 'pandoc_markdown'
    cd['meta_data_options']['front_matter_format'] = 'toml'

    cd.generate_conversion_settings_from_parsed_config_file_data()

    assert cd.conversion_settings.front_matter_format == 'yaml'


def test_generate_conversion_settings_from_parsed_config_file_data_test_source_setting(good_config_ini, tmp_path):
    # by inducing a system exit we know the new path was passed into config_settings correctly
    # the error is raised when the source setter sees an invalid path
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.read_config_file()

    # set the source location
    cd['file_options']['source'] = 'new_source'

    # confirm conversion_settings source is empty
    assert cd.conversion_settings.source == ''

    # convert config parser object to conversion settings
    with pytest.raises(SystemExit) as exc:
        cd.generate_conversion_settings_from_parsed_config_file_data()

    assert isinstance(exc.type, type(SystemExit))
    assert str(exc.value) == '1'


def test_conversion_settings_property_obj_confirm_obj_read(tmp_path, good_config_ini):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cs = ConversionSettings()

    cs.quick_set_multimarkdown_settings()

    cd.conversion_settings = cs

    assert cd.conversion_settings.export_format == 'multimarkdown'
    assert cd['export_formats']['export_format'] == 'multimarkdown'


def test_conversion_settings_proprty_obj_confirm_config_file_written(tmp_path, good_config_ini):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cs = ConversionSettings()

    cs.quick_set_multimarkdown_settings()

    cd.conversion_settings = cs

    cd.read_config_file()

    assert cd['export_formats']['export_format'] == 'multimarkdown'


def test_conversion_settings_proprty_obj_confirm_string_setting(tmp_path, good_config_ini):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.conversion_settings = 'multimarkdown'

    assert cd.conversion_settings.export_format == 'multimarkdown'
    assert cd['export_formats']['export_format'] == 'multimarkdown'


def test_conversion_settings_property_string_setting_confirm_config_file_written(tmp_path, good_config_ini):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.conversion_settings = 'multimarkdown'

    cd.read_config_file()

    assert cd['export_formats']['export_format'] == 'multimarkdown'


def test_parse_config_file(good_config_ini, tmp_path):
    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.parse_config_file()

    assert cd.conversion_settings.export_format == 'obsidian'


def test_parse_config_file_invalid_config_file(good_config_ini, tmp_path):
    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    with patch('config_data.ConfigData.validate_config_file',
               spec=True) as mock_validate_config_file:
        with patch('config_data.ConfigData.ask_user_to_choose_new_default_config_file',
                   spec=True) as mock_ask_user_to_choose_new_default_config_file:
            mock_validate_config_file.return_value = False
            cd.parse_config_file()

    mock_validate_config_file.assert_called_once()
    mock_ask_user_to_choose_new_default_config_file.assert_called_once()


def test_ask_user_to_choose_new_default_config_file_user_choose_exit(good_config_ini, tmp_path, monkeypatch):
    print('hello')

    def patched_cli(_):
        return 'exit'

    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    monkeypatch.setattr(interactive_cli.InvalidConfigFileCommandLineInterface, 'run_cli', patched_cli)

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    with pytest.raises(SystemExit) as exc:
        cd.ask_user_to_choose_new_default_config_file()

    assert isinstance(exc.type, type(SystemExit))
    assert str(exc.value) == '0'


def test_ask_user_to_choose_new_default_config_file_user_choose_new_file(good_config_ini, tmp_path, monkeypatch):
    import interactive_cli

    def patched_cli(_):
        return 'default'

    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    monkeypatch.setattr(interactive_cli.InvalidConfigFileCommandLineInterface, 'run_cli', patched_cli)

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cd.ask_user_to_choose_new_default_config_file()

    assert cd.conversion_settings.export_format == 'gfm'


def test_str(good_config_ini, tmp_path):
    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")
    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)
    cd.parse_config_file()

    result = str(cd)
    assert result == "ConfigData{'conversion_inputs': {'conversion_input': 'nsx'}, 'markdown_conversion_inputs': {'markdown_conversion_input': 'gfm'}, 'quick_settings': {'quick_setting': 'obsidian'}, 'export_formats': {'export_format': 'obsidian'}, 'meta_data_options': {'front_matter_format': 'yaml', 'metadata_schema': 'title,ctime,mtime,tag', 'tag_prefix': '#', 'spaces_in_tags': 'False', 'split_tags': 'False', 'metadata_time_format': '%Y-%m-%d %H:%M:%S%Z'}, 'table_options': {'first_row_as_header': 'True', 'first_column_as_header': 'True'}, 'chart_options': {'chart_image': 'True', 'chart_csv': 'True', 'chart_data_table': 'True'}, 'file_options': {'source': '', 'export_folder': 'notes-15', 'attachment_folder_name': 'attachments', 'allow_spaces_in_filenames': 'True', 'filename_spaces_replaced_by': '-', 'allow_unicode_in_filenames': 'True', 'allow_uppercase_in_filenames': 'True', 'allow_non_alphanumeric_in_filenames': 'True', 'creation_time_in_exported_file_name': 'True', 'max_file_or_directory_name_length': '255', 'orphans': 'copy', 'make_absolute': 'False'}, 'nimbus_options': {'embed_these_document_types': 'md,pdf', 'embed_these_image_types': 'png,jpg,jpeg,gif,bmp,svg', 'embed_these_audio_types': 'mp3,webm,wav,m4a,ogg,3gp,flac', 'embed_these_video_types': 'mp4,webm,ogv', 'keep_nimbus_row_and_column_headers': 'False', 'unrecognised_tag_format': 'html'}}"


def test_repr(good_config_ini, tmp_path):
    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")
    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)
    cd.parse_config_file()

    result = repr(cd)
    assert result == "ConfigData{'conversion_inputs': {'conversion_input': 'nsx'}, 'markdown_conversion_inputs': {'markdown_conversion_input': 'gfm'}, 'quick_settings': {'quick_setting': 'obsidian'}, 'export_formats': {'export_format': 'obsidian'}, 'meta_data_options': {'front_matter_format': 'yaml', 'metadata_schema': 'title,ctime,mtime,tag', 'tag_prefix': '#', 'spaces_in_tags': 'False', 'split_tags': 'False', 'metadata_time_format': '%Y-%m-%d %H:%M:%S%Z'}, 'table_options': {'first_row_as_header': 'True', 'first_column_as_header': 'True'}, 'chart_options': {'chart_image': 'True', 'chart_csv': 'True', 'chart_data_table': 'True'}, 'file_options': {'source': '', 'export_folder': 'notes-15', 'attachment_folder_name': 'attachments', 'allow_spaces_in_filenames': 'True', 'filename_spaces_replaced_by': '-', 'allow_unicode_in_filenames': 'True', 'allow_uppercase_in_filenames': 'True', 'allow_non_alphanumeric_in_filenames': 'True', 'creation_time_in_exported_file_name': 'True', 'max_file_or_directory_name_length': '255', 'orphans': 'copy', 'make_absolute': 'False'}, 'nimbus_options': {'embed_these_document_types': 'md,pdf', 'embed_these_image_types': 'png,jpg,jpeg,gif,bmp,svg', 'embed_these_audio_types': 'mp3,webm,wav,m4a,ogg,3gp,flac', 'embed_these_video_types': 'mp4,webm,ogv', 'keep_nimbus_row_and_column_headers': 'False', 'unrecognised_tag_format': 'html'}}"


def test_generate_conversion_settings_using_quick_settings_string(good_config_ini, tmp_path):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'obsidian', allow_no_value=True)

    # remove the config.ini so we can check it is saved
    Path(f'{str(tmp_path)}/config.ini').unlink()
    assert not Path(f'{str(tmp_path)}/config.ini').exists()

    cd.generate_conversion_settings_using_quick_settings_string('gfm')
    assert Path(f'{str(tmp_path)}/config.ini').exists()
    assert cd['quick_settings']['quick_setting'] == 'gfm'


@pytest.mark.parametrize(
    'silent, expected', [
        (True, ''),
        (False, 'Unable to save config.ini file')
    ], ids=['silent-mode', 'not-silent']
)
def test_generate_conversion_settings_using_quick_settings_string_to_forced_bad_directory(good_config_ini,
                                                                                          tmp_path,
                                                                                          caplog,
                                                                                          capsys,
                                                                                          monkeypatch,
                                                                                          silent,
                                                                                          expected):
    """Force a bad directory into the config.ini save method to check it is handled and logged"""

    config.yanom_globals.is_silent = silent
    Path(tmp_path, 'data').mkdir()
    Path(tmp_path, 'data', 'config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(str(Path(tmp_path, 'data', 'config.ini')), 'obsidian', allow_no_value=True)

    # remove the config.ini so we can check a new one is saved
    Path(tmp_path, 'data', 'config.ini').unlink()
    assert not Path(tmp_path, 'config.ini').exists()
    cd._config_file = 'config.ini'

    monkeypatch.setattr(ConversionSettings, 'working_directory', Path(tmp_path, "abc"))
    cd.generate_conversion_settings_using_quick_settings_string('gfm')
    assert not Path(tmp_path, 'abc', 'config.ini').exists()
    assert not Path(tmp_path, 'config.ini').exists()

    assert caplog.records
    assert f"Unable to save config.ini file '{Path(tmp_path, 'abc/data')}' is not a directory. No such file or directory" in caplog.messages

    captured = capsys.readouterr()
    assert expected in captured.out


def test_generate_conversion_settings_using_quick_settings_string_bad_value(good_config_ini, tmp_path, caplog):
    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    with pytest.raises(ValueError):
        cd.generate_conversion_settings_using_quick_settings_string('invalid')

    assert 'is not a recognised quick setting string' in caplog.records[-1].message


def test_generate_conversion_settings_using_quick_settings_object(good_config_ini, tmp_path):
    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cs = ConversionSettings()
    cs.quick_set_commonmark_settings()
    cd.generate_conversion_settings_using_quick_settings_object(cs)

    assert cd['quick_settings']['quick_setting'] == 'commonmark'


def test_generate_conversion_settings_using_quick_settings_object_bad_value(good_config_ini, tmp_path, caplog):
    good_config_ini = good_config_ini.replace('source = my_source', 'source = ')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)

    cs = ''

    with pytest.raises(TypeError):
        cd.generate_conversion_settings_using_quick_settings_object(cs)

    assert 'Passed invalid value' in caplog.records[-1].message


def test_set_default_time_format(good_config_ini, tmp_path):
    good_config_ini = good_config_ini.replace('metadata_time_format = %%Y-%%m-%%d %%H:%%M:%%S%%Z', 'metadata_time_format = ')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)
    cd.parse_config_file()

    assert cd['meta_data_options']['metadata_time_format'] == ''
    assert cd.conversion_settings.metadata_time_format == '%Y-%m-%d %H:%M:%S%Z'


def test_set_time_format(good_config_ini, tmp_path):
    good_config_ini = good_config_ini.replace('metadata_time_format = %%Y-%%m-%%d %%H:%%M:%%S%%Z', 'metadata_time_format = %%Y')

    Path(f'{str(tmp_path)}/config.ini').write_text(good_config_ini, encoding="utf-8")

    cd = config_data.ConfigData(f"{str(tmp_path)}/config.ini", 'gfm', allow_no_value=True)
    cd.parse_config_file()

    assert cd['meta_data_options']['metadata_time_format'] == '%Y'
    assert cd.conversion_settings.metadata_time_format == '%Y'