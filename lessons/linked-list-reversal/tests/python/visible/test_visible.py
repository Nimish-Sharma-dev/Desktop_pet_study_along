from lessonkit import check


def test_five_nodes():
    check('reverse_list', ['linked_list'], 'linked_list', [[1, 2, 3, 4, 5]], [5, 4, 3, 2, 1])

def test_two_nodes():
    check('reverse_list', ['linked_list'], 'linked_list', [[1, 2]], [2, 1])
