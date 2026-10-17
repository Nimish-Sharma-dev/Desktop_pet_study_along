def two_sum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        j = seen.get(target - x)
        if j is not None:
            return [j, i]
        seen[x] = i
    return []


def is_anagram(s, t):
    if len(s) != len(t):
        return False
    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    for ch in t:
        if counts.get(ch, 0) == 0:
            return False
        counts[ch] -= 1
    return True
