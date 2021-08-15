"""
Builds a windows packaged version of YANOM

Creates pyInstaller build, places a zipped copy in dist folder, extracts a copy to a test directory
"""

import contextlib
import os
import sys
from pathlib import Path
import shutil
import subprocess

import PyInstaller.__main__


VERSION = '1.4.0'
TEST_DIR = 'D:\\yanom-versions'
ZIP_FILENAME = f'yanom-v{VERSION}-win10-64'


def main():

    remove_existing_build_folders()

    copy_spec_file_to_source()

    build_package()

    create_zip_of_pakcage()

    extract_package_to_test_dir()


def extract_package_to_test_dir():
    if Path(f'{TEST_DIR}\\{VERSION}').exists():
        shutil.rmtree(f'{TEST_DIR}\\{VERSION}')

    print(f"Extracting zip file to test dir - {TEST_DIR}")
    shutil.unpack_archive(f'../../dist/{ZIP_FILENAME}.zip', f'{TEST_DIR}\\{VERSION}', 'zip')


def create_zip_of_pakcage():
    with contextlib.suppress(FileNotFoundError):
        os.remove('../../dist/{ZIP_FILENAME}')

    print("Creating zip file of package")
    shutil.make_archive(f'../../dist/{ZIP_FILENAME}', 'zip', root_dir='dist', base_dir='yanom')


def build_package():
    PyInstaller.__main__.run([
        '--clean',
        '../../src/yanom.spec'
    ])

    print("Create yanom/data dir")
    Path('./../src/dist/yanom/data').mkdir(exist_ok=True)

    copy_pandoc_to_yanom_folder()
    copy_shortcut_file_to_yanom_folder()
    copy_config_file_to_data_folder()


def copy_pandoc_to_yanom_folder():
    try:
        result = subprocess.run('xcopy  /e /i /y "c:\\Program Files\\Pandoc" dist\\yanom\\pandoc')
        result.check_returncode()
    except subprocess.CalledProcessError as e:
        print(f'error copying pandoc - {e}')
        xcopy_exit_codes = {0: 'Files were copied without error.',
                            1: 'No files were found to copy.',
                            2: 'The user pressed CTRL+C to terminate xcopy.',
                            4: 'Initialization error occurred. There is not enough memory or disk space, or you entered an invalid drive name or invalid syntax on the command line.',
                            5: 'Disk write error occurred.',
                            }
        print(xcopy_exit_codes[e.returncode])
        sys.exit(1)


def copy_config_file_to_data_folder():
    if not Path('../../src/config.ini').exists():
        print('config.ini missing')
        sys.exit(1)

    print("Copy config.ini")
    shutil.copy('../../src/config.ini', 'dist/yanom/data')


def copy_shortcut_file_to_yanom_folder():
    if not Path('yanom.exe - Shortcut.lnk').exists():
        print('yanom shorcut missing')
        sys.exit(1)

    print("Copy YANOM shortcut")
    shutil.copy('yanom.exe - Shortcut.lnk', 'dist/yanom')


def copy_spec_file_to_source():
    if not Path('yanom.spec').exists():
        print('spec file missing')
        sys.exit(1)

    print("Copy spec file")
    shutil.copy('yanom.spec', '../../src')


def remove_existing_build_folders():
    with contextlib.suppress(FileNotFoundError):
        print("Remove existing windows dist and build folders if exist")
        shutil.rmtree('../../src/dist')
        shutil.rmtree('../../src/build')


if __name__ == "__main__":
    main()

