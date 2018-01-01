#-----------------------------------------------------------------------------#
#   test_bloom.py                                                             #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#



import math
import random
import string
import unittest

from bloom import BloomFilter



class BloomFilterTests(unittest.TestCase):
    def test_init(self):
        dilberts = BloomFilter()
        assert dilberts.key.startswith(BloomFilter._RANDOM_KEY_PREFIX)
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 0

    def test_init_with_iterable(self):
        dilberts = BloomFilter({'rajiv', 'raj'})
        assert dilberts.key.startswith(BloomFilter._RANDOM_KEY_PREFIX)
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 2

    def test_size_and_num_hashes(self):
        dilberts = BloomFilter(num_values=100, false_positives=0.1)
        assert dilberts.size() == 480
        assert dilberts.num_hashes() == 3

        dilberts = BloomFilter(num_values=100, false_positives=0.01)
        assert dilberts.size() == 960
        assert dilberts.num_hashes() == 7

        dilberts = BloomFilter(num_values=1000, false_positives=0.1)
        assert dilberts.size() == 4800
        assert dilberts.num_hashes() == 3

        dilberts = BloomFilter(num_values=1000, false_positives=0.01)
        assert dilberts.size() == 9592
        assert dilberts.num_hashes() == 7

    def test_add(self):
        dilberts = BloomFilter()
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 0

        dilberts.add('rajiv')
        assert 'rajiv' in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 1

        dilberts.add('raj')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 2

        dilberts.add('rajiv')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 2

        dilberts.add('raj')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 2

        dilberts.add('dan')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 3

        dilberts.add('eric')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts
        assert len(dilberts) == 4

    def test_update(self):
        dilberts = BloomFilter()
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert 'jenny' not in dilberts
        assert 'will' not in dilberts
        assert 'rhodes' not in dilberts
        assert len(dilberts) == 0

        dilberts.update({'rajiv', 'raj'}, {'dan', 'eric'})
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts
        assert 'jenny' not in dilberts
        assert 'will' not in dilberts
        assert 'rhodes' not in dilberts
        assert len(dilberts) == 4

        dilberts.update({'eric', 'jenny', 'will'})
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts
        assert 'jenny' in dilberts
        assert 'will' in dilberts
        assert 'rhodes' not in dilberts
        assert len(dilberts) == 6

        dilberts.update(set())
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts
        assert 'jenny' in dilberts
        assert 'will' in dilberts
        assert 'rhodes' not in dilberts
        assert len(dilberts) == 6

    def test_clear(self):
        dilberts = BloomFilter({'rajiv', 'raj'})
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 2

        dilberts.clear()
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert len(dilberts) == 0

    def test_repr(self):
        dilberts = BloomFilter(key='dilberts')
        assert repr(dilberts) == '<BloomFilter key=dilberts>'



class RecentlyConsumedTests(unittest.TestCase):
    "Simulate reddit's recently consumed problem to test our Bloom filter."

    def setUp(self):
        super(self.__class__, self).setUp()

        # Construct a set of links that the user has seen.
        self.seen_links = set()
        while len(self.seen_links) < 100:
            fullname = self.random_fullname()
            self.seen_links.add(fullname)

        # Construct a set of links that the user hasn't seen.  Ensure that
        # there's no intersection between the seen set and the unseen set.
        self.unseen_links = set()
        while len(self.unseen_links) < 100:
            fullname = self.random_fullname()
            if fullname not in self.seen_links:
                self.unseen_links.add(fullname)

        # Initialize the recently consumed Bloom filter on the seen set.
        self.recently_consumed = BloomFilter(
            num_values=1000,
            false_positives=0.001,
            key='recently-consumed',
        )
        self.recently_consumed.clear()
        self.recently_consumed.update(self.seen_links)

    def tearDown(self):
        self.recently_consumed.memcache.delete(self.recently_consumed.key)
        super(self.__class__, self).tearDown()

    @staticmethod
    def random_fullname(prefix='t3_', size=6):
        alphabet36, id36 = string.digits + string.ascii_lowercase, []
        for _ in xrange(size):
            id36.append(random.choice(alphabet36))
        return prefix + ''.join(id36)

    @staticmethod
    def round(number, sig_digits=1):
        '''Round a float to the specified number of significant digits.

        Reference implementation:
            https://github.com/ActiveState/code/blob/3b27230f418b714bc9a0f897cb8ea189c3515e99/recipes/Python/578114_Round_number_specified_number_significant/recipe-578114.py
        '''
        try:
            ndigits = sig_digits - 1 - int(math.floor(math.log10(abs(number))))
        except ValueError:
            # math.log10(number) raised a ValueError, so number must be 0.0.
            # No need to round 0.0.
            return number
        else:
            return round(number, ndigits)

    def test_zero_false_negatives(self):
        'Ensure that we produce zero false negatives'
        for seen_link in self.seen_links:
            assert seen_link in self.recently_consumed

    def test_acceptable_false_positives(self):
        'Ensure that we produce false positives at an acceptable rate'
        acceptable, actual = self.recently_consumed.false_positives, 0

        for unseen_link in self.unseen_links:
            actual += unseen_link in self.recently_consumed
        actual /= float(len(self.unseen_links))
        actual = self.round(actual, sig_digits=1)

        message = 'acceptable: {}; actual: {}'.format(acceptable, actual)
        assert actual <= acceptable, message



class StoreBitArrayTests(unittest.TestCase):
    'Whenever we change a BloomFilter, ensure that we Memcache our changes.'

    def setUp(self):
        super(self.__class__, self).setUp()
        self.dilberts = BloomFilter({'rajiv', 'raj'}, key='dilberts')

    def tearDown(self):
        self.dilberts.memcache.delete(self.dilberts.key)
        super(self.__class__, self).tearDown()

    def test_init_gets_stored(self):
        'When we __init__() on an iterable, ensure we Memcache the bit array'
        office_space = BloomFilter(key='dilberts')
        assert office_space._bit_array == self.dilberts._bit_array

    def test_add_gets_stored(self):
        'When we add() an element, ensure that we Memcache the bit array'
        self.dilberts.add('dan')
        office_space = BloomFilter(key='dilberts')
        assert office_space._bit_array == self.dilberts._bit_array

    def test_update_gets_stored(self):
        'When we update() with elements, ensure that we Memcache the bit array'
        self.dilberts.update({'dan', 'eric'})
        office_space = BloomFilter(key='dilberts')
        assert office_space._bit_array == self.dilberts._bit_array

    def test_clear_gets_stored(self):
        'When we clear() all elements, ensure that we Memcache the bit array'
        self.dilberts.clear()
        office_space = BloomFilter(key='dilberts')
        assert office_space._bit_array == self.dilberts._bit_array



class CheckAndSetTests(unittest.TestCase):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.thread1 = BloomFilter(key='dilberts')
        self.thread1.clear()
        self.thread2 = BloomFilter(key='dilberts')

    def tearDown(self):
        self.thread1.memcache.delete(self.thread1.key)
        super(self.__class__, self).tearDown()

    def test_check_and_set(self):
        "Ensure that multiple threads don't stomp each other's changes"

        # Let's simulate instantiating BloomFilters in two threads, both
        # pointed at the same Memcache key.  I've named these BloomFilters
        # self.thread1 and self.thread2 for clarity's sake.

        # When we update the BloomFilter in thread 1, ...
        self.thread1.update({'rajiv', 'raj'})

        # ... notice that the BloomFilter in thread 2 doesn't automatically get
        # updated:
        assert 'rajiv' not in self.thread2
        assert 'raj' not in self.thread2

        # But now when we update the BloomFilter in thread 2, ...
        self.thread2.update({'dan', 'eric'})

        # ... notice that this BloomFilter in thread 2 first pulls in thread
        # 1's changes, then applies its own:
        assert 'rajiv' in self.thread2
        assert 'raj' in self.thread2
        assert 'dan' in self.thread2
        assert 'eric' in self.thread2

        # So even though our local BloomFilter objects might get out of sync,
        # ...
        assert 'dan' not in self.thread1
        assert 'eric' not in self.thread1

        # ... whenever we update them, we first merge in changes from Memcache,
        # which is always in sync:
        self.thread1.update({'jenny', 'will'})
        assert 'dan' in self.thread1
        assert 'eric' in self.thread1
