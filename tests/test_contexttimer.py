#-----------------------------------------------------------------------------#
#   test_contexttimer.py                                                      #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


import time
import unittest

from bloom import ContextTimer


class ContextTimerTests(unittest.TestCase):
    ACCURACY = 50.0     # in milliseconds

    def setUp(self):
        super(ContextTimerTests, self).setUp()
        self.timer = ContextTimer()

    def _confirm_elapsed(self, expected):
        got = round(self.timer.elapsed() / self.ACCURACY) * self.ACCURACY
        assert got == expected, '{} != {}'.format(got, expected)

    def test_start_stop_and_elapsed(self):
        # timer hasn't been started
        with self.assertRaises(RuntimeError):
            self.timer.elapsed()
        with self.assertRaises(RuntimeError):
            self.timer.stop()

        # timer has been started but not stopped
        self.timer.start()
        with self.assertRaises(RuntimeError):
            self.timer.start()
        time.sleep(0.1)
        self._confirm_elapsed(1*100)
        self.timer.stop()

        # timer has been stopped
        with self.assertRaises(RuntimeError):
            self.timer.start()
        time.sleep(0.1)
        self._confirm_elapsed(1*100)
        with self.assertRaises(RuntimeError):
            self.timer.stop()

    def test_context_manager(self):
        with self.timer:
            self._confirm_elapsed(0)
            for iteration in range(1, 3):
                time.sleep(0.1)
                self._confirm_elapsed(iteration*100)
            self._confirm_elapsed(iteration*100)
        time.sleep(0.1)
        self._confirm_elapsed(iteration*100)

        with self.assertRaises(RuntimeError), self.timer:
            pass
