#-----------------------------------------------------------------------------#
#   test_memlock.py                                                           #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


import time
import unittest

from bloom import ContextTimer, MemLock, ReleaseUnlockedLock


class MemLockTests(unittest.TestCase):
    def setUp(self):
        super(MemLockTests, self).setUp()
        self.memlock = MemLock(key='printer')
        self._release()

    def tearDown(self):
        self._release()
        super(MemLockTests, self).tearDown()

    def _release(self):
        try:
            self.memlock.release()
        except ReleaseUnlockedLock:
            pass

    def test_acquire_and_time_out(self):
        assert not self.memlock.locked()
        assert self.memlock.acquire()
        assert self.memlock.locked()
        time.sleep(self.memlock.auto_release_time)
        assert not self.memlock.locked()

    def test_acquire_same_lock_twice_blocking_without_timeout(self):
        with ContextTimer() as timer:
            assert not self.memlock.locked()
            assert self.memlock.acquire()
            assert self.memlock.locked()
            assert self.memlock.acquire()
            assert self.memlock.locked()
            assert timer.elapsed() > self.memlock.auto_release_time

    def test_acquire_same_lock_twice_blocking_with_timeout(self):
        assert not self.memlock.locked()
        assert self.memlock.acquire()
        assert self.memlock.locked()
        assert not self.memlock.acquire(timeout=0)
        assert self.memlock.locked()

    def test_acquire_same_lock_twice_non_blocking_without_timeout(self):
        assert not self.memlock.locked()
        assert self.memlock.acquire()
        assert self.memlock.locked()
        assert not self.memlock.acquire(blocking=False)
        assert self.memlock.locked()
        time.sleep(self.memlock.auto_release_time)
        assert not self.memlock.locked()

    def test_acquire_same_lock_twice_non_blocking_with_timeout(self):
        assert not self.memlock.locked()
        assert self.memlock.acquire()
        assert self.memlock.locked()
        with self.assertRaises(ValueError):
            self.memlock.acquire(blocking=False, timeout=0)
        assert self.memlock.locked()

    def test_acquire_then_release(self):
        assert not self.memlock.locked()
        assert self.memlock.acquire()
        assert self.memlock.locked()
        self.memlock.release()
        assert not self.memlock.locked()

    def test_release_unlocked_lock(self):
        assert not self.memlock.locked()
        with self.assertRaises(ReleaseUnlockedLock):
            self.memlock.release()

    def test_releaseunlockedlock_repr(self):
        assert not self.memlock.locked()
        try:
            self.memlock.release()
        except ReleaseUnlockedLock as err:
            assert repr(err) == (
                '<ReleaseUnlockedLock key=printer retriable=False>'
            )

    def test_release_same_lock_twice(self):
        assert not self.memlock.locked()
        assert self.memlock.acquire()
        assert self.memlock.locked()
        self.memlock.release()
        assert not self.memlock.locked()
        with self.assertRaises(ReleaseUnlockedLock):
            self.memlock.release()
        assert not self.memlock.locked()

    def test_context_manager(self):
        assert not self.memlock.locked()
        with self.memlock:
            assert self.memlock.locked()
        assert not self.memlock.locked()

    def test_context_manager_time_out_before_exit(self):
        assert not self.memlock.locked()
        with self.assertRaises(ReleaseUnlockedLock), self.memlock:
            assert self.memlock.locked()
            time.sleep(self.memlock.auto_release_time)
            assert not self.memlock.locked()
        assert not self.memlock.locked()

    def test_context_manager_release_before_exit(self):
        assert not self.memlock.locked()
        with self.assertRaises(ReleaseUnlockedLock), self.memlock:
            assert self.memlock.locked()
            self.memlock.release()
            assert not self.memlock.locked()
        assert not self.memlock.locked()

    def test_repr(self):
        assert repr(self.memlock) == '<MemLock key=printer locked=False>'
