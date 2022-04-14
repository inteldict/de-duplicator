import argparse
import os
import sys
from typing import AnyStr, Set

from fileutils import directory_is_empty, duplicate_found, extension_filter_builder, \
    path_blacklist_builder, derive_filtered_file_iter, derive_filtered_empty_directory_iter, file_iter, \
    empty_directory_iter, FileCandidate, sizeof_fmt
from hash import derive_hash_func, derive_hash_builder, HASH_FUNC

EPILOG = f'''Example usage:
// The program can use hash function of your choice, see hashlib for details
 
// Find and print duplicated images [jpg,png] and empty directories 
$ python3 {sys.argv[0]} -d /tmp/test -f jpg,png -e -o -n

// Remove duplicated images [jpg,png] and empty directories
$ python3 {sys.argv[0]} -d /tmp/test -f jpg,png -e -o
'''


def delete_empty_directories(empty_directories: [AnyStr], remove: bool = False) -> None:
    counter = 0
    freed_size = 0
    for full_dir_path in empty_directories:
        if directory_is_empty(full_dir_path):
            counter += 1
            freed_size += os.path.getsize(full_dir_path)
            if remove:
                print(f"Removing empty directory: {full_dir_path}")
                os.removedirs(full_dir_path)
            else:
                print(f"Empty directory: {full_dir_path}")
    if remove:
        print(f"Total empty directories removed: {counter}, freed size: {sizeof_fmt(freed_size)}")
    else:
        print(f"Total empty directories found: {counter}, total size: {sizeof_fmt(freed_size)}")


def remove_duplicates(files, keep_oldest=True, remove=False):
    hash_func = derive_hash_func(derive_hash_builder(False), HASH_FUNC)
    hash_dict = {}
    counter = 0
    freed_size = 0
    for file_name in files:
        digest = hash_func(file_name)
        test_file = FileCandidate(file_name)
        if digest in hash_dict:
            prev_file = hash_dict[digest]
            last_modified = test_file.last_modified
            counter += 1
            if keep_oldest:
                if prev_file.last_modified <= last_modified:
                    freed_size += duplicate_found(test_file, remove)
                else:
                    freed_size += duplicate_found(prev_file, remove)
                    hash_dict[digest] = FileCandidate(file_name)
            else:
                if prev_file.last_modified >= last_modified:
                    freed_size += duplicate_found(test_file, remove)
                else:
                    freed_size += duplicate_found(prev_file, remove)
                    hash_dict[digest] = FileCandidate(file_name)
        else:
            hash_dict[digest] = test_file
    if remove:
        print(f"Total duplicates removed: {counter}, freed size: {sizeof_fmt(freed_size)}")
    else:
        print(f"Total duplicates found: {counter}, total duplicates size: {sizeof_fmt(freed_size)}")


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
    parser = argparse.ArgumentParser(description='Given a directory, find duplicate files and empty directories '
                                                 'employing hash comparison (md5, sha1, sha256, etc.)',
                                     epilog=EPILOG)
    parser.add_argument("--directory", "-d",
                        help="Root directory to scan. If not specified, current directory will be used", required=False)
    parser.add_argument("--file-extensions", "-f", help="Comma separated list of file extensions f.e. jpg,png",
                        required=False)
    parser.add_argument("--path-blacklist", "-b", help="Comma separated blacklist f.e. .number,.git",
                        required=False)
    parser.add_argument("--oldest", "-o", help="Keep oldest / newest files", required=False, default=True,
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

    custom_file_iter = file_iter
    custom_dir_iter = empty_directory_iter
    # If specified, build file iterator given extension filters and blacklists
    if filename_filters or path_blacklists:
        custom_file_iter = derive_filtered_file_iter(filename_filters, path_blacklists)
        if path_blacklists:
            custom_dir_iter = derive_filtered_empty_directory_iter(path_blacklists)

    remove_duplicates(custom_file_iter(root_dir), keep_oldest=args.oldest, remove=args.remove)

    if args.empty:  # Analyze or remove empty directories
        delete_empty_directories(custom_dir_iter(root_dir), args.remove)
