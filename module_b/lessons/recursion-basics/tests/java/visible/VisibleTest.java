import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void fib_zero() {
        LessonKit.check(() -> Solution.fib(0), 0);
    }

    @Test
    void fib_one() {
        LessonKit.check(() -> Solution.fib(1), 1);
    }

    @Test
    void fib_two() {
        LessonKit.check(() -> Solution.fib(2), 1);
    }

    @Test
    void fib_ten() {
        LessonKit.check(() -> Solution.fib(10), 55);
    }

    @Test
    void digits_zero() {
        LessonKit.check(() -> Solution.sumDigits(0), 0);
    }

    @Test
    void digits_single() {
        LessonKit.check(() -> Solution.sumDigits(7), 7);
    }

    @Test
    void digits_123() {
        LessonKit.check(() -> Solution.sumDigits(123), 6);
    }

    @Test
    void digits_9999() {
        LessonKit.check(() -> Solution.sumDigits(9999), 36);
    }

}
