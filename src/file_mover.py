from pathlib import Path


def create_target_absolute_file_path(file_path, source_absolute_root, target_path_root, target_suffix):
    """
    Create an absolute path to a file.

    Create an absolute path to a file replacing the source_absolute_root part of the path with the target_path_root path
    if file_path is on the source_absolute_root path and replace the extension with target_suffix.

    If file_path is not on source_absolute_root return file_path with the target_suffix


    Parameters
    ----------
    file_path : str or Path
        Path to a file
    source_absolute_root : str or Path
        a path that may be the start of file_path
    target_path_root : str or Path
        A path that will become the start of the path to the returned target path
    target_suffix : str
        The suffix to use on the returned target path

    Returns
    -------
    Path
        The new absolute path to the file that was on file_path

    """

    if Path(file_path).is_relative_to(source_absolute_root):
        target_relative_path_to_source_root = Path(file_path).relative_to(source_absolute_root)
        # target_relative_path_to_source_root is the relative path that will be added onto the export folder path
        return Path(target_path_root, target_relative_path_to_source_root).with_suffix(target_suffix)

    if not Path(file_path).is_absolute():
        # path is relative add target path_root and new suffix
        return Path(target_path_root, file_path).with_suffix(target_suffix)

    # file is not in the source path return the file path with the new suffix
    return Path(file_path).with_suffix(target_suffix)


def get_file_suffix_for(export_format: str) -> str:
    if export_format == 'html':
        return '.html'
    return '.md'
