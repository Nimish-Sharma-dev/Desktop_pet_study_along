import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void sum_basic() {
        LessonKit.check(() -> Solution.twoSum(new int[]{2,7,11,15}, 9), new int[]{0,1});
    }

    @Test
    void sum_not_first() {
        LessonKit.check(() -> Solution.twoSum(new int[]{3,2,4}, 6), new int[]{1,2});
    }

    @Test
    void sum_duplicates() {
        LessonKit.check(() -> Solution.twoSum(new int[]{3,3}, 6), new int[]{0,1});
    }

    @Test
    void sum_none() {
        LessonKit.check(() -> Solution.twoSum(new int[]{1,2,3}, 7), new int[]{});
    }

    @Test
    void anagram_yes() {
        LessonKit.check(() -> Solution.isAnagram("listen", "silent"), true);
    }

    @Test
    void anagram_no() {
        LessonKit.check(() -> Solution.isAnagram("rat", "car"), false);
    }

}
