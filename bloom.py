#-----------------------------------------------------------------------------#
#   bloom.py                                                                  #
#                                                                             #
#   Copyright (c) 2017, Rajiv Bakulesh Shah, original author.                 #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#



import collections
import functools
import math
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
        self.memcache = memcache or Client(
            self._DEFAULT_MEMCACHE_SERVER,
            connect_timeout=1,
            timeout=1,
        )
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

    def size(self):
        '''The required number of bits (m) given n and p.

        This method returns the required number of bits (m) for the underlying
        string representing this Bloom filter given the the number of elements
        that you expect to insert (n) and your acceptable false positive
        probability (p).

        More about the formula that this method implements:
            https://en.wikipedia.org/wiki/Bloom_filter#Optimal_number_of_hash_functions
        '''
        try:
            return self._size
        except AttributeError:
            self._size = -self.num_values * math.log(self.false_positives) / math.log(2)**2
            self._size = int(math.ceil(self._size))
            return self.size()

    def num_hashes(self):
        '''The number of hash functions (k) given m and n, minimizing p.

        This method returns the number of times (k) to run our hash functions
        on a given input string to compute bit offsets into the underlying
        string representing this Bloom filter.  m is the size in bits of the
        underlying string, n is the number of elements that you expect to
        insert, and p is your acceptable false positive probability.

        More about the formula that this method implements:
            https://en.wikipedia.org/wiki/Bloom_filter#Optimal_number_of_hash_functions
        '''
        try:
            return self._num_hashes
        except AttributeError:
            self._num_hashes = self.size() / self.num_values * math.log(2)
            self._num_hashes = int(math.ceil(self._num_hashes))
            return self.num_hashes()
