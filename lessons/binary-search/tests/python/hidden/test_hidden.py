from lessonkit import check


def test_hidden_empty():
    check('binary_search', ['int_list', 'int'], 'int', [[], 3], -1)

def test_hidden_single_found():
    check('binary_search', ['int_list', 'int'], 'int', [[4], 4], 0)

def test_hidden_single_missing():
    check('binary_search', ['int_list', 'int'], 'int', [[4], 7], -1)

def test_hidden_two_elements():
    check('binary_search', ['int_list', 'int'], 'int', [[1, 3], 3], 1)

def test_hidden_below_min():
    check('binary_search', ['int_list', 'int'], 'int', [[5, 6, 7], 1], -1)

def test_hidden_large():
    check('binary_search', ['int_list', 'int'], 'int', [{'gen': 'range', 'args': [0, 1000000, 1]}, 999999], 999999)
