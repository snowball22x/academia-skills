#!/usr/bin/env python3
"""check_essay.py - deterministic checks for Shanghai gaokao essays (stdlib only, UTF-8).

Reports only; never rewrites text. Subcommands:

  write  ESSAY.md [--keywords a,b] [--json]       checks for a freshly written essay (hard/soft rules)
  draft  ESSAY.md [--title T] [--keywords a,b]    checks for a student draft: + deduction estimate,
                                                  + per-paragraph table, + fixed-title check
  diff   OLD.md NEW.md                            paragraph-level change ratio (limits "local edit" scope)
  claims ESSAY.md                                 extract checkable statements for the evidence ledger

Essay file format: first non-empty line = title, remaining non-empty lines = paragraphs.
Exit codes: 0 ok / 1 hard findings (write/draft) / 2 usage or file error.
Rules live in assets/lint-rules.json (override with --rules).
"""
from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import re
import statistics
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RULES = os.path.join(os.path.dirname(HERE), "assets", "lint-rules.json")

TERMINAL_PUNCT = "。！？!?；…"
SUBHEADING_PATTERNS = [
    re.compile(r"^#{1,6}\s"),
    re.compile(r"^[一二三四五六七八九十]+[、．.]"),
    re.compile(r"^\d+[、．.)）]"),
    re.compile(r"^[（(][一二三四五六七八九十\d]+[）)]"),
    re.compile(r"^第[一二三四五六七八九十\d]+[点部分章节]"),
]
PAIRS = {"“": "”", "‘": "’", "《": "》", "（": "）", "「": "」", "『": "』"}
CLOSERS = {v: k for k, v in PAIRS.items()}


# ----------------------------------------------------------------- basics
def count_chars(text: str) -> dict:
    """Count non-whitespace characters, with and without punctuation (Unicode category P*)."""
    chars = [c for c in text if not c.isspace()]
    no_punct = [c for c in chars if not unicodedata.category(c).startswith("P")]
    return {"with_punct": len(chars), "without_punct": len(no_punct)}


def _clean_title(line: str) -> str:
    t = line.strip().lstrip("#").strip()
    if len(t) >= 2 and t[0] == "《" and t[-1] == "》":
        t = t[1:-1]
    return t.strip().strip("“”\"'")


def split_title_body(text: str, title: str | None = None):
    lines = [ln.strip() for ln in text.replace("\r", "").split("\n") if ln.strip()]
    if not lines:
        return (title, [])
    first = _clean_title(lines[0])
    if title is not None:
        if first == _clean_title(title):
            return (title, lines[1:])
        return (title, lines)
    looks_like_title = len(first) <= 30 and not first.endswith(tuple(TERMINAL_PUNCT)) and first != ""
    if looks_like_title:
        return (first, lines[1:])
    return (None, lines)


def load_rules(path: str | None = None) -> dict:
    with open(path or DEFAULT_RULES, encoding="utf8") as f:
        return json.load(f)


def _find(f, fid, level, msg, where=None):
    f.append({"id": fid, "level": level, "msg": msg, "where": where})


def punct_errors(paragraphs: list[str]) -> int:
    n = 0
    for p in paragraphs:
        stack = []
        for c in p:
            if c in PAIRS:
                stack.append(c)
            elif c in CLOSERS:
                if stack and stack[-1] == CLOSERS[c]:
                    stack.pop()
                else:
                    n += 1
        n += len(stack)
        n += math.ceil(p.count('"') / 2) if '"' in p else 0
        n += len(re.findall(r"([，。；：、！？])\1", p))
        n += len(re.findall(r"，。", p))
    return n


def parallelism_runs(paragraphs: list[str]) -> int:
    runs = 0
    for p in paragraphs:
        clauses = [c for c in re.split(r"[，；。！？]", p) if c]
        i = 0
        while i < len(clauses):
            j = i
            while (
                j + 1 < len(clauses)
                and 3 <= len(clauses[j]) <= 30
                and 3 <= len(clauses[j + 1]) <= 30
                and clauses[j][:2] == clauses[j + 1][:2]
            ):
                j += 1
            if j - i + 1 >= 3:
                runs += 1
            i = j + 1
    return runs


def sentence_lengths(paragraphs: list[str]) -> list[int]:
    out = []
    for p in paragraphs:
        for s in re.split(r"[。！？!?]", p):
            s = s.strip()
            if s:
                out.append(count_chars(s)["with_punct"])
    return out


def _is_subheading(line: str) -> bool:
    if any(p.search(line) for p in SUBHEADING_PATTERNS):
        return True
    return len(line) <= 20 and not line.endswith(tuple(TERMINAL_PUNCT + "”"))


# --------------------------------------------------------------- analysis
def analyze(text: str, rules: dict, mode: str = "write", keywords=None, title: str | None = None) -> dict:
    t, body = split_title_body(text, title=title)
    body_text = "\n".join(body)
    cc = count_chars(body_text)
    findings: list[dict] = []
    lim, lr, pr = rules["limits"], rules["length"], rules["paragraphs"]

    # --- title
    if t is None or t == "":
        _find(findings, "no_title", "hard", "无标题（上海细则：无标题扣2分）")
    else:
        for w in rules["banned_title_terms"]:
            if w in t:
                _find(findings, "banned_title", "hard", f"标题含烂俗意象“{w}”", "title")

    # --- length
    if not (lr["min_with_punct"] <= cc["with_punct"] <= lr["max_with_punct"]):
        _find(findings, "length_out_of_range", "hard",
              f"正文{cc['with_punct']}字（含标点），目标{lr['min_with_punct']}–{lr['max_with_punct']}")
    if cc["without_punct"] < lr["exam_minimum"]:
        _find(findings, "length_no_punct_below_min", "soft",
              f"不计标点仅{cc['without_punct']}字，若阅卷口径不计标点则可能不足{lr['exam_minimum']}字；加厚阐释而非加例子")

    # --- paragraphs
    plen = [count_chars(p)["with_punct"] for p in body]
    if body and not (pr["min"] <= len(body) <= pr["max"]):
        _find(findings, "paragraph_count", "soft", f"共{len(body)}段，建议{pr['min']}–{pr['max']}段")
    if plen and plen[0] > pr["first_max_chars"]:
        _find(findings, "first_para_long", "soft", f"首段{plen[0]}字，应≤{pr['first_max_chars']}字", "para 1")
    if plen and not (pr["last_min_chars"] <= plen[-1] <= pr["last_max_chars"]):
        _find(findings, "last_para_size", "soft",
              f"结尾段{plen[-1]}字，建议{pr['last_min_chars']}–{pr['last_max_chars']}字", f"para {len(body)}")

    # --- subheadings
    for i, p in enumerate(body, 1):
        if _is_subheading(p):
            _find(findings, "subheading", "hard", f"疑似小标题/序号分节：{p[:20]}", f"para {i}")

    # --- banned terms
    for w in rules["banned_terms"]:
        if w in body_text:
            _find(findings, "banned_term", "hard", f"含论文腔/空话“{w}”×{body_text.count(w)}")

    # --- connectors
    however = sum(body_text.count(w) for w in rules["however_terms"])
    if however > lim["however_total"]:
        _find(findings, "however_limit", "hard", f"“然而/但是”共{however}次，上限{lim['however_total']}")
    order_hits = [w for w in rules["mechanical_order_terms"] if w in body_text]
    if len(order_hits) >= 2:
        _find(findings, "mechanical_order", "hard", f"机械推进词并用：{'/'.join(order_hits)}")

    # --- punctuation budgets
    excl = body_text.count("！") + body_text.count("!")
    if excl > lim["exclamation_total"]:
        _find(findings, "exclamation_limit", "hard", f"感叹号{excl}个，上限{lim['exclamation_total']}")
    dashes = body_text.count("——")
    if dashes > lim["dash_total"]:
        _find(findings, "dash_budget", "soft", f"破折号{dashes}个，建议≤{lim['dash_total']}（破折号是阅卷老师点名的AI信号之一）")

    # --- signature phrases
    sig_counts = {}
    for phrase, mx in rules["signature_phrases"].items():
        if phrase.startswith("_"):
            continue
        n = body_text.count(phrase)
        sig_counts[phrase] = n
        if n > mx:
            _find(findings, "signature_phrase", "soft", f"口头禅“{phrase}”×{n}，上限{mx}；换说法或删")

    # --- paragraph openers that are connectors (assembly-line skeleton)
    openers = sum(1 for p in body if p.startswith(tuple(rules["connector_opener_terms"])))
    if openers > lim["connector_openers"]:
        _find(findings, "connector_openers", "soft",
              f"{openers}个段落以连接词开头，建议≤{lim['connector_openers']}；其余段落直接以论点句/场景句/设问开头")

    # --- parallelism & rhythm
    runs = parallelism_runs(body)
    if runs > lim["parallelism_runs"]:
        _find(findings, "parallelism", "soft", f"排比/同首字连排{runs}处，建议≤{lim['parallelism_runs']}")
    sl = sentence_lengths(body)
    stdev = statistics.pstdev(sl) if len(sl) >= 2 else 0.0
    if len(sl) >= 8 and stdev < lim["min_sentence_len_stdev"]:
        _find(findings, "rhythm_flat", "soft", f"句长标准差仅{stdev:.1f}，句子长短过于均匀")

    # --- keywords
    kw_report = {}
    for kw in keywords or []:
        n = body_text.count(kw)
        kw_report[kw] = {"body": n, "in_title": bool(t and kw in t)}
        if n < 2:
            _find(findings, "keyword_low", "soft", f"题眼“{kw}”正文仅出现{n}次，应至少2次")

    perr = punct_errors(body)
    if perr > 3:
        _find(findings, "punct_errors", "soft", f"标点错误{perr}处（>3处酌情扣分）")

    report = {
        "mode": mode,
        "title": t,
        "metrics": {
            **cc,
            "paragraphs": len(body),
            "paragraph_chars": plen,
            "however": however,
            "exclamations": excl,
            "dashes": dashes,
            "signature": sig_counts,
            "parallelism_runs": runs,
            "connector_openers": openers,
            "sentence_len_mean": round(statistics.mean(sl), 1) if sl else 0,
            "sentence_len_stdev": round(stdev, 1),
            "keywords": kw_report,
            "punct_errors": perr,
        },
        "findings": findings,
    }
    report["passed"] = not any(f["level"] == "hard" for f in findings)

    if mode == "draft":
        mn = lr["exam_minimum"]
        per = lr["deduct_per_chars"]
        report["deductions"] = {
            "no_title": 2 if not t else 0,
            "length_shortfall_with_punct": math.ceil(max(0, mn - cc["with_punct"]) / per),
            "length_shortfall_without_punct": math.ceil(max(0, mn - cc["without_punct"]) / per),
            "punct_errors_over_3": perr > 3,
            "note": "依据公开转载的上海细则扣分项：无标题-2；不足字数每少50字-1；标点错误>3处酌情；错别字1个-1(上限5，本脚本不判定，交由通读)。字数口径(含/不含标点)官方未确认，故两种都给。",
        }
        if title is not None:
            first_line = next((ln for ln in text.replace("\r", "").split("\n") if ln.strip()), "")
            report["metrics"]["title_matches_fixed"] = _clean_title(first_line) == _clean_title(title)
        table = []
        for i, p in enumerate(body, 1):
            table.append({
                "index": i,
                "chars": plen[i - 1],
                "head": p[:24],
                "however": sum(p.count(w) for w in rules["however_terms"]),
                "dashes": p.count("——"),
                "signature": [ph for ph in rules["signature_phrases"] if not ph.startswith("_") and ph in p],
                "keywords": {kw: p.count(kw) for kw in (keywords or [])},
            })
        report["paragraphs"] = table
    return report


# ------------------------------------------------------------------- diff
def diff_essays(old_text: str, new_text: str) -> dict:
    ot, ob = split_title_body(old_text)
    nt, nb = split_title_body(new_text)
    sm = difflib.SequenceMatcher(None, ob, nb, autojunk=False)
    paras = []
    removed = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(j2 - j1):
                paras.append({"new_index": j1 + k + 1, "old_index": i1 + k + 1, "status": "unchanged", "similarity": 1.0})
        elif tag == "insert":
            for k in range(j1, j2):
                paras.append({"new_index": k + 1, "old_index": None, "status": "added", "similarity": 0.0})
        elif tag == "delete":
            for k in range(i1, i2):
                removed.append({"new_index": None, "old_index": k + 1, "status": "removed", "similarity": 0.0})
        else:  # replace: pair positionally
            n_old, n_new = i2 - i1, j2 - j1
            for k in range(max(n_old, n_new)):
                if k < n_old and k < n_new:
                    s = difflib.SequenceMatcher(None, ob[i1 + k], nb[j1 + k], autojunk=False).ratio()
                    paras.append({"new_index": j1 + k + 1, "old_index": i1 + k + 1, "status": "modified", "similarity": round(s, 3)})
                elif k < n_new:
                    paras.append({"new_index": j1 + k + 1, "old_index": None, "status": "added", "similarity": 0.0})
                else:
                    removed.append({"new_index": None, "old_index": i1 + k + 1, "status": "removed", "similarity": 0.0})
    old_body, new_body = "\n".join(ob), "\n".join(nb)
    ratio = difflib.SequenceMatcher(None, old_body, new_body, autojunk=False).ratio() if (old_body or new_body) else 1.0
    return {
        "title_unchanged": _clean_title(ot or "") == _clean_title(nt or ""),
        "old_title": ot,
        "new_title": nt,
        "changed_ratio": round(1 - ratio, 3),
        "old_chars": count_chars(old_body)["with_punct"],
        "new_chars": count_chars(new_body)["with_punct"],
        "paragraphs": paras + removed,
    }


# ----------------------------------------------------------------- claims
def extract_claims(text: str, rules: dict | None = None) -> list[dict]:
    rules = rules or load_rules()
    min_q = rules["claims"]["min_quote_chars"]
    stop = set(rules["claims"]["speaker_stoplist"])
    t, body = split_title_body(text)
    out: list[dict] = []

    def add(kind, txt, para):
        out.append({"id": f"C{len(out) + 1}", "kind": kind, "text": txt, "para": para})

    for i, p in enumerate(body, 1):
        for m in re.finditer(r"《([^》]{1,30})》", p):
            add("work_title", m.group(1), i)
        for m in re.finditer(r"“([^”]{%d,})”" % min_q, p):
            add("quote", m.group(1), i)
        for m in re.finditer(r"(\d{3,4})年", p):
            add("year", m.group(0), i)
        for m in re.finditer(r"\d+(?:\.\d+)?\s?(?:%|％|万|亿|千|百|倍|个|人|次|项|岁|米|公里|元)", p):
            add("number", m.group(0), i)
        for m in re.finditer(r"([一-龥·]{2,4}?)(?:说|曰|云|写道|指出|认为|提出|称)", p):
            name = m.group(1)
            if name not in stop and len(name) >= 2:
                add("speaker", name, i)
    return out


# -------------------------------------------------------------------- CLI
def _render(report: dict) -> str:
    m = report["metrics"]
    lines = [
        f"标题：{report['title'] or '（无）'}",
        f"字数：含标点 {m['with_punct']} / 不含标点 {m['without_punct']}；{m['paragraphs']} 段；各段 {m['paragraph_chars']}",
        f"然而/但是 {m['however']}；感叹号 {m['exclamations']}；破折号 {m['dashes']}；排比 {m['parallelism_runs']}；句长均值/标准差 {m['sentence_len_mean']}/{m['sentence_len_stdev']}；标点错误 {m['punct_errors']}",
    ]
    sig = {k: v for k, v in m["signature"].items() if v}
    if sig:
        lines.append("口头禅计数：" + "，".join(f"{k}×{v}" for k, v in sig.items()))
    for f in report["findings"]:
        lines.append(f"[{'HARD' if f['level'] == 'hard' else 'soft'}] {f['msg']}" + (f"（{f['where']}）" if f["where"] else ""))
    if "deductions" in report:
        d = report["deductions"]
        lines.append(f"扣分预估：无标题 -{d['no_title']}；字数缺额 含标点口径 -{d['length_shortfall_with_punct']} / 不含标点口径 -{d['length_shortfall_without_punct']}")
    lines.append("结果：" + ("通过" if report["passed"] else "未通过（有 HARD 项）"))
    return "\n".join(lines)


def _read(path: str) -> str:
    with open(path, encoding="utf8") as f:
        return f.read()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Shanghai gaokao essay checker (reports only).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("write", "draft"):
        sp = sub.add_parser(name)
        sp.add_argument("essay")
        sp.add_argument("--rules")
        sp.add_argument("--keywords", default="")
        sp.add_argument("--json", action="store_true")
        if name == "draft":
            sp.add_argument("--title", help="user-fixed title that must stay unchanged")
    sp = sub.add_parser("diff")
    sp.add_argument("old")
    sp.add_argument("new")
    sp = sub.add_parser("claims")
    sp.add_argument("essay")
    sp.add_argument("--rules")
    args = ap.parse_args(argv)
    try:
        if args.cmd in ("write", "draft"):
            rules = load_rules(args.rules)
            kws = [k for k in args.keywords.split(",") if k]
            rep = analyze(_read(args.essay), rules, mode=args.cmd, keywords=kws, title=getattr(args, "title", None))
            print(json.dumps(rep, ensure_ascii=False, indent=2) if args.json else _render(rep))
            return 0 if rep["passed"] else 1
        if args.cmd == "diff":
            print(json.dumps(diff_essays(_read(args.old), _read(args.new)), ensure_ascii=False, indent=2))
            return 0
        if args.cmd == "claims":
            print(json.dumps(extract_claims(_read(args.essay), load_rules(args.rules)), ensure_ascii=False, indent=2))
            return 0
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
