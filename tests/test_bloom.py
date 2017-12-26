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
