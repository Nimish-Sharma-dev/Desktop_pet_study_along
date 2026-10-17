BASE = "def search(nums, target):\n    lo = 0\n    hi = len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1\n"

def ren(s, a, b):
    import re
    return re.sub(rf"\b{a}\b", b, s)

# renames only
RENAMES = [BASE, ren(BASE, "lo", "left"), ren(ren(BASE, "lo", "left"), "hi", "right"),
           ren(ren(ren(BASE, "lo", "left"), "hi", "right"), "mid", "m"),
           ren(ren(ren(ren(BASE, "lo", "left"), "hi", "right"), "mid", "m"), "target", "t")]

# independent line shuffles (lo/hi init swapped back and forth) + rename
SHUFFLE_A = BASE.replace("    lo = 0\n    hi = len(nums) - 1\n", "    hi = len(nums) - 1\n    lo = 0\n")
SHUFFLES = [BASE, SHUFFLE_A, BASE, SHUFFLE_A, BASE]

# flip-flopping a real operator
FLIP = BASE.replace("lo <= hi", "lo < hi")
FLIPFLOP = [BASE, FLIP, BASE, FLIP, BASE]

# genuine rewrite: iterative -> different algorithm, typed in stages that each parse
REWRITE = [BASE,
           "def search(nums, target):\n    return -1\n",
           "def search(nums, target):\n    for i in range(len(nums)):\n        pass\n    return -1\n",
           "def search(nums, target):\n    for i in range(len(nums)):\n        if nums[i] == target:\n            return i\n    return -1\n",
           "def search(nums, target):\n    for i, x in enumerate(nums):\n        if x == target:\n            return i\n        if x > target:\n            break\n    return -1\n"]

# real bug-fixing steps, each changes behaviour
REAL_STEPS = [BASE.replace("hi = len(nums) - 1", "hi = len(nums)"), BASE,
              BASE.replace("lo = mid + 1", "lo = mid"), BASE.replace("lo = mid + 1", "lo = mid + 2"),
              BASE.replace("return -1", "return None")]

# dependent reorder: swapping statements that share a variable changes data flow
DEPENDENT = [BASE, BASE.replace("        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n",
                                "        if nums[mid] == target:\n            return mid\n        mid = (lo + hi) // 2\n")]
