#!/usr/bin/env python3
"""Cross-essay convergence report: do essays written with this skill share the same verbal tics and paragraph skeleton?

Usage: python tests/eval_convergence.py tests/baseline_v1/p*_essay.md
Reports (stdlib only):
  - per-paragraph opener table (first clause before the first comma)
  - for each paragraph index, how many essays open with the same connector word
  - phrases (5-grams) shared by >= ceil(N/2) essays
  - signature-phrase coverage across essays
"""
import collections
import json
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(os.path.dirname(HERE), "assets", "lint-rules.json")
CONNECTORS = ["诚然", "可是", "然而", "但是", "更值得警惕的是", "由此看来", "归根结底", "于是", "问题在于", "流行的一种看法是", "如今", "与其"]


def body(path):
    lines = [ln.strip() for ln in open(path, encoding="utf8").read().replace("\r", "").split("\n") if ln.strip()]
    return lines[0], lines[1:]


def grams(text, n=5):
    t = re.sub(r"[\s，。！？；：、“”《》（）…—]", "", text)
    return {t[i:i + n] for i in range(len(t) - n + 1)}


def main(paths):
    essays = {os.path.basename(p): body(p) for p in paths}
    n = len(essays)
    print(f"essays: {n}")
    print("\n[paragraph opener connector by paragraph index]")
    maxp = max(len(b) for _, b in essays.values())
    worst = 0
    for i in range(maxp):
        c = collections.Counter()
        for _, b in essays.values():
            if i < len(b):
                hit = next((w for w in CONNECTORS if b[i].startswith(w)), None)
                if hit:
                    c[hit] += 1
        if c:
            w, k = c.most_common(1)[0]
            worst = max(worst, k)
            print(f"  para {i + 1}: '{w}' opens {k}/{n} essays")
    print(f"  => max same-opener agreement at one paragraph position: {worst}/{n}")
    print("\n[phrases shared by >= half of the essays]")
    G = [grams("".join(b)) for _, b in essays.values()]
    c = collections.Counter(g for s in G for g in s)
    thr = math.ceil(n / 2)
    shared = sorted(g for g, k in c.items() if k >= thr)
    print(f"  {len(shared)} five-grams; sample: {shared[:12]}")
    rules = json.load(open(RULES, encoding="utf8"))
    print("\n[signature phrases: number of essays containing each]")
    total = 0
    for ph in rules["signature_phrases"]:
        if ph.startswith("_"):
            continue
        k = sum(1 for _, b in essays.values() if ph in "".join(b))
        if k:
            print(f"  {ph}: {k}/{n}")
        if ph in ("更值得警惕的是", "诚然", "归根结底", "由此看来", "渡口"):
            total += k
    print(f"  => tic-phrase hits (5 tics, summed over essays): {total}")


if __name__ == "__main__":
    main(sys.argv[1:])
