# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project follows something close to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) as there is no public API yet then the following guide applies.

- Increment the patch number when you ship a bug fix
- Increment the minor version number when adding a new feature or set of features and any current bug fixes not yet released
- Increment the major version when significantly overhaul the user interface, or rewrite all internals.


## [1.4.0] - developing

### Added
- Updated file and directory name cleaning.
  - Allows any characters except null and Windows reserved characters 
  - Windows reserved file names are prepended with underscore on all operating systems.
  - Spaces are replaced by dash.

## [1.3.3] - 2021-08-01

### Added
- Mouse support in the interactive command line questions.
- NSX conversion.
  - Filenames and directories can now have unicode characters.
  - Filenames and directories from nsx with quoted characters will be unquoted.
  
### Changed
- Change PyInquirer from imported pypi package to git submodule using fork of the original PyInquirer.
  - Add mouse support for command line interface. Items can be mouse clicked, where there is a list of choices (radio butotns) or text entry the return key must be used to move to next question.
  - In list questions, the last value used or value from config.ini is at its original place in the list rather than moving it to the top of list as the default option in the new PyInquirer code now works.
- Add check for valid working directory when saving config.ini
- Replace directory and filename cleaning functions.  
  - If cleaned name becomes and empty string generate random name.
  - Allow unicode characters in names.
  - Unquote non-ASCII (uses utf-8).
- Changes for logging and exception handling.
  - Increased logging around changing file names and directories and any issues creating them on disk.
  - Exceptions now log traceback.
  - Warning level log file now created and populated.
  - Unhandled exceptions are now handled and logged,
  - Logging now commences slightly earlier in program startup,
- All calls to get values from json data now check the key exists and logs if it is not and handle the absence of the key.  This allows for unknown versions of nsx files, that may have missing key values, attempt to continue conversion.
  - If note json data does not have a key for encrypt the assumption is the note is not encrypted.  Note text will appear encrypted after conversion if the note is actually encrypted.
  - If notes or notebooks data is missing from the nsx file the note or notebook is skipped rather than exiting the program.
  - Parent notebook key and id are missing from the nsx note data the note will be placed in the Recycle Bin notebook directory.
- If export folder or attachment folder names are blank in config.ini or the interactive command line tool YANOM defaults of 'notes' and 'attachments'.
- With an attempted read of an encrypted attachment from the nsx file sys.exit is no longer called.  A warning is logged and execution continues.
- Tidy up docker files using best practices.  No functional changes. Removed no longer used ubuntu docker file.
- Tests updated and improved as opportunities identified.

#### Fixed
- Fatal Error when user clicks with mouse in interactive command line.  Now supports mouse, no longer reliant on user only using keyboard.
- Fixed unknown nsx format with missing encrypt key causes error.  Add defensive checks around json data requests for potential unknown nsx formats.
- Fixed possible error due to name cleaning resulting in zero length name.  Replaced file and directory cleaning functions that do not return zero length names.
- Fixed keyboard interrupt in a PyInquirer question printed traceback to screen.  No longer prints traceback, traceback will be logged.

## [1.3.2] - 2021-07-23

### Added
- Refactor image tag processing - improved efficiency.

### Fixed
- Potential pandoc failure when converting single row tables from nsx file.
- Metadata keys named 'content' would make 3rd party library raise an exception.  Now manually iterate the metadata items instead of using 3rd party function.
- Metadata key of 'charset' would make 3rd party library raise an exception.
- File renaming for duplicate attachment names for nsx export - fixes bug introduced in 1.3.0 that resulted in duplicate names over writing each other, now duplicates are renamed.
- Catch attachments set as null in nsx file, continue to convert note but there will be no attachments. log file records a WARNING message.
- Web version of note station can export encrypted notes. Check for and filter out encrypted notes from nsx files.  The encrypted notes are not converted and a warning is placed in the log file.

## [1.3.1] - 2021-07-22

### Fixed
- Exporting NSX where the notebook name had a dot `.` in it would create a correct notebook directory but the notes would try to save in a directory that was just the part before the dot `1234.567` became `1234` when saving files. NOw files are saved correctly using full directory name.

## [1.3.0] - 2021-06-16

### Added
- Exporting to 'pandoc-markdown' now uses YANOM's metadata parser giving wider choice of metadata keys to be parsed or not parsed.  The export only produces a YAML front matter section.
- Can now add a tag prefix to tag metadata values in front matter sections.  This is not required by most markdown readers, but is an option if required.
- Re-write of algorithm to match links between note pages. Now only a single link to a page needs to be valid in any notebook in a nsx export file for renamed links to that page to be corrected.

### Changed
- Add tests for chart processing, image processing, metadata processing, pandoc processing, synology attachment processing, zip file handling, timer, inter note link processing, notes converter, nsx file converter, synology notebook processing, synology note page processing.
- Windows pyinstaller package is no longer 'onefile' due to Windows Defender issues.

### Fixed
- Fix html tag widths were coded incorrectly when cleaning nsx html formatting prior to any conversion.
- Image tag prefix is now correctly implemented.
- Under a packaged runtime environment replacing a missing config.ini would fail.

## [1.2.0] - 2021-05-25

### Added
- Add support for export files from the Synology DSM Note-Station web app.  Export files are slightly different format from the desktop app.
- For Note-Station conversion, add option to select chart elements to reproduce image, csv and data table, or any combination of the three.
- Removed requirement to install pandoc for packaged versions.

### Changed
- Code refactoring and cleaning
  - sn_note_writer refactored to generic file writer and used by additional converters
  - Minor simplifications in  nsx_file_converter and sn_notebook
  - sn_zipfile reader simplified to function
  - conversion_settings simplified form factory object generator to a single class and methods for quick settings for simpler management of settings that should persist when selecting a quick setting.
  - chart_processing moved Chart class to be an inner class of ChartProcessor and changed signature of init to accept 3 booleans for the three available chart options.
- Additional documentation added, docstrings and README files.
- Additional tests writen for checklist processing, helper functions, chart processing, conversion settings, file writer.
- Changed pandoc version testing from `distutils` to `packaging`.

### Fixed
- Testing identified a potential issue where an HTML `a` anchor tag that does not have a `href` inside of it would cause an error when searching for links between note pages during html to markdown conversion.


## [1.1.0] - 2021-05-14
### Added
- Support for iframes in HTML to Markdown and NSX files to Markdown.
- Progress bars during conversion.

### Fixed
- Note-Station program exports the 'My Notebook' with no title.  Now detect this and give the notebook it's 'My Notebook' title.
- Image width detection now detects widths with `px` appended to the width.

## [1.0.0] - 2021-05-09
### Initial release functionality

- project [wiki](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki) covering installation, use and functionality etc.
- Convert Note-Station `.nsx` export files to Markdown or HTML
- Convert HTML to Markdown
- Convert Markdown to HTML
- Convert Markdown to a different format of Markdown
- List of available Markdown formats that can be used as inputs or outputs
  - CommonMark  (Used by Joplin)
  - GFM - Git Flavoured Markdown  (Typora, Git Hub, Haroopad) 
  - Obsidian formatted markdown 
  - MultiMarkdown (MultiMarkdown Composer) 
  - Pandoc markdown 
  - Pandoc markdown-strict 
  - QOwnNotes optimised markdown-
- Note content that will be converted successfully
  - Headers
  - Bulleted lists
  - Numbered lists
  - Checklists
  - Tables
  - Images 
  - Image width where supported in Markdown 
  - IFrames 
  - Metadata - support JSON, TOML or YAML front matter, and `meta` tags in HTML
  - Tags 
    - included in front matter, html header or as plain text with an optional prefix character
    - option to split grouped tags photography/landscape/winter becomes #photography, #landscape, #winter
    - option to remove spaces from tag names
  - Tags 
  - File attachments are maintained
  - Note-Station specific features
    - Charts are recreated.  An image is placed on the page, along with a data table of the chart data, and a link to a csv file of the data.      
    - Links between note pages.
      - For Note-Station most of the time this will be successful.  However, there are some limitations and the [Synology Note-Station Links to Other Note Pages](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki/Synology-Note-Station-Links-to-Other-Note-Pages) wiki page has examples of the possible issues and solutions for them.
    - Note-Station audio notes - are attached as an attachment
    - Option to include creation time in file name


