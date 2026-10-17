function twoSumSorted(nums, target) {
  let left = 0;
  let right = nums.length - 1;
  while (left < right) {
    const total = nums[left] + nums[right];
    if (total === target) return [left, right];
    if (total < target) {
      left++;
    } else {
      right--;
    }
  }
  return [];
}

module.exports = { twoSumSorted };
