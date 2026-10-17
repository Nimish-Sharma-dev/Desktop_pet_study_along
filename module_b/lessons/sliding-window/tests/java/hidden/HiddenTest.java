import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_window_is_whole_list() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{1,2,3}, 3), 6L);
    }

    @Test
    void hidden_window_too_big() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{1,2}, 5), 0L);
    }

    @Test
    void hidden_empty() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{}, 3), 0L);
    }

    @Test
    void hidden_zero_window() {
        LessonKit.check(() -> Solution.maxWindowSum(new int[]{1,2,3}, 0), 0L);
    }

    @Test
    void hidden_large() {
        LessonKit.check(() -> Solution.maxWindowSum(LessonKit.range(0, 1500000, 1), 5000), 7487497500L);
    }

}
