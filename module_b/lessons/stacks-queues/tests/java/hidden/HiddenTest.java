import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_empty_string() {
        LessonKit.check(() -> Solution.isValidParentheses(""), true);
    }

    @Test
    void hidden_only_open() {
        LessonKit.check(() -> Solution.isValidParentheses("(("), false);
    }

    @Test
    void hidden_close_first() {
        LessonKit.check(() -> Solution.isValidParentheses(")("), false);
    }

    @Test
    void hidden_only_close() {
        LessonKit.check(() -> Solution.isValidParentheses("]"), false);
    }

    @Test
    void hidden_unclosed_after_valid() {
        LessonKit.check(() -> Solution.isValidParentheses("()["), false);
    }

    @Test
    void hidden_temps_empty() {
        LessonKit.check(() -> Solution.dailyTemperatures(new int[]{}), new int[]{});
    }

    @Test
    void hidden_temps_single() {
        LessonKit.check(() -> Solution.dailyTemperatures(new int[]{5}), new int[]{0});
    }

    @Test
    void hidden_temps_falling() {
        LessonKit.check(() -> Solution.dailyTemperatures(new int[]{5,4,3}), new int[]{0,0,0});
    }

    @Test
    void hidden_temps_equal() {
        LessonKit.check(() -> Solution.dailyTemperatures(new int[]{5,5,5}), new int[]{0,0,0});
    }

}
