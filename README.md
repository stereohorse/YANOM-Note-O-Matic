![coverage 91%](https://img.shields.io/badge/coverage-91%25-orange)  ![open issues](https://img.shields.io/github/issues/kevindurston21/YANOM-Note-O-Matic)  ![License](https://img.shields.io/github/license/kevindurston21/YANOM-Note-O-Matic)  ![version tag](https://img.shields.io/github/v/tag/kevindurston21/YANOM-Note-O-Matic)

# YANOM - Yet Another Note-O-Matic
YANOM - stands for Yet Another Note-O-Matic. 

YANOM is a file converter to support the use of non-proprietary open file formats for note-taking systems.

It achieves this by converting proprietary note system formats into Markdown or HTML files.  

Additionally, YANOM has the capability to add support for modified Markdown formats used by specific Markdown note-taking system, for example Obsidian image tags are formatted to support image sizing.

## YANOM's Goals
- To be a user-friendly tool anybody can use, with documentation that is detailed enough for any user to install and use.
- Incrementally support additional proprietary formats and open file formats when possible.

# Sections in this read me are
- [YANOM - Yet Another Note-O-Matic](#yanom---yet-another-note-o-matic)
  * [YANOM's Goals](#yanoms-goals)
- [Sections in this read me are](#sections-in-this-read-me-are)
  * [YANOM Note-O-Matic wiki](#yanom-note-o-matic-wiki)
  * [Version 1.1.0 capabilities](#current-capabilities)
    + [Current functionality](#current-functionality)
  * [Getting Started](#getting-started)
    + [Prerequisites](#prerequisites)
      - [Prerequisites source code](#prerequisites-source-code)
      - [Prerequisite for the Debian packaged version](#prerequisite-for-the-debian-packaged-version)
      - [No prerequisites for the Windows and Mac OSX packaged versions, or the docker image](#no-prerequisites-for-the-windows-and-mac-osx-packaged-versions-or-the-docker-image)
    + [Using the pre-built packaged versions for Debian linux, windows and Mac OSX](#using-the-pre-built-packaged-versions-for-debian-linux-windows-and-mac-osx)
    + [Using the docker image](#using-the-docker-image)
    + [Installing from source code](#installing-from-source-code)
  * [Running the tests](#running-the-tests)
    + [Unit Tests with pytest](#unit-tests-with-pytest)
    + [End-to-end tests](#end-to-end-tests)
  * [Deployment](#deployment)
  * [Contributing](#contributing)
  * [Versioning](#versioning)
  * [Change log](#change-log)
  * [Authors](#authors)
  * [License](#license)
  * [Acknowledgments](#acknowledgments)

## YANOM Note-O-Matic wiki
The [YANOM wiki](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki) explains features, functionality, installation and use in greater detail than this read me.

## Current capabilities 
- Conversion of Synology Note-Station files to markdown or html.  [Full details of the supported features and examples](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki/note-station-conversion-details.md) are in the wiki. 
- Conversion between Markdown formats
- HTML to Markdown and Markdown to HTML

YANOM only exports to HTML or Markdown.

Future versions will support conversion from additional proprietary file formats.  

### Current functionality

- Convert Note-Station `.nsx` export files to Markdown or HTML
- Convert HTML to Markdown
- Convert Markdown to HTML
- Convert Markdown to a different format of Markdown 
- Report details of and issues identified during conversion
  - Detials such as 
    - number of notes converted
    - attachment files and images processed, 
    - links between note recreated
  - Issues identified such as
    - Links between note station notes that could not be recreated
    - Links in notes that are for files that can not be located
    - Orphan Files that exist but are not linked to a note
- User selectable filename and directory name cleaning options (file name cleaning only for nsx files)
- List of available Markdown formats that can be used as inputs or outputs
  - CommonMark  (Used by Joplin)
  - GFM - Git Flavoured Markdown  (Typora, Git Hub, Haroopad) 
  - Obsidian formatted markdown 
  - MultiMarkdown (MultiMarkdown Composer) 
  - Pandoc markdown 
  - Pandoc markdown-strict 
  - QOwnNotes optimised markdown-strict
- Note content that will be converted successfully
  - Headers
  - Bulleted lists
  - Numbered lists
  - Checklists
    - Checklist items that have hyperlinks will maintain the links in exported markdown
  - Tables
  - Images 
  - Image width where supported in Markdown 
  - IFrames
  - Metadata - support JSON, TOML or YAML front matter, and `meta` tags in HTML.  
    - It is also possible include the metadata as plain text at the top of the exported file
    - Option to discard metadata
  - Tags 
    - included in front matter, html header or as plain text with an optional prefix character
    - option to split grouped tags photography/landscape/winter becomes #photography, #landscape, #winter
    - option to remove spaces from tag names, spaces are replaced with hyphen `-`
  - File attachments are maintained
  - Option to 
  - Note-Station specific features
    - Charts are recreated.  Options to place an image, data table of the chart data and, a link to a csv file on the exported page.  
    - If duplicate files are attached to different notes within a notebook only a single copy of the attachment is stored in the attachment folder and links will be to that file.
    - Links between note pages.
      - For Note-Station most of the time this will be successful.  However, there are some limitations and the [Synology Note-Station Links to Other Note Pages](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki/Synology-Note-Station-Links-to-Other-Note-Pages) wiki page has examples of the possible issues and solutions for them.
    - Note-Station audio notes - are attached as an attachment
    - Option to include creation time in file name
    - Add file extension for filenames, for common file types, where extension is missing. This may occur when there are sync issues between desktop and server note station versions.
    - File name cleaning options - in manual mode user can choose to keep/remove spaces, unicode characters, uppercase characters, choose what character to replace spaces with.
    - File name lengths - User can set a maximum file name length. Long note titles can cause issues on Windows where long paths are not enabled, on these systems YANOM restricts file names to 64 characters.
    - Retrieve meta data
    - Some ability to handle nsx files from systems with synchronisation issues, such as attachments with no names or extensions, missing data fields describing the data, however final exported content will be variable quality depending on the synchronisation issue.


The formatting for QOwnNotes and Obsidian are variations on common Markdown formats optimised for those note systems.

## Getting Started

Packaged versions of YANOM have been created, please check the [WIKI](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki) for details on how to install those.

The wiki also includes more detailed instructions on [installing and using the source code](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki) than can be easily documented here.


### Prerequisites

#### Prerequisites source code
YANOM relies on a python environment when run form source code.  

1. You will need to have a working installation of Python 3.6 or higher.  Details of how to install python, and the installation files, can be found on the [python website](https://www.python.org/downloads/)
2. Once Python is installed, install pipenv using `pip install pipenv`.
3. If using PyCharm - Edit your yanom.py Run time settings from the menu 'Run' -> 'Edit configuration..' and tick the "Emulate terminal in output console" option in the 'Execution' section.  This is required for the interactive command line to run.

YANOM also requires Pandoc.  [Pandoc](https://pandoc.org/installing.html) v1.16 or higher should be used and ideally 2.11 or higher as that is where most testing has been done.

#### Prerequisite for the Debian packaged version
Pandoc is required to be installed.

#### No prerequisites for the Windows and Mac OSX packaged versions, or the docker image
The packaged versions include the required python environment and pandoc.


### Using the pre-built packaged versions for Debian linux, windows and Mac OSX

Packaged versions of YANOM are available.  Please see the wiki for how to install and use them.

Also, please note the Mac OSX package is slow to start and can take 20 or more seconds to launch.   The windows versoin takes around 10 seconds to start.

The Mac OSX version is code signed and has been notarised by apple, and should not give any security warnings.

### Using the docker image
A docker image has been created and is available on [docker hub](https://hub.docker.com/r/thehistorianandthegeek/yanom).

For further information on the duse of the YANOM docker image please check the [wiki page](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki/Installing YANOM using Docker.md)

### Installing from source code

Download the source code from [git hub](https://github.com/kevindurston21/YANOM-Note-O-Matic) 

Un-zip the downloaded file.

Use `pip install -r requirements.txt` to install the required dependencies to  run the code.  If you are going to develop the code use `pip install -r requirements_dev.txt` to install additional development dependencies.

>NOTE it has been seen in some linux versions that a dependency for the package `toml` was not installed automatically.   The symptoms seen were that when a file was converted using `toml` as the front matter format YANOM would crash.  The workaround was to use `pipenv install toml` and then YANOM would run OK.

At the command line type `python yanom.py`  if you wish to add command line arguments you just add them like this `python yanom.py --source notes`

For details of the command line options and how to use YANOM please refer to the [Using YANOM](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki/using-yanom.md) wiki page


## Running the tests

### Unit Tests with pytest
Some tests were created to run with unittest, but these also run with pytest.  

Please refer to the [test folder](test) for the test files.

Install [pytest](https://docs.pytest.org/en/6.2.x/getting-started.html) for testing and [pytest-cov](https://pypi.org/project/pytest-cov/) for coverage reports.

You can run all tests and create html coverage report if you use this command in the root of the project

`pytest --cov-report html:cov_html test/ --cov=src`

Current coverage is currently 91%

### End-to-end tests

Only a simple manual end-to-end test process exists.

Conversion is made from the `test.nsx` file to Markdown, using each combination of settings.

One set tof the markdown files generated form the `test.nsx` file is converted to html. 

The generated html files are then converted back into a Markdown format.

## Deployment

Deploying source code to a live environment is addressed in the [wiki](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki)

Deployment of packages is achieved using pyinstaller.  For details see the [wiki](https://github.com/kevindurston21/YANOM-Note-O-Matic/wiki)

## Contributing
Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details on our code of conduct.

Please read [CONTRIBUTING.md](docs/contributing.md) for the process for submitting pull requests to us.

## Versioning

We use [Semantic Versioning](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/kevindurston21/YANOM-Note-O-Matic/tags).

## Change log
Please see [CHANGELOG.md](CHANGELOG.md)

## Authors

* **Kevin Durston**

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE) file for details

## Acknowledgments

- [Maboroshy](https://github.com/Maboroshy) for showing that dissecting an NSX file was possible