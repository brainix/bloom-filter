#-----------------------------------------------------------------------------#
#   exceptions.py                                                             #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


class BloomFilterException(Exception):
    def __init__(self, memcache=None, key=None, retriable=False):
        super(BloomFilterException, self).__init__()
        self.memcache = memcache
        self.key = key
        self.retriable = retriable

    def __repr__(self):     # pragma: no cover
        return '<{} key={} retriable={}>'.format(
            self.__class__.__name__,
            self.key,
            self.retriable,
        )


class CheckAndSetError(BloomFilterException):
    def __init__(self, memcache=None, key=None):
        super(CheckAndSetError, self).__init__(
            memcache=memcache,
            key=key,
            retriable=True,
        )


class ReleaseUnlockedLock(BloomFilterException):
    def __init__(self, memcache=None, key=None):
        super(ReleaseUnlockedLock, self).__init__(
            memcache=memcache,
            key=key,
            retriable=False,
        )
