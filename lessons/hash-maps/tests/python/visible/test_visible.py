from lessonkit import check


def test_sum_basic():
    check('two_sum', ['int_list', 'int'], 'int_list', [[2, 7, 11, 15], 9], [0, 1])

def test_sum_not_first():
    check('two_sum', ['int_list', 'int'], 'int_list', [[3, 2, 4], 6], [1, 2])

def test_sum_duplicates():
    check('two_sum', ['int_list', 'int'], 'int_list', [[3, 3], 6], [0, 1])

def test_sum_none():
    check('two_sum', ['int_list', 'int'], 'int_list', [[1, 2, 3], 7], [])

def test_anagram_yes():
    check('is_anagram', ['string', 'string'], 'bool', ['listen', 'silent'], True)

def test_anagram_no():
    check('is_anagram', ['string', 'string'], 'bool', ['rat', 'car'], False)
