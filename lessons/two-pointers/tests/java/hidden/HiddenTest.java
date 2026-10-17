import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_empty() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{}, 5), new int[]{});
    }

    @Test
    void hidden_single_cannot_pair_with_itself() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{5}, 10), new int[]{});
    }

    @Test
    void hidden_duplicates() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{1,1,3,5}, 2), new int[]{0,1});
    }

    @Test
    void hidden_negatives() {
        LessonKit.check(() -> Solution.twoSumSorted(new int[]{-4,-1,0,3,10}, -5), new int[]{0,1});
    }

    @Test
    void hidden_large() {
        LessonKit.check(() -> Solution.twoSumSorted(LessonKit.range(0, 300000, 2), 1199994), new int[]{299998,299999});
    }

}
