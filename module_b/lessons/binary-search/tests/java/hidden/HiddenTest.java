import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_empty() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{}, 3), -1);
    }

    @Test
    void hidden_single_found() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{4}, 4), 0);
    }

    @Test
    void hidden_single_missing() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{4}, 7), -1);
    }

    @Test
    void hidden_two_elements() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{1,3}, 3), 1);
    }

    @Test
    void hidden_below_min() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{5,6,7}, 1), -1);
    }

    @Test
    void hidden_large() {
        LessonKit.check(() -> Solution.binarySearch(LessonKit.range(0, 1000000, 1), 999999), 999999);
    }

}
