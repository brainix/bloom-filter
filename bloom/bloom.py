#-----------------------------------------------------------------------------#
#   bloom.py                                                                  #
#                                                                             #
#   Copyright (c) 2017, Rajiv Bakulesh Shah, original author.                 #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#



import collections
import functools
import itertools
import json
import math
import random
import string

import mmh3
from bitarray import bitarray
from pymemcache.client.base import Client

from .exceptions import CheckAndSetError



MemcacheServer = collections.namedtuple('MemcacheServer', ('hostname', 'port'))



class BloomFilter(object):
    '''Memcache-backed Bloom filter with an API similar to Python sets.

    Bloom filters are a powerful data structure that help you to answer the
    question, "Have I seen this element before?" but not the question, "What
    are all of the elements that I've seen before?"  So think of Bloom filters
    as Python sets that you can add elements to and use to test element
    membership, but that you can't iterate through or get elements back out of.

    Bloom filters are probabilistic, which means that they can sometimes
    generate false positives (as in, they may report that you've seen a
    particular element before even though you haven't).  But they will never
    generate false negatives (so every time that they report that you haven't
    seen a particular element before, you really must never have seen it).  You
    can tune your acceptable false positive probability, though at the expense
    of the storage size and the element insertion/lookup time of your Bloom
    filter.

    Wikipedia article:
        https://en.wikipedia.org/wiki/Bloom_filter

    Reference implementation:
        http://www.maxburstein.com/blog/creating-a-simple-bloom-filter/

    Instantiate a Bloom filter and clean up Memcache before the doctest:

        >>> dilberts = BloomFilter(
        ...     num_values=1000,
        ...     false_positives=0.001,
        ...     key='dilberts',
        ... )
        >>> dilberts.clear()

    Here, num_values represents the number of elements that you expect to
    insert into your BloomFilter, and false_positives represents your
    acceptable false positive probability.  Using these two parameters,
    BloomFilter automatically computes its own storage size and number of times
    to run its hash functions on element insertion/lookup such that it can
    guarantee a false positive rate at or below what you can tolerate, given
    that you're going to insert your specified number of elements.

    Insert an element into the Bloom filter:

        >>> dilberts.add('rajiv')

    This Bloom filter implementation supports elements of any type that can be
    dumped as JSON.

    Test for membership in the Bloom filter:

        >>> 'rajiv' in dilberts
        True
        >>> 'raj' in dilberts
        False
        >>> 'dan' in dilberts
        False

    See how many elements you've inserted into the Bloom filter:

        >>> len(dilberts)
        1

    Note that BloomFilter.__len__() is an approximation, so please don't rely
    on it for anything important like financial systems or cat gif websites.

    Insert multiple elements into the Bloom filter:

        >>> dilberts.update({'raj', 'dan'})

    I recommend using BloomFilter.update() to insert multiple elements into the
    Bloom filter (over repeated BloomFilter.add() calls) as
    BloomFilter.update() inserts all of the elements and then stores the Bloom
    filter to Memcache once (rather than inserting one element, storing the
    Bloom filter to Memcache, inserting another element, storing the Bloom
    filter to Memcache again, etc.).

    Remove all of the elements from the Bloom filter:

        >>> dilberts.clear()
    '''

    _DEFAULT_MEMCACHE_SERVER = MemcacheServer(hostname='localhost', port=11211)
    _RANDOM_KEY_PREFIX = 'bloom:'
    _RANDOM_KEY_CHARS = ''.join((string.digits, string.ascii_lowercase))
    _RANDOM_KEY_LENGTH = 16

    def __init__(self, iterable=frozenset(), memcache=None, key=None,
                 num_values=1000, false_positives=0.001):
        self.memcache = memcache or Client(
            self._DEFAULT_MEMCACHE_SERVER,
            connect_timeout=1,
            timeout=1,
        )
        self.key = key or self._random_key()
        self.num_values = num_values
        self.false_positives = false_positives
        self._load_bit_array()
        self.update(iterable)

    def __del__(self):  # pragma: no cover
        if self.key.startswith(self._RANDOM_KEY_PREFIX):
            self.clear()

    @classmethod
    def _random_key(cls):
        random_char = functools.partial(random.choice, cls._RANDOM_KEY_CHARS)
        suffix = ''.join(random_char() for _ in xrange(cls._RANDOM_KEY_LENGTH))
        random_key = ''.join((cls._RANDOM_KEY_PREFIX, suffix))
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
            self._size = self._size + (8 - self._size % 8) % 8
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
            (17L, 271L, 669L, 242L, 166L, 4L, 536L)
            >>> tuple(dilberts._bit_offsets('raj'))
            (521L, 491L, 440L, 871L, 938L, 682L, 455L)
            >>> tuple(dilberts._bit_offsets('dan'))
            (61L, 854L, 730L, 730L, 475L, 364L, 850L)

        Thus, if we want to insert the value 'rajiv' into our Bloom filter,
        then we must set bits 17, 271, 669, 242, 166, 4, and 536 all to 1.  If
        any/all of them are already 1, no problems.

        Similarly, if we want to check to see if the value 'rajiv' is in our
        Bloom filter, then we must check to see if the bits 17, 271, 669, 242,
        166, 4, and 536 are all set to 1.  If even one of those bits is set to
        0, then the value 'rajiv' must never have been inserted into our Bloom
        filter.  But if all of those bits are set to 1, then the value 'rajiv'
        was *probably* inserted into our Bloom filter.
        '''
        encoded_value = json.dumps(value, sort_keys=True)
        for seed in range(self.num_hashes()):
            yield mmh3.hash(encoded_value, seed=seed) % self.size()

    def _load_bit_array(self):
        bit_string, self._cas = self.memcache.gets(self.key)
        if bit_string is None:
            self._bit_array = bitarray('0' * self.size())
            self._store_bit_array()
        else:
            self._bit_array = bitarray()
            self._bit_array.frombytes(bit_string)

    def _store_bit_array(self):
        bit_string = self._bit_array.tobytes()
        if self._cas is None:
            self.memcache.set(self.key, bit_string)
        else:
            if not self.memcache.cas(self.key, bit_string, self._cas):
                raise CheckAndSetError(memcache=self.memcache, key=self.key)
        self._load_bit_array()

    def _retry_check_and_set(num_tries=3):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                for try_num in xrange(num_tries):   # pragma: no cover
                    try:
                        return func(self, *args, **kwargs)
                    except CheckAndSetError:
                        if try_num < num_tries - 1:
                            self._load_bit_array()
                        else:
                            raise
            return wrapper
        return decorator

    def add(self, value):
        '''Add an element to a BloomFilter.  O(k)

        Here, k is the number of times to run our hash functions on a given
        input string to compute bit offests into the underlying string
        representing this Bloom filter.

        Your element can be of any type that can be dumped as JSON.
        '''
        self.update({value})

    @_retry_check_and_set()
    def update(self, *iterables):
        '''Populate a Bloom filter with the elements in iterables.  O(n * k)

        Here, n is the number of elements in iterables that you want to insert
        into this Bloom filter, and k is the number of times to run our hash
        functions on each element.

        Your elements can be of any type that can be dumped as JSON.
        '''
        bit_offsets = set()
        for value in itertools.chain(*iterables):
            bit_offsets.update(self._bit_offsets(value))
        for bit_offset in bit_offsets:
            self._bit_array[bit_offset] = 1
        self._store_bit_array()

    def __contains__(self, value):
        '''bf.__contains__(element) <==> element in bf.  O(k)

        Here, k is the number of times to run our hash functions on a given
        input string to compute bit offests into the underlying string
        representing this Bloom filter.

        Your element can be of any type that can be dumped as JSON.
        '''
        bit_offsets = set(self._bit_offsets(value))
        return all(self._bit_array[bit_offset] for bit_offset in bit_offsets)

    @_retry_check_and_set()
    def clear(self):
        '''Remove all elements from this Bloom filter.  O(m)

        Here, m is the size in bits of the underlying string representing this
        Bloom filter.
        '''
        self._bit_array.setall(0)
        self._store_bit_array()

    def __len__(self):
        '''Return the approximate the number of elements in a BloomFilter.  O(m)

        Here, m is the size in bits of the underlying string representing this
        Bloom filter.

        Please note that this method returns an approximation, not an exact
        value.  So please don't rely on it for anything important like
        financial systems or cat gif websites.

        More about the formula that this method implements:
            https://en.wikipedia.org/wiki/Bloom_filter#Approximating_the_number_of_items_in_a_Bloom_filter
        '''
        num_bits_set = self._bit_array.count()
        len_ = -float(self.size()) / self.num_hashes() * math.log(1 - float(num_bits_set) / self.size())
        return int(math.floor(len_))

    def __repr__(self):
        'Return the string representation of a BloomFilter.  O(1)'
        return '<{} key={}>'.format(self.__class__.__name__, self.key)



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
