const { check } = require('./lessonkit');

test("five_nodes", () => {
  check("reverseList", ["linked_list"], "linked_list", [[1, 2, 3, 4, 5]], [5, 4, 3, 2, 1]);
});

test("two_nodes", () => {
  check("reverseList", ["linked_list"], "linked_list", [[1, 2]], [2, 1]);
});

