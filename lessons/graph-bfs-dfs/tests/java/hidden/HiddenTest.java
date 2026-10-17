import org.junit.jupiter.api.Test;

public class HiddenTest {
    @Test
    void hidden_path_cycle_terminates() {
        LessonKit.check(() -> Solution.shortestPath(4, new int[][]{{0,1},{1,2},{2,3},{3,0}}, 0, 2), 2);
    }

    @Test
    void hidden_path_single_node() {
        LessonKit.check(() -> Solution.shortestPath(1, new int[][]{}, 0, 0), 0);
    }

    @Test
    void hidden_path_long_chain() {
        LessonKit.check(() -> Solution.shortestPath(3000, LessonKit.chainEdges(3000), 0, 2999), 2999);
    }

    @Test
    void hidden_components_no_nodes() {
        LessonKit.check(() -> Solution.countComponents(0, new int[][]{}), 0);
    }

    @Test
    void hidden_components_cycle() {
        LessonKit.check(() -> Solution.countComponents(4, new int[][]{{0,1},{1,2},{2,3},{3,0}}), 1);
    }

    @Test
    void hidden_components_isolated() {
        LessonKit.check(() -> Solution.countComponents(4, new int[][]{}), 4);
    }

    @Test
    void hidden_components_deep_chain() {
        LessonKit.check(() -> Solution.countComponents(3000, LessonKit.chainEdges(3000)), 1);
    }

}
