import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void basic() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{2,7,11,15}, 9), new int[]{0,1});
    }

    @Test
    void middle_pair() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{1,2,4,6,10}, 8), new int[]{1,3});
    }

    @Test
    void outer_pair() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{1,3,4,8}, 9), new int[]{0,3});
    }

    @Test
    void no_pair() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{1,2,3}, 10), new int[]{});
    }

}
