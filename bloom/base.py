#-----------------------------------------------------------------------------#
#   base.py                                                                   #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


import collections
import doctest
import functools
import random
import string
import sys

from pymemcache.client.base import Client


MemcacheServer = collections.namedtuple('MemcacheServer', ('hostname', 'port'))


class Base(object):
    _DEFAULT_MEMCACHE_SERVER = MemcacheServer(hostname='localhost', port=11211)
    _RANDOM_KEY_PREFIX = 'base:'
    _RANDOM_KEY_CHARS = ''.join((string.digits, string.ascii_lowercase))
    _RANDOM_KEY_LENGTH = 16

    def __init__(self, memcache=None, key=None):
        self.memcache = memcache or Client(
            self._DEFAULT_MEMCACHE_SERVER,
            connect_timeout=1,
            timeout=1,
        )
        self.key = key or self._random_key()

    def __del__(self):  # pragma: no cover
        if self.key.startswith(self._RANDOM_KEY_PREFIX):
            self.memcache.delete(self.key)

    @classmethod
    def _random_key(cls):
        random_char = functools.partial(random.choice, cls._RANDOM_KEY_CHARS)
        suffix = ''.join(random_char() for _ in xrange(cls._RANDOM_KEY_LENGTH))
        random_key = ''.join((cls._RANDOM_KEY_PREFIX, suffix))
        return random_key

    def __repr__(self):
        'Return the string representation of an instance of our subclass.'
        return '<{} key={}>'.format(self.__class__.__name__, self.key)


def run_doctests():         # pragma: no cover
    results = doctest.testmod()
    sys.exit(bool(results.failed))

if __name__ == '__main__':  # pragma: no cover
    # Run the doctests in this module with:
    #   $ source venv/bin/activate
    #   $ python -m bloom.base
    #   $ deactivate
    run_doctests()
