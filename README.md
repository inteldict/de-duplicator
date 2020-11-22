# De-Duplicator
## Flexible tool for removing duplicate files (using md5 hash) and empty directories from computer

Given a directory find duplicate files using a hash sum (md5)

## Example usage:

# Find and print duplicated images [jpg,png] and empty directories 

$ python3 deduplicator.py -d /tmp/test -f jpg,png -e -o -n

# Remove duplicated images [jpg,png] and empty directories 

$ python3 deduplicator.py -d /tmp/test -f jpg,png -e -o

