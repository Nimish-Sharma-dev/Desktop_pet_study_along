from lessonkit import check


def test_found_middle():
    check('binary_search', ['int_list', 'int'], 'int', [[1, 3, 5, 7, 9], 5], 2)

def test_found_first():
    check('binary_search', ['int_list', 'int'], 'int', [[1, 3, 5, 7, 9], 1], 0)

def test_found_last():
    check('binary_search', ['int_list', 'int'], 'int', [[1, 3, 5, 7, 9], 9], 4)

def test_not_found_inside():
    check('binary_search', ['int_list', 'int'], 'int', [[1, 3, 5, 7, 9], 4], -1)

def test_not_found_above():
    check('binary_search', ['int_list', 'int'], 'int', [[1, 3, 5, 7, 9], 10], -1)
