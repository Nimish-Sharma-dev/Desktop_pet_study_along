from lessonkit import check


def test_hidden_window_is_whole_list():
    check('max_window_sum', ['int_list', 'int'], 'long', [[1, 2, 3], 3], 6)

def test_hidden_window_too_big():
    check('max_window_sum', ['int_list', 'int'], 'long', [[1, 2], 5], 0)

def test_hidden_empty():
    check('max_window_sum', ['int_list', 'int'], 'long', [[], 3], 0)

def test_hidden_zero_window():
    check('max_window_sum', ['int_list', 'int'], 'long', [[1, 2, 3], 0], 0)

def test_hidden_large():
    check('max_window_sum', ['int_list', 'int'], 'long', [{'gen': 'range', 'args': [0, 1500000, 1]}, 5000], 7487497500)
