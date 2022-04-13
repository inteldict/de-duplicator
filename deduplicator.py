import argparse
import hashlib
import os
import sys

INTRO = f'''Example usage:
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
    def _hexdigest(bytes_batch, hasher):
        return hash_builder(bytes_batch, hasher).hexdigest()

    def _digest(bytes_batch, hasher):
        return hash_builder(bytes_batch, hasher).digest()

    return _hexdigest if hex_str else _digest


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


def list_files(directory_name, extensions=None):
    for root, dirs, files in os.walk(directory_name, topdown=False):
        for filename in files:
            if extensions:
                _, file_extension = os.path.splitext(filename)
                if file_extension.lower() in extensions:
                    yield os.path.join(root, filename)
            else:
                yield os.path.join(root, filename)
        # recursively iterate over subdirectories
        # for dir in dirs:
        #     yield from list_files(os.path.join(root, subdir), extensions)


def delete_empty_directories(directory_name, remove=False):
    counter = 0
    for root, dirs, _ in os.walk(directory_name, topdown=False):
        for subdir in dirs:
            subdir_path = os.path.join(root, subdir)
            if os.path.isdir(subdir_path) and not os.listdir(subdir_path):  # directory is empty
                counter += 1
                if remove:
                    print(f"Removing empty directory: {subdir_path}")
                    os.removedirs(subdir_path)
                else:
                    print(f"Empty directory found: {subdir_path}")
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


def remove_duplicates(root_dir, extensions=None, keepOldest=True, remove=False, remove_empty=False):
    hash_func = derive_hash_func(derive_hash_builder(False), HASH_FUNC)
    hash_dict = {}
    counter = 0
    for file_name in list_files(root_dir, extensions):
        digest = hash_func(file_name)
        if digest in hash_dict:
            prev_file = hash_dict[digest]
            mod_time = get_last_modification_time(file_name)
            counter += 1
            if keepOldest:
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
    if remove_empty:
        delete_empty_directories(root_dir, remove)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Given a directory find duplicate files using a hash sum (md5)',
                                     epilog=INTRO)
    parser.add_argument("--directory", "-d", help="Root directory to scan", required=False)
    parser.add_argument("--file-extensions", "-f", help="comma separated list of file extensions f.e. jpg,png",
                        required=False)
    parser.add_argument("--oldest", "-o", help="keep oldest / newest files", required=False, default=True,
                        action='store_true')
    parser.add_argument("--no-action", "-n", help="Just list of duplicate files to remove", required=False,
                        default=True, action='store_false')
    parser.add_argument("--empty", "-e", help="Remove empty directories", required=False,
                        default=False, action='store_true')

    args = parser.parse_args()
    # try:
    #     args = parser.parse_args()
    # except:
    #     parser.print_help()
    #     sys.exit(0)

    root_dir = args.directory
    if root_dir:
        root_dir = os.path.abspath(root_dir)
        assert os.path.isdir(root_dir), f"Specified directory: {root_dir} was not found!"
    else:
        root_dir = os.path.dirname(os.path.realpath(__file__))
    print(f'Searching for duplicates in: {root_dir}')

    extensions = args.file_extensions
    if extensions:
        if ',' in extensions:
            extensions = set('.' + e for e in extensions.split(','))
        else:
            extensions = set(('.' + extensions,))
        print(f'Filter files with following extensions: {sorted(extensions)}')
    to_remove = args.no_action
    remove_duplicates(root_dir, extensions, args.oldest, to_remove, remove_empty=args.empty)

# if args.input:
#     if args.input.endswith('.gz'):
#         input = gzip.open(args.input, 'rb')
#     else:
#         input = open(args.input, encoding=ENCODING)
# else:
#     input = sys.stdin
#
# # if args.output:
# #     output = open(args.output, mode='w')
# # else:
# #     output = sys.stdout
#
# sentence_ids = read_nodes(args.nodes)
# replace_tags(input, args.output, sentence_ids)
