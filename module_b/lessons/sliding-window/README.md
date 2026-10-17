# Sliding Window

Return the largest sum of `k` consecutive numbers. If `k` is not between 1 and `len(nums)`, return `0`.

```
max_window_sum([2, 1, 5, 1, 3, 2], 3) -> 9      # 5 + 1 + 3
```

A hidden test uses 1,500,000 numbers with a window of 5,000: re-adding every window from scratch is too slow.
