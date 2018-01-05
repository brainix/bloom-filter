#-----------------------------------------------------------------------------#
#   test_doctests.py                                                          #
#                                                                             #
#   Copyright (c) 2017-2018, Rajiv Bakulesh Shah, original author.            #
#   All rights reserved.                                                      #
#-----------------------------------------------------------------------------#


import doctest
import importlib
import os
import unittest


class DoctestTests(unittest.TestCase):
    def _modules(self):
        test_dir = os.path.dirname(__file__)
        package_dir = os.path.dirname(test_dir)
        source_dir = os.path.join(package_dir, 'bloom')
        source_files = (f for f in os.listdir(source_dir) if f.endswith('.py'))
        for source_file in source_files:
            module_name = os.path.splitext(source_file)[0]
            module = importlib.import_module('bloom.{}'.format(module_name))
            yield module

    def test_doctests(self):
        for module in self._modules():
            results = doctest.testmod(m=module)
            assert not results.failed
