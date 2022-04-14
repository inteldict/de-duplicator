import hashlib

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
