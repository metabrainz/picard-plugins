import doctest


def load_tests(loader, tests, ignore):
    from plugins.addrelease import addrelease
    tests.addTests(doctest.DocTestSuite(addrelease))
    from plugins import decade
    tests.addTests(doctest.DocTestSuite(decade))
    from plugins.standardise_feat import standardise_feat
    tests.addTests(doctest.DocTestSuite(standardise_feat))
    from plugins.key_wheel_converter import key_wheel_converter
    tests.addTests(doctest.DocTestSuite(key_wheel_converter))
    return tests
