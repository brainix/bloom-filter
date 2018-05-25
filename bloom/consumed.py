#-----------------------------------------------------------------------------#
#   consumed.py                                                               #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


import collections
import json

from .base import Base, run_doctests


class RecentlyConsumed(Base):
    '''Memcache-backed data structure to track recently consumed links.

    On the consumer side, we want a data structure similar to a
    collections.deque (as we're appending a user's new consumed links to the
    right and popping old consumed links from the left).  But on the listing
    service side, we want a data structure similar to a set (as we're testing
    many candidate links for membership within the user's RecentlyConsumed).

    Therefore, RecentlyConsumed (persisted in Memcache) implements a subset of
    the collections.deque API and a subset of the set API.  As such, please
    note that RecentlyConsumed silently ignores duplicate values during
    append() and extend().

    Further, please note that RecentlyConsumed is neither thread-safe nor safe
    to use across instances.  Please lock around your RecentlyConsumed
    instances/accesses.  A good choice for such a lock is .memlock.MemLock.
    '''

    _RANDOM_KEY_PREFIX = 'tmp:consumed:'
    _MAXLEN = 1000

    # If _NOREPLY is False, then we wait for each Memcache command to complete
    # before moving on to the next line of code.  _NOREPLY should be False when
    # running our unit tests (to make our tests run deterministically), but
    # True on production (so that our code runs faster).
    _NOREPLY = True

    def __init__(self, memcache=None, key=None, maxlen=_MAXLEN):
        super(RecentlyConsumed, self).__init__(memcache=memcache, key=key)
        self._maxlen = maxlen
        self._load_from_memcache()

    @property
    def maxlen(self):
        return self._maxlen

    @maxlen.setter
    def maxlen(self, value):
        message = "attribute 'maxlen' of '{}' objects is not writable"
        message = message.format(self.__class__.__name__)
        raise AttributeError(message)

    def _load_from_memcache(self):
        string = self.memcache.get(self.key, default='[]')
        list_ = json.loads(string)
        if self.maxlen is not None and len(list_) > self.maxlen:
            message = 'persistent {} beyond its maximum size'
            message = message.format(self.__class__.__name__)
            raise IndexError(message)
        self._deque = collections.deque(list_)
        self._set = set(list_)

    def _store_to_memcache(self):
        if self._set:
            list_ = list(self._deque)
            string = json.dumps(list_)
            self.memcache.set(self.key, string, noreply=self._NOREPLY)
        else:
            self.memcache.delete(self.key, noreply=self._NOREPLY)

    def _prune_to_maxlen(self):
        while self.maxlen is not None and len(self) > self.maxlen:
            value = self._deque.popleft()
            self._set.remove(value)

    def __len__(self):
        'Return the number of items in the RecentlyConsumed.'
        return len(self._set)

    def __contains__(self, value):
        'rc.__contains__(element) <==> element in rc.'
        return unicode(value) in self._set

    def append(self, value):
        'Add an element to the right side of the RecentlyConsumed.'
        value = unicode(value)
        if value not in self:
            self._deque.append(value)
            self._set.add(value)
            self._prune_to_maxlen()
            self._store_to_memcache()

    def extend(self, values):
        'Extend a RecentlyConsumed by appending elements from the iterable.'
        values = tuple(unicode(value) for value in values if value not in self)
        if values:
            self._deque.extend(values)
            self._set.update(values)
            self._prune_to_maxlen()
            self._store_to_memcache()

    def clear(self):
        'Remove all elements from the RecentlyConsumed.'
        self._deque.clear()
        self._set.clear()
        self._store_to_memcache()

    def __repr__(self):
        'Return the string representation of the RecentlyConsumed data struct.'
        repr = self.__class__.__name__ + '('
        repr += str(list(self._deque))
        repr += ', key={}'.format(self.key)
        if self.maxlen is not None:
            repr += ', ' + 'maxlen={}'.format(self.maxlen)
        repr += ')'
        return repr


if __name__ == '__main__':  # pragma: no cover
    # Run the doctests in this module with:
    #   $ source venv/bin/activate
    #   $ python -m bloom.consumed
    #   $ deactivate
    run_doctests()
