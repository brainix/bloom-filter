#-----------------------------------------------------------------------------#
#   bloom.py                                                                  #
#                                                                             #
#   Copyright (c) 2017, Rajiv Bakulesh Shah, original author.                 #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#



import collections
import functools
import json
import math
import random
import string

import mmh3
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

    def _bit_offsets(self, value):
        '''The bit offsets to set/check in this Bloom filter for a given value.

        Instantiate a Bloom filter:

            >>> dilberts = BloomFilter(
            ...     num_values=100,
            ...     false_positives=0.01,
            ...     key='dilberts',
            ... )

        Now let's look at a few examples:

            >>> tuple(dilberts._bit_offsets('rajiv'))
            (183L, 319L, 787L, 585L, 8L, 471L, 711L)
            >>> tuple(dilberts._bit_offsets('raj'))
            (482L, 875L, 725L, 667L, 109L, 714L, 595L)
            >>> tuple(dilberts._bit_offsets('dan'))
            (687L, 925L, 954L, 707L, 615L, 914L, 620L)

        Thus, if we want to insert the value 'rajiv' into our Bloom filter,
        then we must set bits 183, 319, 787, 585, 8, 471, and 711 all to 1.  If
        any/all of them are already 1, no problems.

        Similarly, if we want to check to see if the value 'rajiv' is in our
        Bloom filter, then we must check to see if the bits 183, 319, 787, 585,
        8, 471, and 711 are all set to 1.  If even one of those bits is set to
        0, then the value 'rajiv' must never have been inserted into our Bloom
        filter.  But if all of those bits are set to 1, then the value 'rajiv'
        was *probably* inserted into our Bloom filter.
        '''
        encoded_value = json.dumps(value, sort_keys=True)
        for seed in range(self.num_hashes()):
            yield mmh3.hash(encoded_value, seed=seed) % self.size()



def main():                 # pragma: no cover
    # Run the doctests in this module with:
    #   $ source venv/bin/activate
    #   $ python -m bloom
    #   $ deactivate
    import doctest
    import sys
    results = doctest.testmod()
    sys.exit(bool(results.failed))

if __name__ == '__main__':  # pragma: no cover
    main()
