#-----------------------------------------------------------------------------#
#   bloom.py                                                                  #
#                                                                             #
#   Copyright (c) 2017, Rajiv Bakulesh Shah, original author.                 #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#



import collections
import functools
import random
import string

from pymemcache.client.base import Client



MemcacheServer = collections.namedtuple('MemcacheServer', ('hostname', 'port'))



class BloomFilter(object):
    _DEFAULT_MEMCACHE_SERVER = MemcacheServer(hostname='localhost', port=11211)
    _RANDOM_KEY_PREFIX = 'bloom:'
    _RANDOM_KEY_LENGTH = 16

    def __init__(self, iterable=frozenset(), memcache=None, key=None,
                 num_values=100, false_positives=0.01):
        self.memcache = memcache or Client(self._DEFAULT_MEMCACHE_SERVER)
        self.key = key or self._random_key()
        self.num_values = num_values
        self.false_positives = false_positives
        # TODO: self.update(iterable)

    def __del__(self):  # pragma: no cover
        if self.key.startswith(self._RANDOM_KEY_PREFIX):
            self.memcache.delete(self.key)

    def _random_key(self):
        all_chars = ''.join((string.digits, string.ascii_lowercase))
        random_char = functools.partial(random.choice, all_chars)
        suffix = ''.join(random_char() for _ in xrange(self._RANDOM_KEY_LENGTH))
        random_key = ''.join((self._RANDOM_KEY_PREFIX, suffix))
        return random_key
