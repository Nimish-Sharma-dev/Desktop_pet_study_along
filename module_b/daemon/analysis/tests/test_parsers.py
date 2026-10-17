import json
from analysis.runners import parsers as P

FAIL = 'LESSON_FAIL {"error_type":"WrongAnswer","expected":2,"actual":3,"line":9}'


def test_junit_xml_pytest_junit5_gtest_shapes():
    xml = f'''<testsuites><testsuite name="s">
      <testcase classname="a" name="test_ok"/>
      <testcase classname="a" name="test_bad"><failure message="boom" type="AssertionError">{FAIL}</failure></testcase>
      <testcase classname="a" name="test_err"><error type="IndexError">trace</error></testcase>
      <testcase classname="a" name="test_skip"><skipped/></testcase></testsuite></testsuites>'''
    r = {x["name"]: x for x in P.parse_junit_xml(xml)}
    assert r["test_ok"]["passed"] and not r["test_bad"]["passed"]
    assert r["test_bad"]["info"] == {"error_type": "WrongAnswer", "expected": 2, "actual": 3, "line": 9}
    assert r["test_err"]["exception"] == "IndexError" and r["test_skip"]["skipped"]


def test_go_test_json():
    lines = [{"Action": "run", "Test": "Test_a"}, {"Action": "output", "Test": "Test_a", "Output": "--- PASS\n"},
             {"Action": "pass", "Test": "Test_a"}, {"Action": "run", "Test": "Test_b"},
             {"Action": "output", "Test": "Test_b", "Output": f"    k_test.go:5: {FAIL}\n"},
             {"Action": "fail", "Test": "Test_b"}, {"Action": "run", "Test": "Test_hang"}, {"Action": "fail"}]
    r = {x["name"]: x for x in P.parse_go_test_json("\n".join(json.dumps(l) for l in lines))}
    assert r["Test_a"]["passed"] and r["Test_b"]["info"]["actual"] == 3 and "Test_hang" not in r


def test_jest_and_vitest_json():
    data = {"testResults": [{"assertionResults": [
        {"title": "ok", "status": "passed", "failureMessages": []},
        {"title": "bad", "status": "failed", "failureMessages": [f"Error: {FAIL}\n    at x"]}]},
        {"assertionResults": [], "status": "failed", "message": "SyntaxError: nope"}]}
    r = P.parse_jest_json("warn\n" + json.dumps(data))
    assert [x["name"] for x in r] == ["ok", "bad", "<suite>"] and r[1]["info"]["expected"] == 2 and r[2]["suite_error"]


CARGO = f'''running 3 tests
test tests::found ... ok
test tests::missing ... FAILED
test tests::slow ... ignored

failures:

---- tests::missing stdout ----
thread 'tests::missing' panicked at 'assertion failed: {FAIL}', tests/v.rs:9:5

failures:
    tests::missing
'''


def test_cargo_test_text():
    r = {x["name"]: x for x in P.parse_cargo_test(CARGO)}
    assert r["tests::found"]["passed"] and r["tests::slow"]["skipped"]
    assert not r["tests::missing"]["passed"] and r["tests::missing"]["info"]["line"] == 9


def test_xunit_xml():
    xml = f'''<assemblies><assembly><collection>
      <test name="L.V.found" result="Pass"/>
      <test name="L.V.missing" result="Fail"><failure><message><![CDATA[{FAIL}]]></message><stack-trace>at S</stack-trace></failure></test>
      <test name="L.V.skipped" result="Skip"/></collection></assembly></assemblies>'''
    r = {x["name"]: x for x in P.parse_xunit_xml(xml)}
    assert r["L.V.found"]["passed"] and r["L.V.missing"]["info"]["error_type"] == "WrongAnswer" and r["L.V.skipped"]["skipped"]


def test_empty_outputs_do_not_crash():
    assert P.parse_junit_xml("") == [] and P.parse_jest_json("") == [] and P.parse_go_test_json("") == []
