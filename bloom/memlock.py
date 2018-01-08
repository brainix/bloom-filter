#-----------------------------------------------------------------------------#
#   memlock.py                                                                #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


import random
import time

from .base import Base, run_doctests
from .contexttimer import ContextTimer
from .exceptions import ReleaseUnlockedLock


class MemLock(Base):
    '''Memcache-backed lock with an API similar to Python's threading.Lock.

    This algorithm safely and reliably provides a mutually-exclusive locking
    primitive to protect a resource shared across threads, processes, and even
    machines.

    Usage:

        >>> printer_lock = MemLock(key='printer')
        >>> printer_lock.locked()
        False
        >>> printer_lock.acquire()
        True
        >>> printer_lock.locked()
        True
        >>> # Critical section - print stuff here.
        >>> printer_lock.release()
        >>> printer_lock.locked()
        False

    MemLocks time out (by default, after 1 second).  You should take care to
    ensure that your critical section completes well within the timeout.  The
    reasons that MemLocks time out are to preserve "liveness" and to avoid
    deadlocks (in the event that a process dies inside a critical section
    before it releases its lock).

        >>> printer_lock.acquire()
        True
        >>> printer_lock.locked()
        True
        >>> # Critical section - print stuff here.
        >>> time.sleep(1)
        >>> printer_lock.locked()
        False

    You can use a MemLock as a context manager:

        >>> states = []
        >>> with MemLock(key='printer') as printer_lock:
        ...     states.append(printer_lock.locked())
        ...     # Critical section - print stuff here.
        >>> states.append(printer_lock.locked())
        >>> states
        [True, False]
    '''

    _RANDOM_KEY_PREFIX = 'tmp:memlock:'
    _AUTO_RELEASE_TIME = 1
    _RETRY_DELAY = 0.2

    def __init__(self, memcache=None, key=None,
                 auto_release_time=_AUTO_RELEASE_TIME):
        super(MemLock, self).__init__(memcache=memcache, key=key)
        self.auto_release_time = auto_release_time

        # Set self._value to a random string, unique to this MemLock instance.
        # Later when we acquire this lock, in Memcache, we'll set self.key to
        # self._value.
        #
        # We need for self._value to be unique for each MemLock instance
        # because two machines may instantiate MemLocks on the same Memcache
        # key, and self._value is the only way that we can know which machine
        # holds the lock.
        self._value = self._random_key()

    def _memcache_add(self):
        return self.memcache.add(
            self.key,
            self._value,
            expire=self.auto_release_time,
            noreply=False,
        )

    def acquire(self, blocking=True, timeout=-1):
        'Lock the lock.'
        if blocking:
            with ContextTimer() as timer:
                while timeout == -1 or timer.elapsed() / 1000 < timeout:
                    if self._memcache_add():
                        return True
                    else:
                        time.sleep(random.uniform(0, self._RETRY_DELAY))
            return False
        elif timeout == -1:
            return self._memcache_add()
        else:
            raise ValueError("can't specify a timeout for a non-blocking call")

    def locked(self):
        'Whether the lock is locked.'
        return bool(self.memcache.get(self.key))

    def release(self):
        'Unlock the lock.'
        if not self.memcache.delete(self.key, noreply=False):
            raise ReleaseUnlockedLock(memcache=self.memcache, key=self.key)

    def __enter__(self):
        'Using a MemLock as a context manager, enter the critical section.'
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        'Using a MemLock as a context manager, exit the critical section.'
        self.release()

    def __repr__(self):
        return '<{} key={} locked={}>'.format(
            self.__class__.__name__,
            self.key,
            self.locked(),
        )


if __name__ == '__main__':  # pragma: no cover
    # Run the doctests in this module with:
    #   $ source venv/bin/activate
    #   $ python -m bloom.memlock
    #   $ deactivate
    run_doctests()
