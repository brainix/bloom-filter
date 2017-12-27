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
        bloom_filter = BloomFilter()
        assert bloom_filter.key.startswith(BloomFilter._RANDOM_KEY_PREFIX)
        assert bloom_filter.num_values == 100
        assert bloom_filter.false_positives == 0.01

    def test_size(self):
        bloom_filter = BloomFilter(num_values=100, false_positives=0.1)
        assert bloom_filter.size() == 480

        bloom_filter = BloomFilter(num_values=100, false_positives=0.01)
        assert bloom_filter.size() == 960

        bloom_filter = BloomFilter(num_values=1000, false_positives=0.1)
        assert bloom_filter.size() == 4800

        bloom_filter = BloomFilter(num_values=1000, false_positives=0.01)
        assert bloom_filter.size() == 9592

    def test_num_hashes(self):
        bloom_filter = BloomFilter(num_values=100, false_positives=0.1)
        assert bloom_filter.num_hashes() == 3

        bloom_filter = BloomFilter(num_values=100, false_positives=0.01)
        assert bloom_filter.num_hashes() == 7

        bloom_filter = BloomFilter(num_values=1000, false_positives=0.1)
        assert bloom_filter.num_hashes() == 3

        bloom_filter = BloomFilter(num_values=1000, false_positives=0.01)
        assert bloom_filter.num_hashes() == 7
