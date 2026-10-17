from lessonkit import check


def test_hidden_empty():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[], 5], [])

def test_hidden_single_cannot_pair_with_itself():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[5], 10], [])

def test_hidden_duplicates():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[1, 1, 3, 5], 2], [0, 1])

def test_hidden_negatives():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [[-4, -1, 0, 3, 10], -5], [0, 1])

def test_hidden_large():
    check('two_sum_sorted', ['int_list', 'int'], 'int_list', [{'gen': 'range', 'args': [0, 300000, 2]}, 1199994], [299998, 299999])
