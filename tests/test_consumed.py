#-----------------------------------------------------------------------------#
#   test_consumed.py                                                          #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


import unittest

from bloom import RecentlyConsumed


class RecentlyConsumedTests(unittest.TestCase):
    def setUp(self):
        super(RecentlyConsumedTests, self).setUp()

        # Wait for each Memcache command to complete before moving on to the
        # next line of code.  This makes our tests run deterministically.
        RecentlyConsumed._NOREPLY = False

        self.consumed = RecentlyConsumed(key='consumed:rajiv', maxlen=10)

    def tearDown(self):
        self.consumed.clear()
        RecentlyConsumed._NOREPLY = True
        super(RecentlyConsumedTests, self).tearDown()

    def test_maxlen_is_not_writable(self):
        with self.assertRaises(AttributeError):
            self.consumed.maxlen = 100

    def test_memcached_list_does_not_exceed_maxlen(self):
        self.consumed.extend(('t3_1', 't3_2', 't3_3', 't3_4', 't3_5', 't3_6'))
        with self.assertRaises(IndexError):
            RecentlyConsumed(key='consumed:rajiv', maxlen=5)

    def test_typical_usage(self):
        assert len(self.consumed) == 0
        assert 't3_1' not in self.consumed
        assert 't3_2' not in self.consumed
        assert 't3_3' not in self.consumed
        assert 't3_4' not in self.consumed
        assert 't3_5' not in self.consumed

        self.consumed.append('t3_1')
        assert len(self.consumed) == 1
        assert 't3_1' in self.consumed
        assert 't3_2' not in self.consumed
        assert 't3_3' not in self.consumed
        assert 't3_4' not in self.consumed
        assert 't3_5' not in self.consumed

        self.consumed.extend(('t3_1', 't3_2', 't3_3'))
        assert len(self.consumed) == 3
        assert 't3_1' in self.consumed
        assert 't3_2' in self.consumed
        assert 't3_3' in self.consumed
        assert 't3_4' not in self.consumed
        assert 't3_5' not in self.consumed

        self.consumed.append('t3_3')
        assert len(self.consumed) == 3
        assert 't3_1' in self.consumed
        assert 't3_2' in self.consumed
        assert 't3_3' in self.consumed
        assert 't3_4' not in self.consumed
        assert 't3_5' not in self.consumed

        self.consumed.append('t3_4')
        assert len(self.consumed) == 4
        assert 't3_1' in self.consumed
        assert 't3_2' in self.consumed
        assert 't3_3' in self.consumed
        assert 't3_4' in self.consumed
        assert 't3_5' not in self.consumed

        self.consumed.extend(('t3_3', 't3_4'))
        assert len(self.consumed) == 4
        assert 't3_1' in self.consumed
        assert 't3_2' in self.consumed
        assert 't3_3' in self.consumed
        assert 't3_4' in self.consumed
        assert 't3_5' not in self.consumed

    def test_pruning_to_maxlen(self):
        self.consumed.extend(('t3_1', 't3_2', 't3_3', 't3_4', 't3_5'))
        self.consumed.extend(('t3_6', 't3_7', 't3_8', 't3_9', 't3_10'))
        assert len(self.consumed) == 10
        assert 't3_1' in self.consumed
        assert 't3_2' in self.consumed
        assert 't3_3' in self.consumed
        assert 't3_4' in self.consumed
        assert 't3_5' in self.consumed
        assert 't3_6' in self.consumed
        assert 't3_7' in self.consumed
        assert 't3_8' in self.consumed
        assert 't3_9' in self.consumed
        assert 't3_10' in self.consumed
        assert 't3_11' not in self.consumed
        assert 't3_12' not in self.consumed
        assert 't3_13' not in self.consumed
        assert 't3_14' not in self.consumed
        assert 't3_15' not in self.consumed

        self.consumed.append('t3_11')
        assert len(self.consumed) == 10
        assert 't3_1' not in self.consumed
        assert 't3_2' in self.consumed
        assert 't3_3' in self.consumed
        assert 't3_4' in self.consumed
        assert 't3_5' in self.consumed
        assert 't3_6' in self.consumed
        assert 't3_7' in self.consumed
        assert 't3_8' in self.consumed
        assert 't3_9' in self.consumed
        assert 't3_10' in self.consumed
        assert 't3_11' in self.consumed
        assert 't3_12' not in self.consumed
        assert 't3_13' not in self.consumed
        assert 't3_14' not in self.consumed
        assert 't3_15' not in self.consumed

        self.consumed.extend(('t3_12', 't3_13', 't3_14', 't3_15'))
        assert len(self.consumed) == 10
        assert 't3_1' not in self.consumed
        assert 't3_2' not in self.consumed
        assert 't3_3' not in self.consumed
        assert 't3_4' not in self.consumed
        assert 't3_5' not in self.consumed
        assert 't3_6' in self.consumed
        assert 't3_7' in self.consumed
        assert 't3_8' in self.consumed
        assert 't3_9' in self.consumed
        assert 't3_10' in self.consumed
        assert 't3_11' in self.consumed
        assert 't3_12' in self.consumed
        assert 't3_13' in self.consumed
        assert 't3_14' in self.consumed
        assert 't3_15' in self.consumed

    def test_clear(self):
        self.consumed.extend(('t3_1', 't3_2', 't3_3'))
        self.consumed.clear()
        assert len(self.consumed) == 0
        assert 't3_1' not in self.consumed
        assert 't3_2' not in self.consumed
        assert 't3_3' not in self.consumed
        assert repr(self.consumed) == (
            "RecentlyConsumed([], key=consumed:rajiv, maxlen=10)"
        )

    def test_repr(self):
        assert repr(self.consumed) == (
            "RecentlyConsumed([], key=consumed:rajiv, maxlen=10)"
        )

    def test_repr_when_maxlen_is_none(self):
        consumed2 = RecentlyConsumed(key='consumed:rajiv', maxlen=None)
        assert repr(consumed2) == "RecentlyConsumed([], key=consumed:rajiv)"

    def test_persistence(self):
        'Ensure that RecentlyConsumed gets persisted in Memcache'
        self.consumed.extend(('t3_1', 't3_2', 't3_3'))
        consumed2 = RecentlyConsumed(key='consumed:rajiv', maxlen=10)
        assert repr(consumed2) == (
            "RecentlyConsumed([u't3_1', u't3_2', u't3_3'], "
            "key=consumed:rajiv, maxlen=10)"
        )
