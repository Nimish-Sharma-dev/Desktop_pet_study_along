import org.junit.jupiter.api.Test;

public class VisibleTest {
    @Test
    void path_chain() {
        LessonKit.check(() -> Solution.shortestPath(5, new int[][]{{0,1},{1,2},{2,3},{3,4}}, 0, 4), 4);
    }

    @Test
    void path_uses_shortcut() {
        LessonKit.check(() -> Solution.shortestPath(5, new int[][]{{0,1},{1,2},{2,3},{3,4},{0,4}}, 0, 3), 2);
    }

    @Test
    void path_unreachable() {
        LessonKit.check(() -> Solution.shortestPath(4, new int[][]{{0,1},{2,3}}, 0, 3), -1);
    }

    @Test
    void path_same_node() {
        LessonKit.check(() -> Solution.shortestPath(3, new int[][]{{0,1}}, 2, 2), 0);
    }

    @Test
    void components_two_pairs() {
        LessonKit.check(() -> Solution.countComponents(5, new int[][]{{0,1},{2,3}}), 3);
    }

    @Test
    void components_connected() {
        LessonKit.check(() -> Solution.countComponents(3, new int[][]{{0,1},{1,2}}), 1);
    }

}
