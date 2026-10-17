public class Solution {
    public static int[] twoSumSorted(int[] nums, int target) {
        int left = 0;
        int right = nums.length - 1;
        while (left < right) {
            int total = nums[left] + nums[right];
            if (total == target) return new int[]{left, right};
            if (total < target) {
                left++;
            } else {
                right--;
            }
        }
        return new int[]{};
    }
}
