package solution

import (
	"encoding/json"
	"fmt"
	"regexp"
	"runtime/debug"
	"strconv"
	"strings"
	"testing"
	"time"
)

// Lesson test kit (go). Failures are reported as `LESSON_FAIL {json}`.

var lineRx = regexp.MustCompile(`solution\.go:(\d+)`)

func lessonRange(start, count, step int) []int {
	out := make([]int, count)
	for i := range out {
		out[i] = start + i*step
	}
	return out
}

func lessonChainEdges(n int) [][]int {
	out := [][]int{}
	for i := 0; i+1 < n; i++ {
		out = append(out, []int{i, i + 1})
	}
	return out
}

func jsonStr(v interface{}) string {
	b, err := json.Marshal(v)
	if err != nil {
		return fmt.Sprintf("%v", v)
	}
	s := string(b)
	if s == "null" {
		return "[]"
	}
	return s
}

func classify(msg string) string {
	switch {
	case strings.Contains(msg, "index out of range"), strings.Contains(msg, "slice bounds out of range"):
		return "IndexError"
	case strings.Contains(msg, "nil pointer"):
		return "NullReference"
	case strings.Contains(msg, "stack"):
		return "RecursionError"
	}
	return "Panic"
}

func lessonFail(t *testing.T, expected, actual interface{}, et, detail, stack string) {
	t.Helper()
	info := map[string]interface{}{"error_type": et, "detail": detail}
	var e, a interface{}
	_ = json.Unmarshal([]byte(jsonStr(expected)), &e)
	info["expected"] = e
	if actual != nil {
		_ = json.Unmarshal([]byte(jsonStr(actual)), &a)
		info["actual"] = a
	}
	if m := lineRx.FindStringSubmatch(stack); m != nil {
		n, _ := strconv.Atoi(m[1])
		info["line"] = n
	}
	b, _ := json.Marshal(info)
	t.Errorf("LESSON_FAIL %s", string(b))
}

func runCase(t *testing.T, f func() interface{}, expected interface{}) {
	t.Helper()
	type outcome struct {
		v     interface{}
		perr  interface{}
		stack string
	}
	ch := make(chan outcome, 1)
	go func() {
		defer func() {
			if r := recover(); r != nil {
				ch <- outcome{perr: r, stack: string(debug.Stack())}
			}
		}()
		ch <- outcome{v: f()}
	}()
	select {
	case o := <-ch:
		if o.perr != nil {
			msg := fmt.Sprint(o.perr)
			lessonFail(t, expected, nil, classify(msg), msg, o.stack)
			return
		}
		if jsonStr(o.v) != jsonStr(expected) {
			lessonFail(t, expected, o.v, "WrongAnswer", "", "")
		}
	case <-time.After(2 * time.Second):
		lessonFail(t, expected, nil, "Timeout", "no answer after 2s", "")
	}
}
