import contextlib
from pathlib import Path
import shutil
import subprocess
import sys

import PyInstaller.__main__

VERSION = '1.5.1'
NOTARISE_ZIP_FILENAME = f'yanom-v{VERSION}'


def main():
    remove_existing_build_folders()
    copy_spec_file_to_source()
    build_package()
    check_signing()
    print('Check signing and test program locally before submitting for notarisation')
    print('run "2_notarise_package.py" to have the package notarised')


def remove_existing_build_folders():
    with contextlib.suppress(FileNotFoundError):
        print("Remove existing dist and build folders if they exist")
        shutil.rmtree('dist')
        shutil.rmtree('build')


def copy_spec_file_to_source():
    if not Path('one_file/yanom.spec').exists():
        print('spec file missing')
        sys.exit(1)

    print("Copy spec file")
    shutil.copy('one_file/yanom.spec', '../../src')


def build_package():
    PyInstaller.__main__.run([
        '--clean',
        '../../src/yanom.spec'
    ])

    print("Create data dir")
    data_dir = Path('dist/data')
    data_dir.mkdir()

    copy_pandoc_to_yanom_folder()
    copy_config_file_to_data_folder()


def copy_pandoc_to_yanom_folder():
    Path('dist/pandoc').mkdir()
    shutil.copy2('/usr/local/bin/pandoc', 'dist/pandoc')


def copy_config_file_to_data_folder():
    if not Path('../../src/config.ini').exists():
        print('config.ini missing')
        sys.exit(1)

    print("Copy config.ini")
    shutil.copy('../../src/config.ini', 'dist/data')


def check_signing():
    result1 = subprocess.run('spctl -a -t exec -vv ./dist/yanom', shell=True, capture_output=True)
    print(result1.stderr)

    result2 = subprocess.run('codesign --verify --deep --strict --verbose=2 ./dist/yanom', shell=True,
                             capture_output=True)
    print(result2.stderr)


if __name__ == "__main__":
    main()
