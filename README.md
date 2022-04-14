# De-Duplicator
Flexible tool for removing duplicate files by employing hash comparison (md5, sha1, sha256, etc.) and empty directories from computer

## Example usage:

### Find and print duplicated images [jpg, png] and empty directories 
```
$ python3 deduplicator.py -d /tmp/test -f jpg,png -e -o -n
```

### Find and print duplicated images [jpg, png] and empty directories IGNORING directories from blacklist [.numbers, .git] 
```
$ python3 deduplicator.py -d /home/mheimer/Documents -f jpg,jpeg,png -b .numbers,.git -e -o
```

### Remove duplicated images [jpg, png] and empty directories 
```
$ python3 deduplicator.py -d /tmp/test -f jpg,png -e -o -r
```

### Optional arguments
```
  -h, --help            Show this help message and exit
  --directory DIRECTORY, -d DIRECTORY
                        Root directory to scan. If not specified, current directory will be used
  --file-extensions FILE_EXTENSIONS, -f FILE_EXTENSIONS
                        Comma separated list of file extensions f.e. jpg,png
  --path-blacklist PATH_BLACKLIST, -b PATH_BLACKLIST
                        Comma separated blacklist f.e. .number,.git
  --oldest, -o          Keep oldest / newest files
  --remove, -r          Use this option to perform changes on the filesystem
  --empty, -e           Remove empty directories

```

