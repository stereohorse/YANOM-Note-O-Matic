import contextlib
from pathlib import Path
import shutil


VERSION = '1.6.0'
ZIP_FILENAME = f'yanom-v{VERSION}-osx-10.15.7'


def main():
    remove_zip_file_used_to_notarise()
    create_deployment_zip()
    copy_to_main_dist_folder()
    cleanup()


def remove_zip_file_used_to_notarise():
    print('Clean up - remove zip file used for notarisation')
    if Path(f'yanom-v{VERSION}.zip').exists():
        Path(f'yanom-v{VERSION}.zip').unlink()


def create_deployment_zip():
    print(f'create deployment zip file {ZIP_FILENAME}.zip')
    shutil.make_archive(f'{ZIP_FILENAME}', 'zip', root_dir='dist')


def copy_to_main_dist_folder():
    print('copy distribution zip file to project root dist folder')
    shutil.copy2(f'{ZIP_FILENAME}.zip', '../../dist')


def cleanup():
    print("Clean up - remove deployment zip file form script folder")
    Path(f'{ZIP_FILENAME}.zip').unlink()
    with contextlib.suppress(FileNotFoundError):
        print("Clean up - remove dist and build folders if exist")
        shutil.rmtree('dist')
        shutil.rmtree('build')


if __name__ == "__main__":
    main()
