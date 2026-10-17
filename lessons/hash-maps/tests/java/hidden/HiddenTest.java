import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_sum_empty() {
        LessonKit.check(() -> Solution.twoSum(new int[]{}, 4), new int[]{});
    }

    @Test
    void hidden_sum_no_self_reuse() {
        LessonKit.check(() -> Solution.twoSum(new int[]{5}, 10), new int[]{});
    }

    @Test
    void hidden_sum_negatives() {
        LessonKit.check(() -> Solution.twoSum(new int[]{-3,4,3,90}, 0), new int[]{0,2});
    }

    @Test
    void hidden_sum_large() {
        LessonKit.check(() -> Solution.twoSum(LessonKit.range(0, 300000, 1), 599997), new int[]{299998,299999});
    }

    @Test
    void hidden_anagram_empty() {
        LessonKit.check(() -> Solution.isAnagram("", ""), true);
    }

    @Test
    void hidden_anagram_length_differs() {
        LessonKit.check(() -> Solution.isAnagram("a", "ab"), false);
    }

    @Test
    void hidden_anagram_same_letters_different_counts() {
        LessonKit.check(() -> Solution.isAnagram("aacc", "ccac"), false);
    }

}
