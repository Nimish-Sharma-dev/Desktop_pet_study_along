from lessonkit import check


def test_basic():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[2, 7, 11, 15], 9], [0, 1])

def test_middle_pair():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[1, 2, 4, 6, 10], 8], [1, 3])

def test_outer_pair():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[1, 3, 4, 8], 9], [0, 3])

def test_no_pair():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[1, 2, 3], 10], [])
