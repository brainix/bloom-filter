#-----------------------------------------------------------------------------#
#   test_bloom.py                                                             #
#                                                                             #
#   Copyright (c) 2017, Rajiv Bakulesh Shah, original author.                 #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#



import unittest

from bloom import BloomFilter



class BloomFilterTests(unittest.TestCase):
    def test_init(self):
        dilberts = BloomFilter()
        assert dilberts.key.startswith(BloomFilter._RANDOM_KEY_PREFIX)
        assert dilberts.num_values == 100
        assert dilberts.false_positives == 0.01
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

    def test_init_with_iterable(self):
        dilberts = BloomFilter(
            {'rajiv', 'raj'},
            num_values=100,
            false_positives=0.01,
        )
        assert dilberts.num_values == 100
        assert dilberts.false_positives == 0.01
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
        dilberts = BloomFilter(num_values=100, false_positives=0.01)
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
        dilberts = BloomFilter(num_values=100, false_positives=0.01)
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
        dilberts = BloomFilter(
            {'rajiv', 'raj'},
            num_values=100,
            false_positives=0.01,
        )
        assert 'rajiv' in dilberts
        assert 'raj' in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts

        dilberts.clear()
        assert 'rajiv' not in dilberts
        assert 'raj' not in dilberts
        assert 'dan' not in dilberts
        assert 'eric' not in dilberts
