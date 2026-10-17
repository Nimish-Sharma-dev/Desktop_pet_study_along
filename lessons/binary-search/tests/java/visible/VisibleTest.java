import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void found_middle() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{1,3,5,7,9}, 5), 2);
    }

    @Test
    void found_first() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{1,3,5,7,9}, 1), 0);
    }

    @Test
    void found_last() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{1,3,5,7,9}, 9), 4);
    }

    @Test
    void not_found_inside() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{1,3,5,7,9}, 4), -1);
    }

    @Test
    void not_found_above() {
        LessonKit.check(() -> Solution.binarySearch(new int[]{1,3,5,7,9}, 10), -1);
    }

}
