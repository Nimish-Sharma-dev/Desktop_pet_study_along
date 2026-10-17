function maxWindowSum(nums, k) {
  if (k <= 0 || k > nums.length) return 0;
  let window = 0;
  for (let i = 0; i < k; i++) window += nums[i];
  let best = window;
  for (let i = k; i < nums.length; i++) {
    window += nums[i] - nums[i - k];
    best = Math.max(best, window);
  }
  return best;
}

module.exports = { maxWindowSum };
