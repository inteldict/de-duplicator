import os
from datetime import datetime
from typing import AnyStr, Callable, Iterable


class FileCandidate:
    def __init__(self, path):
        self.path = path
        file_stat = os.stat(path)
        self.last_modified = get_last_modification_time(file_stat)
        self.size = file_stat.st_size

    def __repr__(self):
        return f"{self.path} with the size {self.size} modified at {self.last_modified}"

    def size_path_modified(self) -> str:
        return f"{self.size}\t{self.path}\t{datetime.fromtimestamp(self.last_modified)}"


def duplicate_found(file: FileCandidate, do_delete=False) -> int:
    if do_delete:
        print(f"Removing: {file.size_path_modified()}")
        os.remove(file.path)
    else:
        print(f"Duplicate: {file.size_path_modified()}")
    return file.size


def directory_is_empty(path: AnyStr) -> bool:
    """
    :param path: a directory path
    :return: True if directory is empty, False otherwise
    """
    return not any(os.scandir(path))


def derive_filtered_file_iter(filename_filters: [] = None, path_blacklists: [] = None) -> Callable[
    [AnyStr], Iterable[AnyStr]]:
    def _filtered_file_iter(directory_name: AnyStr) -> Iterable[AnyStr]:
        for root, _, files in os.walk(directory_name, topdown=False):
            if any(in_blacklist(root) for in_blacklist in path_blacklists):  # skip the path from blacklist
                continue
            for filename in files:
                if all(filename_filter(filename) for filename_filter in filename_filters):
                    yield os.path.join(root, filename)

    return _filtered_file_iter


def file_iter(directory_name: AnyStr) -> [AnyStr]:
    for root, _, files in os.walk(directory_name, topdown=False):
        for filename in files:
            yield os.path.join(root, filename)


def derive_filtered_empty_directory_iter(path_blacklists: [] = None) -> Callable[[AnyStr], Iterable[AnyStr]]:
    def _filtered_empty_directory_iter(directory_name: AnyStr) -> [AnyStr]:
        for root, dirs, _ in os.walk(directory_name, topdown=False):
            if any(in_blacklist(root) for in_blacklist in path_blacklists):  # skip the path from blacklist
                continue
            for subdir in dirs:
                subdir_path = os.path.join(root, subdir)
                if directory_is_empty(subdir_path):  # directory is empty
                    yield subdir_path

    return _filtered_empty_directory_iter


def empty_directory_iter(directory_name: AnyStr) -> [AnyStr]:
    for root, dirs, _ in os.walk(directory_name, topdown=False):
        for subdir in dirs:
            subdir_path = os.path.join(root, subdir)
            if directory_is_empty(subdir_path):  # directory is empty
                yield subdir_path


def extension_filter_builder(extensions: [AnyStr]) -> Callable[[AnyStr], bool]:
    """

    :param extensions: whitelist of extensions
    :return: Function that checks if filename is in the whitelist
    """

    def _extension_filter(filename: AnyStr) -> bool:
        """
        :param filename: a file name
        :return: True if filename is in the extensions
        """
        _, extension = os.path.splitext(filename)
        if extension and extension.lower() in extensions:
            return True
        return False

    return _extension_filter


def path_blacklist_builder(path_blacklist: [AnyStr]) -> Callable[[AnyStr], bool]:
    """
    :param path_blacklist: blacklist substrings of path
    :return: Function that checks any path in the blacklist
    """

    def _path_in_blacklist(path: AnyStr) -> bool:
        """

        :param path: a file path without filename
        :return: True if path was found in the blacklist
        """
        for black_path in path_blacklist:
            if black_path in path:
                return True
        return False

    return _path_in_blacklist


def get_last_modification_time(file_stat):
    return max(file_stat.st_ctime, file_stat.st_mtime)


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
