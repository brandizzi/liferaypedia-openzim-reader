import doctest
import unittest

import liferaypedia_openzim_reader.htmlinspector
import liferaypedia_openzim_reader.zimreader


def load_tests(loader, tests, pattern):
    """Load doctests from htmlinspector and zimreader."""
    suite = unittest.TestSuite()
    suite.addTests(doctest.DocTestSuite(liferaypedia_openzim_reader.htmlinspector))
    suite.addTests(doctest.DocTestSuite(liferaypedia_openzim_reader.zimreader))
    return suite
