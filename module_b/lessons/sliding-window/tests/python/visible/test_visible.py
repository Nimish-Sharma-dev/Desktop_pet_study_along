from lessonkit import check


def test_basic():
    check('max_window_sum', ['int_list', 'int'], 'long', [[1, 4, 2, 10, 2, 3, 1, 0, 20], 4], 24)

def test_small_window():
    check('max_window_sum', ['int_list', 'int'], 'long', [[2, 1, 5, 1, 3, 2], 3], 9)

def test_one_element():
    check('max_window_sum', ['int_list', 'int'], 'long', [[5], 1], 5)

def test_all_negative():
    check('max_window_sum', ['int_list', 'int'], 'long', [[-3, -1, -2], 2], -3)
