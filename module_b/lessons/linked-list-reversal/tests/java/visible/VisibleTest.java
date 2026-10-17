import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void five_nodes() {
        LessonKit.check(() -> ListKit.toList(Solution.reverseList(ListKit.fromList(new int[]{1,2,3,4,5}))), new int[]{5,4,3,2,1});
    }

    @Test
    void two_nodes() {
        LessonKit.check(() -> ListKit.toList(Solution.reverseList(ListKit.fromList(new int[]{1,2}))), new int[]{2,1});
    }

}
