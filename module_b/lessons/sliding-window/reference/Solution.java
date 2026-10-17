public class Solution {
    public static long maxWindowSum(int[] nums, int k) {
        if (k <= 0 || k > nums.length) return 0;
        long window = 0;
        for (int i = 0; i < k; i++) window += nums[i];
        long best = window;
        for (int i = k; i < nums.length; i++) {
            window += nums[i] - nums[i - k];
            best = Math.max(best, window);
        }
        return best;
    }
}
