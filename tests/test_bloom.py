#-----------------------------------------------------------------------------#
#   test_bloom.py                                                             #
#                                                                             #
#   Copyright (c) 2017, Rajiv Bakulesh Shah, original author.                 #
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
        assert dilberts.num_values == 1000
        assert dilberts.false_positives == 0.001
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

    def test_init_with_iterable(self):
        dilberts = BloomFilter({'rajiv', 'raj'})
        assert dilberts.num_values == 1000
        assert dilberts.false_positives == 0.001
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

    def test_size(self):
        dilberts = BloomFilter(num_values=100, false_positives=0.1)
        assert dilberts.size() == 480

        dilberts = BloomFilter(num_values=100, false_positives=0.01)
        assert dilberts.size() == 960

        dilberts = BloomFilter(num_values=1000, false_positives=0.1)
        assert dilberts.size() == 4800

        dilberts = BloomFilter(num_values=1000, false_positives=0.01)
        assert dilberts.size() == 9592

    def test_num_hashes(self):
        dilberts = BloomFilter(num_values=100, false_positives=0.1)
        assert dilberts.num_hashes() == 3

        dilberts = BloomFilter(num_values=100, false_positives=0.01)
        assert dilberts.num_hashes() == 7

        dilberts = BloomFilter(num_values=1000, false_positives=0.1)
        assert dilberts.num_hashes() == 3

        dilberts = BloomFilter(num_values=1000, false_positives=0.01)
        assert dilberts.num_hashes() == 7

    def test_membership(self):
        dilberts = BloomFilter()
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

        dilberts.add('rajiv')
        assert 'rajiv' in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

        dilberts.add('raj')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

        dilberts.add('rajiv')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

        dilberts.add('raj')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

        dilberts.add('dan')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' not in dilberts

        dilberts.add('eric')
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts

    def test_update(self):
        dilberts = BloomFilter()
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
        assert 'jenny' not in dilberts
        assert 'will' not in dilberts
        assert 'rhodes' not in dilberts

        dilberts.update({'rajiv', 'raj'}, {'dan', 'eric'})
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts
        assert 'jenny' not in dilberts
        assert 'will' not in dilberts
        assert 'rhodes' not in dilberts

        dilberts.update({'jenny', 'will'})
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts
        assert 'jenny' in dilberts
        assert 'will' in dilberts
        assert 'rhodes' not in dilberts

        dilberts.update(set())
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' in dilberts
        assert 'eric' in dilberts
        assert 'jenny' in dilberts
        assert 'will' in dilberts
        assert 'rhodes' not in dilberts

    def test_clear(self):
        dilberts = BloomFilter({'rajiv', 'raj'})
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

        dilberts.clear()
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

    def test_len(self):
        dilberts = BloomFilter()
        assert len(dilberts) == 0

        dilberts.add('rajiv')
        assert len(dilberts) == 1

        dilberts.add('raj')
        assert len(dilberts) == 2

        dilberts.add('rajiv')
        assert len(dilberts) == 2

        dilberts.add('raj')
        assert len(dilberts) == 2

        dilberts.add('dan')
        assert len(dilberts) == 3

        dilberts.add('eric')
        assert len(dilberts) == 4

        dilberts.clear()
        assert len(dilberts) == 0

    def test_repr(self):
        dilberts = BloomFilter(key='dilberts')
        assert repr(dilberts) == '<BloomFilter key=dilberts>'



class RecentlyConsumedTests(unittest.TestCase):
    "Simulate reddit's recently consumed problem to test our Bloom filter."

    def setUp(self):
        super(RecentlyConsumedTests, self).setUp()

        # Construct a set of links that the user has seen.
        self.seen_links = set()
        while len(self.seen_links) < 1000:
            fullname = self.random_fullname()
            self.seen_links.add(fullname)

        # Construct a set of links that the user hasn't seen.  Ensure that
        # there's no intersection between the seen set and the unseen set.
        self.unseen_links = set()
        while len(self.unseen_links) < 1000:
            fullname = self.random_fullname()
            if fullname not in self.seen_links:
                self.unseen_links.add(fullname)

        # Initialize the recently consumed Bloom filter on the seen set.
        self.recently_consumed = BloomFilter(
            num_values=len(self.seen_links),
            false_positives=0.001,
            key='recently-consumed',
        )
        self.recently_consumed.clear()
        self.recently_consumed.update(self.seen_links)

    def tearDown(self):
        self.recently_consumed.clear()

    @staticmethod
    def random_fullname(prefix='t3_', size=6):
        alphabet, id36 = string.digits + string.ascii_lowercase, []
        for _ in xrange(size):
            id36.append(random.choice(alphabet))
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
        'Ensure that we produce zero false negatives.'
        for seen_link in self.seen_links:
            assert seen_link in self.recently_consumed

    def test_acceptable_false_positives(self):
        'Ensure that we produce false positives at an acceptable rate.'
        acceptable, actual = self.recently_consumed.false_positives, 0

        for unseen_link in self.unseen_links:
            actual += unseen_link in self.recently_consumed
        actual /= float(len(self.unseen_links))
        actual = self.round(actual, sig_digits=1)

        message = 'acceptable: {}; actual: {}'.format(acceptable, actual)
        assert actual <= acceptable, message
