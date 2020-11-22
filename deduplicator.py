import argparse
import hashlib
import os
import sys

BLOCK_SIZE = 4096 * 4096

EPILOG = f'''Example usage: 
// Find and print duplicated images [jpg,png] and empty directories
$ python3 {sys.argv[0]} -d /tmp/test -f jpg,png -e -o -n

// Remove duplicated images [jpg,png] and empty directories
$ python3 {sys.argv[0]} -d /tmp/test -f jpg,png -e -o
'''


def md5(file_name):
    hash_md5 = hashlib.md5()
    with open(file_name, "rb") as f:
        for chunk in iter(lambda: f.read(BLOCK_SIZE), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


class File:
    def __init__(self, path, last_modified):
        self.path = path
        self.last_modified = last_modified

    def __repr__(self):
        return f"{self.path} modified at {self.last_modified}"


def list_files(directory_name, extensions=None):
    for root, subdirs, files in os.walk(directory_name):
        for filename in files:
            if extensions:
                _, file_extension = os.path.splitext(filename)
                if file_extension.lower() in extensions:
                    yield os.path.join(root, filename)
            else:
                yield os.path.join(root, filename)
        # recursively iterate over subdirectories
        # for subdir in subdirs:
        #     yield from list_files(os.path.join(root, subdir), extensions)


def delete_empty_directories(directory_name, remove=False):
    counter = 0
    for root, subdirs, _ in os.walk(directory_name):
        for subdir in subdirs:
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
    hash_dict = {}
    counter = 0
    for file_name in list_files(root_dir, extensions):
        md5_digest = md5(file_name)
        if md5_digest in hash_dict:
            prev_file = hash_dict[md5_digest]
            mod_time = get_last_modification_time(file_name)
            counter += 1
            if keepOldest:
                if prev_file.last_modified <= mod_time:
                    delete_file(file_name, remove)
                else:
                    delete_file(prev_file.path, remove)
                    hash_dict[md5_digest] = File(file_name, mod_time)
            else:
                if prev_file.last_modified >= mod_time:
                    delete_file(file_name, remove)
                else:
                    delete_file(prev_file.path, remove)
                    hash_dict[md5_digest] = File(file_name, mod_time)
        else:
            hash_dict[md5_digest] = File(file_name, get_last_modification_time(file_name))
    if remove:
        print(f"Total duplicates removed: {counter}")
    else:
        print(f"Total duplicates found: {counter}")
    if remove_empty:
        delete_empty_directories(root_dir, remove)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Given a directory find duplicates by a content', epilog=EPILOG)
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
