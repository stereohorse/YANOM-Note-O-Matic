from pathlib import Path


def create_target_file_path(file_path, source_absolute_root, target_path_root, target_suffix):
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

    if source_absolute_root == target_path_root:
        # files are being created in the source folders export path == source path
        return Path(file_path).with_suffix(target_suffix)

    if Path(file_path).is_relative_to(source_absolute_root):
        target_relative_path_to_source_root = Path(file_path).relative_to(source_absolute_root)
        # target_relative_path_to_source_root is the relative path that will be added onto the export folder path
        return Path(target_path_root, target_relative_path_to_source_root).with_suffix(target_suffix)

    # file is not in the source path return the file path with the new extension
    return Path(file_path).with_suffix(target_suffix)

#
# def create_relative_path_to_source_root(source_absolute_root, file_path):
#     source_absolute_root = Path(source_absolute_root)
#     file_path = Path(file_path)
#     if source_absolute_root in file_path.parents or source_absolute_root == file_path:
#         return file_path.relative_to(source_absolute_root)
#
#     return

#
# def create_absolute_target_path(target_path_root, source_relative_path):
#     return Path(target_path_root, source_relative_path)
