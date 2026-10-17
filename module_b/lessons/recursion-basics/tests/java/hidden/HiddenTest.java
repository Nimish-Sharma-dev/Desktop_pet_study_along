import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_fib_twenty() {
        LessonKit.check(() -> Solution.fib(20), 6765);
    }

    @Test
    void hidden_fib_thirty() {
        LessonKit.check(() -> Solution.fib(30), 832040);
    }

    @Test
    void hidden_digits_power_of_ten() {
        LessonKit.check(() -> Solution.sumDigits(1000000), 1);
    }

    @Test
    void hidden_digits_ten() {
        LessonKit.check(() -> Solution.sumDigits(10), 1);
    }

}
