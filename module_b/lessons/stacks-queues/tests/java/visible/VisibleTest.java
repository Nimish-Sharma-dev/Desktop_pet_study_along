import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void valid_simple() {
        LessonKit.check(() -> Solution.isValidParentheses("()"), true);
    }

    @Test
    void valid_mixed() {
        LessonKit.check(() -> Solution.isValidParentheses("()[]{}"), true);
    }

    @Test
    void valid_nested() {
        LessonKit.check(() -> Solution.isValidParentheses("{[]}"), true);
    }

    @Test
    void invalid_wrong_type() {
        LessonKit.check(() -> Solution.isValidParentheses("(]"), false);
    }

    @Test
    void invalid_interleaved() {
        LessonKit.check(() -> Solution.isValidParentheses("([)]"), false);
    }

    @Test
    void temps_example() {
        LessonKit.check(() -> Solution.dailyTemperatures(new int[]{73,74,75,71,69,72,76,73}), new int[]{1,1,4,2,1,1,0,0});
    }

    @Test
    void temps_rising() {
        LessonKit.check(() -> Solution.dailyTemperatures(new int[]{30,40,50,60}), new int[]{1,1,1,0});
    }

    @Test
    void temps_short() {
        LessonKit.check(() -> Solution.dailyTemperatures(new int[]{30,60,90}), new int[]{1,1,0});
    }

}
