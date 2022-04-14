import argparse
import hashlib
import os
import sys
from typing import AnyStr, Callable, Set

EPILOG = f'''Example usage:
// The program can use hash function of your choice, see hashlib for details
 
// Find and print duplicated images [jpg,png] and empty directories 
$ python3 {sys.argv[0]} -d /tmp/test -f jpg,png -e -o -n

// Remove duplicated images [jpg,png] and empty directories
$ python3 {sys.argv[0]} -d /tmp/test -f jpg,png -e -o
'''

BLOCK_SIZE = 4096 * 4096
# Setup hasher
# HASH_FUNC = hashlib.md5
HASH_FUNC = hashlib.sha1


def block_iter(file_to_read, block_size=BLOCK_SIZE):
    with file_to_read:
        block = file_to_read.read(block_size)
        while len(block) > 0:
            yield block
            block = file_to_read.read(block_size)


def hash_builder(batch_bytes, hasher):
    for block in batch_bytes:
        hasher.update(block)
    return hasher


def derive_hash_builder(hex_str=False):
    def _hex_digest(bytes_batch, hasher):
        return hash_builder(bytes_batch, hasher).hexdigest()

    def _digest(bytes_batch, hasher):
        return hash_builder(bytes_batch, hasher).digest()

    return _hex_digest if hex_str else _digest


def derive_hash_func(hash_factory, hash_func):
    def _hash(file_name):
        return hash_factory(block_iter(open(file_name, 'rb')), hash_func())

    return _hash


class File:
    def __init__(self, path, last_modified):
        self.path = path
        self.last_modified = last_modified

    def __repr__(self):
        return f"{self.path} modified at {self.last_modified}"


def directory_is_empty(path: AnyStr) -> bool:
    """
    :param path: a directory path
    :return: True if directory is empty, False otherwise
    """
    return not any(os.scandir(path))


def derive_filtered_file_iter(filename_filters: [] = None, path_blacklists: [] = None) -> Callable[[AnyStr], bool]:
    def _filtered_file_iter(directory_name: AnyStr) -> [AnyStr]:
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


def derive_filtered_empty_directory_iter(path_blacklists: [] = None) -> Callable[[AnyStr], bool]:
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


def delete_empty_directories(empty_directories, remove=False):
    counter = 0
    for full_dir_path in empty_directories:
        if directory_is_empty(full_dir_path):  # directory is empty
            counter += 1
            if remove:
                print(f"Removing empty directory: {full_dir_path}")
                os.removedirs(full_dir_path)
            else:
                print(f"Empty directory: {full_dir_path}")
    if remove:
        print(f"Total empty directories removed: {counter}")
    else:
        print(f"Total empty directories found: {counter}")


def delete_file(filename, remove=False):
    if remove:
        print(f"Removing: {filename}")
        os.remove(filename)
    else:
        print(f"Duplicate: {filename}")


def get_last_modification_time(filename):
    stat = os.stat(filename)
    return max(stat.st_ctime, stat.st_mtime)


def remove_duplicates(files, keep_oldest=True, remove=False):
    hash_func = derive_hash_func(derive_hash_builder(False), HASH_FUNC)
    hash_dict = {}
    counter = 0
    for file_name in files:
        digest = hash_func(file_name)
        if digest in hash_dict:
            prev_file = hash_dict[digest]
            mod_time = get_last_modification_time(file_name)
            counter += 1
            if keep_oldest:
                if prev_file.last_modified <= mod_time:
                    delete_file(file_name, remove)
                else:
                    delete_file(prev_file.path, remove)
                    hash_dict[digest] = File(file_name, mod_time)
            else:
                if prev_file.last_modified >= mod_time:
                    delete_file(file_name, remove)
                else:
                    delete_file(prev_file.path, remove)
                    hash_dict[digest] = File(file_name, mod_time)
        else:
            hash_dict[digest] = File(file_name, get_last_modification_time(file_name))
    if remove:
        print(f"Total duplicates removed: {counter}")
    else:
        print(f"Total duplicates found: {counter}")


def get_parent_directory(parent_dir: AnyStr) -> AnyStr:
    if parent_dir:
        parent_dir = os.path.abspath(parent_dir)
        assert os.path.isdir(parent_dir), f"Specified directory: {parent_dir} was not found!"
    else:
        parent_dir = os.path.dirname(os.path.realpath(__file__))
    return parent_dir


def process_comma_separated_values(raw_str: AnyStr) -> [AnyStr]:
    result = []
    if raw_str:
        if ',' in raw_str:
            result.extend((e.strip()) for e in raw_str.split(','))
        else:
            result.append(raw_str.strip())
    return result


def build_extensions(raw_extensions: AnyStr) -> Set[AnyStr]:
    extensions_set = set()
    if raw_extensions:
        if ',' in raw_extensions:
            extensions_set.update(('.' + e.strip()) for e in raw_extensions.split(','))
        else:
            extensions_set.add('.' + raw_extensions)
    return extensions_set


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Given a directory find duplicate files using a hash sum (md5)',
                                     epilog=EPILOG)
    parser.add_argument("--directory", "-d",
                        help="Root directory to scan. If not specified, current directory will be used", required=False)
    parser.add_argument("--file-extensions", "-f", help="comma separated list of file extensions f.e. jpg,png",
                        required=False)
    parser.add_argument("--path-blacklist", "-b", help="comma separated blacklist f.e. .number,.git",
                        required=False)
    parser.add_argument("--oldest", "-o", help="keep oldest / newest files", required=False, default=True,
                        action='store_true')
    parser.add_argument("--remove", "-r", help="Use this option to perform changes on the filesystem", required=False,
                        default=False, action='store_false')
    parser.add_argument("--empty", "-e", help="Remove empty directories", required=False,
                        default=False, action='store_true')

    args = parser.parse_args()

    # Get starting directory for duplicate analysis
    root_dir = get_parent_directory(args.directory)
    print(f'Searching for duplicates in: {root_dir}')

    filename_filters = []
    if args.file_extensions:  # Filter filenames by extension
        file_extensions = build_extensions(args.file_extensions)
        print(f'Filter files with following extensions: {sorted(file_extensions)}')
        filename_filters.append(extension_filter_builder(file_extensions))

    path_blacklists = []
    if args.path_blacklist:  # Path blacklist
        blacklist = process_comma_separated_values(args.path_blacklist)
        path_blacklists.append(path_blacklist_builder(blacklist))

    # Build file iterator given extension filters and blacklists
    if filename_filters or path_blacklists:
        custom_file_iter = derive_filtered_file_iter(filename_filters, path_blacklists)
        if path_blacklists:
            custom_dir_iter = derive_filtered_empty_directory_iter(path_blacklists)
    else:
        custom_file_iter = file_iter
        custom_dir_iter = empty_directory_iter

    remove_duplicates(custom_file_iter(root_dir), keep_oldest=args.oldest, remove=args.remove)

    if args.empty:  # Analyze or remove empty directories
        delete_empty_directories(custom_dir_iter(root_dir), args.remove)
