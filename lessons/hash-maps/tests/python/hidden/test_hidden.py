from lessonkit import check


def test_hidden_sum_empty():
    check('two_sum', ['int_list', 'int'], 'int_list', [[], 4], [])

def test_hidden_sum_no_self_reuse():
    check('two_sum', ['int_list', 'int'], 'int_list', [[5], 10], [])

def test_hidden_sum_negatives():
    check('two_sum', ['int_list', 'int'], 'int_list', [[-3, 4, 3, 90], 0], [0, 2])

def test_hidden_sum_large():
    check('two_sum', ['int_list', 'int'], 'int_list', [{'gen': 'range', 'args': [0, 300000, 1]}, 599997], [299998, 299999])

def test_hidden_anagram_empty():
    check('is_anagram', ['string', 'string'], 'bool', ['', ''], True)

def test_hidden_anagram_length_differs():
    check('is_anagram', ['string', 'string'], 'bool', ['a', 'ab'], False)

def test_hidden_anagram_same_letters_different_counts():
    check('is_anagram', ['string', 'string'], 'bool', ['aacc', 'ccac'], False)
