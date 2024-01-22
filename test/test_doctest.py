import doctest


def load_tests(loader, tests, ignore):
    from plugins.addrelease import addrelease
    tests.addTests(doctest.DocTestSuite(addrelease))

    from plugins import decade
    tests.addTests(doctest.DocTestSuite(decade))

    from plugins.smart_title_case import smart_title_case
    tests.addTests(doctest.DocTestSuite(smart_title_case))

    from plugins.standardise_feat import standardise_feat
    tests.addTests(doctest.DocTestSuite(standardise_feat))

    from plugins.key_wheel_converter import key_wheel_converter
    tests.addTests(doctest.DocTestSuite(key_wheel_converter))

    from plugins import enhanced_titles
    tests.addTests(doctest.DocTestSuite(enhanced_titles))
    return tests
