"""Tests for scripts/check_essay.py (stdlib unittest; run: python -m unittest discover -s tests)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "check_essay.py")
RULES = os.path.join(ROOT, "assets", "lint-rules.json")

spec = importlib.util.spec_from_file_location("check_essay", SCRIPT)
ce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ce)


def para(n, ch="字"):
    """A paragraph of exactly n counted characters, ending with a full stop."""
    return ch * (n - 1) + "。"


def make_essay(title="认可度之上，更有价值度", sizes=(120, 150, 170, 170, 170, 130), extra=None):
    paras = [para(n) for n in sizes]
    if extra:
        paras[1] = extra + paras[1]
    return title + "\n" + "\n".join(paras) + "\n"


def load_rules():
    with open(RULES, encoding="utf8") as f:
        return json.load(f)


def ids(report, level=None):
    return {f["id"] for f in report["findings"] if level is None or f["level"] == level}


class CountingTests(unittest.TestCase):
    def test_count_with_and_without_punct(self):
        c = ce.count_chars("我们，要“学习”！\n  好 好")
        self.assertEqual(c["with_punct"], 11)  # 我们，要“学习”！好好 -> 11 non-space chars
        self.assertEqual(c["without_punct"], 7)  # 我们要学习好好

    def test_digits_and_latin_count_one_each(self):
        c = ce.count_chars("AI在2026年")
        self.assertEqual(c["with_punct"], 8)
        self.assertEqual(c["without_punct"], 8)


class ParseTests(unittest.TestCase):
    def test_title_is_first_short_line(self):
        t, body = ce.split_title_body("认可度之上\n第一段。\n第二段。\n")
        self.assertEqual(t, "认可度之上")
        self.assertEqual(body, ["第一段。", "第二段。"])

    def test_markdown_title_markers_are_stripped(self):
        t, _ = ce.split_title_body("# 《认可度之上》\n正文。\n")
        self.assertEqual(t, "认可度之上")

    def test_missing_title_when_first_line_is_a_sentence(self):
        t, body = ce.split_title_body("今天，我们用点赞数衡量一切。\n第二段。\n")
        self.assertIsNone(t)
        self.assertEqual(len(body), 2)

    def test_explicit_title_overrides_and_is_dropped_from_body(self):
        t, body = ce.split_title_body("固定标题\n正文一。\n", title="固定标题")
        self.assertEqual(t, "固定标题")
        self.assertEqual(body, ["正文一。"])


class WriteChecks(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules()

    def test_clean_essay_has_no_hard_findings(self):
        r = ce.analyze(make_essay(), self.rules, mode="write")
        self.assertEqual(ids(r, "hard"), set(), r["findings"])
        self.assertTrue(r["passed"])

    def test_too_short_is_hard(self):
        r = ce.analyze(make_essay(sizes=(100, 100, 100, 100, 100, 100)), self.rules, mode="write")
        self.assertIn("length_out_of_range", ids(r, "hard"))

    def test_too_long_is_hard(self):
        r = ce.analyze(make_essay(sizes=(150, 250, 250, 250, 250, 120)), self.rules, mode="write")
        self.assertIn("length_out_of_range", ids(r, "hard"))

    def test_missing_title_hard(self):
        text = "今天，我们用点赞数衡量一切，也用它衡量自己的价值。\n" + "\n".join(para(n) for n in (120, 150, 170, 170, 170, 130)) + "\n"
        r = ce.analyze(text, self.rules, mode="write")
        self.assertIn("no_title", ids(r, "hard"))

    def test_subheadings_detected(self):
        text = make_essay().replace("\n字", "\n一、字", 1)
        r = ce.analyze(text, self.rules, mode="write")
        self.assertIn("subheading", ids(r, "hard"))

    def test_markdown_heading_in_body_detected(self):
        text = make_essay() + "## 小标题\n"
        r = ce.analyze(text, self.rules, mode="write")
        self.assertIn("subheading", ids(r, "hard"))

    def test_banned_term(self):
        r = ce.analyze(make_essay(extra="综上所述，"), self.rules, mode="write")
        self.assertIn("banned_term", ids(r, "hard"))

    def test_banned_title(self):
        r = ce.analyze(make_essay(title="破茧成蝶"), self.rules, mode="write")
        self.assertIn("banned_title", ids(r, "hard"))

    def test_however_limit(self):
        r = ce.analyze(make_essay(extra="然而，" * 3 + "但是，"), self.rules, mode="write")
        self.assertIn("however_limit", ids(r, "hard"))
        r2 = ce.analyze(make_essay(extra="然而，" * 3), self.rules, mode="write")
        self.assertNotIn("however_limit", ids(r2))

    def test_exclamation_limit(self):
        r = ce.analyze(make_essay(extra="好！好！"), self.rules, mode="write")
        self.assertIn("exclamation_limit", ids(r, "hard"))

    def test_mechanical_first_second(self):
        r = ce.analyze(make_essay(extra="首先，其次，"), self.rules, mode="write")
        self.assertIn("mechanical_order", ids(r, "hard"))

    def test_dash_budget_soft(self):
        r = ce.analyze(make_essay(extra="甲——乙，丙——丁，戊——己，"), self.rules, mode="write")
        self.assertIn("dash_budget", ids(r, "soft"))

    def test_signature_phrase_budget_soft(self):
        r = ce.analyze(make_essay(extra="更值得警惕的是，更值得警惕的是，"), self.rules, mode="write")
        sig = [f for f in r["findings"] if f["id"] == "signature_phrase"]
        self.assertTrue(sig and "更值得警惕的是" in sig[0]["msg"])
        self.assertEqual(sig[0]["level"], "soft")

    def test_parallelism_detected(self):
        text = make_essay(extra="他看见了光，他看见了影，他看见了路，")
        r = ce.analyze(text, self.rules, mode="write")
        self.assertGreaterEqual(r["metrics"]["parallelism_runs"], 1)

    def test_connector_openers_soft(self):
        paras = [para(120), "诚然，" + para(150), "可是，" + para(170), "更值得警惕的是，" + para(170), "由此看来，" + para(170), para(130)]
        text = "标题\n" + "\n".join(paras) + "\n"
        r = ce.analyze(text, self.rules, mode="write")
        self.assertIn("connector_openers", ids(r, "soft"))
        self.assertEqual(r["metrics"]["connector_openers"], 4)
        r2 = ce.analyze(make_essay(), self.rules, mode="write")
        self.assertNotIn("connector_openers", ids(r2))

    def test_keywords_counted(self):
        text = make_essay(extra="认可度认可度")
        r = ce.analyze(text, self.rules, mode="write", keywords=["认可度", "价值度"])
        self.assertEqual(r["metrics"]["keywords"]["认可度"]["body"], 2)
        self.assertIn("keyword_low", ids(r))  # 价值度 appears 0 times in body

    def test_first_and_last_paragraph_soft_limits(self):
        r = ce.analyze(make_essay(sizes=(260, 100, 170, 170, 170, 60)), self.rules, mode="write")
        self.assertIn("first_para_long", ids(r, "soft"))
        self.assertIn("last_para_size", ids(r, "soft"))


class DraftChecks(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules()

    def test_deductions_no_title_and_shortfall(self):
        text = "\n".join(para(n) for n in (100, 100, 100, 100, 100, 100)) + "\n"
        text = "今天我们都生活在点赞数构成的世界里面，" + text  # first line is a sentence -> no title
        r = ce.analyze(text, self.rules, mode="draft")
        d = r["deductions"]
        self.assertEqual(d["no_title"], 2)
        self.assertEqual(d["length_shortfall_with_punct"], 4)  # 800-~640 -> ceil(160/50)=4

    def test_draft_mode_uses_exam_minimum_for_hard_length(self):
        r = ce.analyze(make_essay(sizes=(130, 140, 150, 150, 150, 120)), self.rules, mode="draft")  # 840 chars
        self.assertNotIn("length_out_of_range", ids(r, "hard"))
        self.assertIn("length_below_recommended", ids(r, "soft"))
        r2 = ce.analyze(make_essay(sizes=(130, 130, 130, 130, 130, 100)), self.rules, mode="draft")  # 750 chars
        self.assertIn("length_out_of_range", ids(r2, "hard"))

    def test_no_deduction_for_adequate_essay(self):
        r = ce.analyze(make_essay(sizes=(150, 200, 200, 200, 200, 100)), self.rules, mode="draft")
        self.assertEqual(r["deductions"]["no_title"], 0)
        self.assertEqual(r["deductions"]["length_shortfall_with_punct"], 0)

    def test_punctuation_pairing_errors(self):
        text = make_essay(extra="他说“好，又说《书名，")
        r = ce.analyze(text, self.rules, mode="draft")
        self.assertGreaterEqual(r["metrics"]["punct_errors"], 2)

    def test_repeated_punct_and_ascii_quotes(self):
        text = make_essay(extra='他说"好"，，')
        r = ce.analyze(text, self.rules, mode="draft")
        self.assertGreaterEqual(r["metrics"]["punct_errors"], 2)

    def test_paragraph_table_locates_issues(self):
        text = make_essay(extra="然而，更值得警惕的是，")
        r = ce.analyze(text, self.rules, mode="draft")
        p2 = r["paragraphs"][1]
        self.assertEqual(p2["however"], 1)
        self.assertIn("更值得警惕的是", p2["signature"])
        self.assertEqual(p2["index"], 2)

    def test_fixed_title_check(self):
        text = make_essay(title="认可度之上，更有价值度")
        r = ce.analyze(text, self.rules, mode="draft", title="认可度之上，更有价值度")
        self.assertTrue(r["metrics"]["title_matches_fixed"])
        r2 = ce.analyze(text.replace("认可度之上", "认可度之下", 1), self.rules, mode="draft", title="认可度之上，更有价值度")
        self.assertFalse(r2["metrics"]["title_matches_fixed"])


class DiffTests(unittest.TestCase):
    def test_identical(self):
        d = ce.diff_essays(make_essay(), make_essay())
        self.assertEqual(d["changed_ratio"], 0.0)
        self.assertTrue(d["title_unchanged"])

    def test_rewrite_ratio_and_title(self):
        old = "标题甲\n" + "\n".join(["甲" * 100, "乙" * 100, "丙" * 100]) + "\n"
        new = "标题乙\n" + "\n".join(["甲" * 100, "戊" * 100, "己" * 100]) + "\n"
        d = ce.diff_essays(old, new)
        self.assertFalse(d["title_unchanged"])
        self.assertGreater(d["changed_ratio"], 0.5)
        self.assertEqual([p["status"] for p in d["paragraphs"]], ["unchanged", "modified", "modified"])

    def test_added_and_removed_paragraphs(self):
        old = "标题\n" + "\n".join(["甲" * 100, "乙" * 100]) + "\n"
        new = "标题\n" + "\n".join(["甲" * 100, "乙" * 100, "丙" * 100]) + "\n"
        d = ce.diff_essays(old, new)
        self.assertEqual(d["paragraphs"][-1]["status"], "added")


class ClaimsTests(unittest.TestCase):
    def test_extracts_titles_quotes_numbers_speakers(self):
        text = "标题\n苏轼在《定风波》里写“一蓑烟雨任平生”。2015年，屠呦呦获诺贝尔奖。据统计增长了37%。鲁迅说：“无穷的远方，无数的人们，都和我有关。”\n"
        c = ce.extract_claims(text)
        kinds = {x["kind"] for x in c}
        self.assertTrue({"work_title", "quote", "year", "number", "speaker"} <= kinds)
        quotes = [x["text"] for x in c if x["kind"] == "quote"]
        self.assertIn("一蓑烟雨任平生", quotes)
        self.assertTrue(any(x["text"] == "鲁迅" for x in c if x["kind"] == "speaker"))

    def test_short_scare_quotes_ignored(self):
        c = ce.extract_claims("标题\n所谓“转”并非必经。\n")
        self.assertEqual([x for x in c if x["kind"] == "quote"], [])


class LengthBandTests(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules()

    def test_between_1000_and_1100_is_soft_only(self):
        r = ce.analyze(make_essay(sizes=(150, 200, 200, 200, 200, 100)), self.rules, mode="write")
        self.assertEqual(sum(r["metrics"]["paragraph_chars"]), 1050)
        self.assertNotIn("length_out_of_range", ids(r, "hard"))
        self.assertIn("length_above_recommended", ids(r, "soft"))

    def test_above_1100_is_hard(self):
        r = ce.analyze(make_essay(sizes=(150, 250, 250, 250, 250, 100)), self.rules, mode="write")
        self.assertIn("length_out_of_range", ids(r, "hard"))


class ClaimsV2Tests(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules()

    def test_known_entities_detected(self):
        text = "标题\n梵高生前画作销路极差。费斯汀格提出社会比较理论，伽利略用望远镜看月面。\n"
        c = ce.extract_claims(text, self.rules)
        ents = {x["text"] for x in c if x["kind"] == "entity"}
        self.assertTrue({"梵高", "费斯汀格", "伽利略"} <= ents)

    def test_speaker_requires_quote_or_colon_after_verb(self):
        text = "标题\n他听了之后说得很好。这样的时刻认为很多。鲁迅说：“无穷的远方，无数的人们，都和我有关。”\n"
        c = ce.extract_claims(text, self.rules)
        sp = [x["text"] for x in c if x["kind"] == "speaker"]
        self.assertEqual(sp, ["鲁迅"])

    def test_ledger_reconciliation(self):
        text = "标题\n梵高生前画作销路极差。《红楼梦》在小圈子传抄。2015年屠呦呦获奖。\n"
        ledger = "| E1 | 梵高 | ... |\n| E2 | 红楼梦 | ... |"
        c = ce.extract_claims(text, self.rules, ledger_text=ledger)
        by = {x["text"]: x["in_ledger"] for x in c}
        self.assertTrue(by["梵高"])
        self.assertTrue(by["红楼梦"])
        self.assertFalse(by["2015年"])


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf8")

    def test_write_cli_exit_codes_and_json(self):
        with tempfile.TemporaryDirectory() as d:
            good = os.path.join(d, "good.md")
            bad = os.path.join(d, "bad.md")
            with open(good, "w", encoding="utf8") as fh:
                fh.write(make_essay())
            with open(bad, "w", encoding="utf8") as fh:
                fh.write(make_essay(sizes=(50, 50, 50, 50, 50, 50)))
            p = self.run_cli("write", good, "--json")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertTrue(json.loads(p.stdout)["passed"])
            p = self.run_cli("write", bad, "--json")
            self.assertEqual(p.returncode, 1)
            self.assertFalse(json.loads(p.stdout)["passed"])

    def test_missing_file_is_usage_error(self):
        p = self.run_cli("write", "does-not-exist.md")
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
