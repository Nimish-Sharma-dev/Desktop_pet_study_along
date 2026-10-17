import java.util.*;
import java.util.concurrent.*;
import java.util.regex.*;
import org.junit.jupiter.api.Assertions;

/** Lesson test kit (java). Failures are reported as `LESSON_FAIL {json}`. */
public class LessonKit {
    static final int TIMEOUT_MS = 2000;

    public static int[] range(int start, int count, int step) {
        int[] out = new int[count];
        for (int i = 0; i < count; i++) out[i] = start + i * step;
        return out;
    }

    public static int[][] chainEdges(int n) {
        int[][] out = new int[Math.max(0, n - 1)][];
        for (int i = 0; i + 1 < n; i++) out[i] = new int[]{i, i + 1};
        return out;
    }

    static String json(Object v) {
        if (v == null) return "null";
        if (v instanceof int[]) return Arrays.toString((int[]) v).replace(" ", "");
        if (v instanceof int[][]) {
            StringBuilder sb = new StringBuilder("[");
            int[][] a = (int[][]) v;
            for (int i = 0; i < a.length; i++) { if (i > 0) sb.append(","); sb.append(json(a[i])); }
            return sb.append("]").toString();
        }
        if (v instanceof String) return "\"" + ((String) v).replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
        return String.valueOf(v);
    }

    static String errorType(Throwable t) {
        String n = t.getClass().getSimpleName();
        if (t instanceof StackOverflowError) return "RecursionError";
        if (t instanceof IndexOutOfBoundsException || t instanceof NoSuchElementException || t instanceof java.util.EmptyStackException) return "IndexError";
        if (t instanceof NullPointerException) return "NullReference";
        if (t instanceof OutOfMemoryError) return "MemoryError";
        return n;
    }

    static void fail(String errorType, Object expected, Object actual, boolean hasActual, String detail, Throwable t) {
        StringBuilder sb = new StringBuilder("{\"error_type\":").append(json(errorType));
        sb.append(",\"expected\":").append(json(expected));
        if (hasActual) sb.append(",\"actual\":").append(json(actual));
        sb.append(",\"detail\":").append(json(detail == null ? "" : detail));
        if (t != null) {
            for (StackTraceElement e : t.getStackTrace()) {
                if ("Solution.java".equals(e.getFileName())) { sb.append(",\"line\":").append(e.getLineNumber()); break; }
            }
        }
        sb.append("}");
        Assertions.fail("LESSON_FAIL " + sb);
    }

    public static void check(Callable<Object> f, Object expected) {
        ExecutorService ex = Executors.newSingleThreadExecutor(r -> {
            Thread th = new Thread(null, r, "case", 16L * 1024 * 1024);
            th.setDaemon(true);
            return th;
        });
        Future<Object> fut = ex.submit(f);
        try {
            Object actual = fut.get(TIMEOUT_MS, TimeUnit.MILLISECONDS);
            if (!json(actual).equals(json(expected))) fail("WrongAnswer", expected, actual, true, "", null);
        } catch (TimeoutException e) {
            fut.cancel(true);
            fail("Timeout", expected, null, false, "no answer after 2s", null);
        } catch (ExecutionException e) {
            Throwable c = e.getCause();
            fail(errorType(c), expected, null, false, c.getClass().getSimpleName() + ": " + String.valueOf(c.getMessage()), c);
        } catch (InterruptedException e) {
            fail("Crash", expected, null, false, "interrupted", null);
        } finally {
            ex.shutdownNow();
        }
    }
}
