# Bloom Filter

Prototype of how we can use a Bloom filter for
[@reddit](https://github.com/reddit)&rsquo;s recently consumed feature.  This
package provides a Memcache-backed Bloom filter with an API similar to Python
sets.

[![Build Status](https://travis-ci.org/brainix/bloom-filter.svg?branch=master)](https://travis-ci.org/brainix/bloom-filter)

## Description

Bloom filters are a powerful data structure that help you to answer the
question, *&ldquo;Have I seen this element before?&rdquo;* but not the
question, *&ldquo;What are all of the elements that I've seen before?&rdquo;*
So think of Bloom filters as Python sets that you can add elements to and use
to test element membership, but that you can&rsquo;t iterate through or get
elements back out of.

Bloom filters are probabilistic, which means that they can sometimes generate
false positives (as in, they may report that you&rsquo;ve seen a particular
element before even though you haven&rsquo;t).  But they will never generate
false negatives (so every time that they report that you haven&rsquo;t seen a
particular element before, you really must never have seen it).  You can tune
your acceptable false positive probability, though at the expense of the
storage size and the element insertion/lookup time of your Bloom filter.

* [Wikipedia Article](https://en.wikipedia.org/wiki/Bloom_filter)
* [Reference Implementation](http://www.maxburstein.com/blog/creating-a-simple-bloom-filter/)
* [Medium Post](https://blog.medium.com/what-are-bloom-filters-1ec2a50c68ff)

## Usage

Instantiate a `BloomFilter`:

    >>> from bloom import BloomFilter
    >>> dilberts = BloomFilter(
    ...     num_values=1000,
    ...     false_positives=0.001,
    ...     key='dilberts',
    ... )

Here, `num_values` represents the number of elements that you expect to insert
into your `BloomFilter`, and `false_positives` represents your acceptable false
positive probability.  Using these two parameters, `BloomFilter` automatically
computes its own storage size and number of times to run its hash functions on
element insertion/lookup such that it can guarantee a false positive rate at or
below what you can tolerate, given that you&rsquo;re going to insert your
specified number of elements.

Insert an element into the `BloomFilter`:

    >>> dilberts.add('rajiv')

This `BloomFilter` implementation supports elements of any type that can be
dumped as JSON.

Test for membership in the `BloomFilter`:

    >>> 'rajiv' in dilberts
    True
    >>> 'raj' in dilberts
    False
    >>> 'dan' in dilberts
    False

See how many elements you&rsquo;ve inserted into the `BloomFilter`:

    >>> len(dilberts)
    1

Note that `BloomFilter.__len__()` is an approximation, so please don&rsquo;t
rely on it for anything important like financial systems or cat gif websites.

Insert multiple elements into the `BloomFilter`:

    >>> dilberts.update({'raj', 'dan'})

I recommend using `BloomFilter.update()` to insert multiple elements into the
`BloomFilter` (over repeated `BloomFilter.add()` calls) as
`BloomFilter.update()` inserts all of the elements and then stores the
`BloomFilter` to Memcache once (rather than inserting one element, storing the
`BloomFilter` to Memcache, inserting another element, storing the `BloomFilter`
to Memcache again, etc.).

Remove all of the elements from the `BloomFilter`:

    >>> dilberts.clear()
