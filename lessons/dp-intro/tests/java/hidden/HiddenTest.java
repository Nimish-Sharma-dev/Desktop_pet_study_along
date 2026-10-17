import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_stairs_zero() {
        LessonKit.check(() -> Solution.climbStairs(0), 1);
    }

    @Test
    void hidden_stairs_forty_five() {
        LessonKit.check(() -> Solution.climbStairs(45), 1836311903);
    }

    @Test
    void hidden_coins_empty_set() {
        LessonKit.check(() -> Solution.minCoins(new int[]{}, 5), -1);
    }

    @Test
    void hidden_coins_unreachable() {
        LessonKit.check(() -> Solution.minCoins(new int[]{5,10}, 7), -1);
    }

    @Test
    void hidden_coins_larger() {
        LessonKit.check(() -> Solution.minCoins(new int[]{186,419,83,408}, 6249), 20);
    }

    @Test
    void hidden_coins_many() {
        LessonKit.check(() -> Solution.minCoins(new int[]{1,5,10,25}, 10000), 400);
    }

}
