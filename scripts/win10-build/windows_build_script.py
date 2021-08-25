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


VERSION = '1.4.1'
TEST_DIR = 'D:\\yanom-versions'
ZIP_FILENAME = f'yanom-v{VERSION}-win10-64'


def main():
    remove_existing_build_folders()
    copy_spec_file_to_source()
    build_package()
    create_zip_of_package()
    extract_package_to_test_dir()
    copy_to_main_dist_folder()


def copy_to_main_dist_folder():
    print('copy distribution zip file to project root dist folder')
    shutil.copy2(f'{ZIP_FILENAME}.zip', '../../dist')


def extract_package_to_test_dir():
    if Path(f'{TEST_DIR}\\{VERSION}').exists():
        shutil.rmtree(f'{TEST_DIR}\\{VERSION}')

    print(f"Extracting zip file to test dir - {TEST_DIR}")
    shutil.unpack_archive(f'{ZIP_FILENAME}.zip', f'{TEST_DIR}\\{VERSION}', 'zip')


def create_zip_of_package():
    with contextlib.suppress(FileNotFoundError):
        os.remove(f'{ZIP_FILENAME}.zip')

    print("Creating zip file of package")
    shutil.make_archive(f'{ZIP_FILENAME}', 'zip', root_dir='dist')


def build_package():
    PyInstaller.__main__.run([
        '--clean',
        '../../src/yanom.spec'
    ])

    print("Create dist/data dir")
    Path('dist/data').mkdir(exist_ok=True)

    copy_pandoc_to_yanom_folder()
    copy_shortcut_file_to_yanom_folder()
    copy_config_file_to_data_folder()


def copy_pandoc_to_yanom_folder():
    try:
        result = subprocess.run('xcopy  /e /i /y "c:\\Program Files\\Pandoc" dist\\pandoc')
        result.check_returncode()
        print('pandoc copied to dist folder')
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
    shutil.copy('../../src/config.ini', 'dist/data')


def copy_shortcut_file_to_yanom_folder():
    if not Path('yanom.exe - Shortcut.lnk').exists():
        print('yanom shortcut missing')
        sys.exit(1)

    print("Copy YANOM shortcut")
    shutil.copy('yanom.exe - Shortcut.lnk', 'dist')


def copy_spec_file_to_source():
    # if not Path('one_dir/yanom.spec').exists():
    if not Path('one_file/yanom.spec').exists():
        print('spec file missing')
        sys.exit(1)

    print("Copy spec file to src")
    # shutil.copy('one_dir/yanom.spec', '../../src')
    shutil.copy('one_file/yanom.spec', '../../src')


def remove_existing_build_folders():
    print('Remove existing dist and build folders')
    with contextlib.suppress(FileNotFoundError):
        print("Remove existing windows dist and build folders if exist")
        shutil.rmtree('dist')
        shutil.rmtree('build')


if __name__ == "__main__":
    main()
