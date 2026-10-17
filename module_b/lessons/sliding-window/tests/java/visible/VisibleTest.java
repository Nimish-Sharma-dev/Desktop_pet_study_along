import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void basic() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{1,4,2,10,2,3,1,0,20}, 4), 24L);
    }

    @Test
    void small_window() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{2,1,5,1,3,2}, 3), 9L);
    }

    @Test
    void one_element() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{5}, 1), 5L);
    }

    @Test
    void all_negative() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{-3,-1,-2}, 2), -3L);
    }

}
