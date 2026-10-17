import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void stairs_one() {
        LessonKit.check(() -> Solution.climbStairs(1), 1);
    }

    @Test
    void stairs_two() {
        LessonKit.check(() -> Solution.climbStairs(2), 2);
    }

    @Test
    void stairs_five() {
        LessonKit.check(() -> Solution.climbStairs(5), 8);
    }

    @Test
    void coins_basic() {
        LessonKit.check(() -> Solution.minCoins(new int[]{1,2,5}, 11), 3);
    }

    @Test
    void coins_impossible() {
        LessonKit.check(() -> Solution.minCoins(new int[]{2}, 3), -1);
    }

    @Test
    void coins_zero_amount() {
        LessonKit.check(() -> Solution.minCoins(new int[]{1}, 0), 0);
    }

    @Test
    void coins_greedy_fails() {
        LessonKit.check(() -> Solution.minCoins(new int[]{1,3,4}, 6), 2);
    }

}
