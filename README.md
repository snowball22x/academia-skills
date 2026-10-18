# academia-skills

Agent skills (SKILL.md format) for academic and exam writing.

## shanghai-gaokao-essay

Writes, outlines and revises 上海高考 argumentative essays (材料作文/思辨议论文, 800+ 字), aiming at the 一类卷 lower bound (63–66 / 70) with a "中规中矩 + 思想深刻" strategy.

### Four modes

| You give it | Mode | You get |
|---|---|---|
| A prompt, and want an essay | **W** write | Full essay + evidence ledger + self-check |
| A prompt, and want ideas / outline / materials | **O** outline | 审题结论, 3 scored 立意 candidates, outline, verified materials (no essay) |
| A prompt + your own 立意 | **O** · 立意打磨 | Evaluation of your angle, how to deepen it, alternatives |
| A prompt + fixed title + your draft | **R** revise | Diagnosis (default) with fact-check of your cited quotes, or — if you ask — a local edit that keeps your title and stays within ≤40% change |

### Layout

```
shanghai-gaokao-essay/
├── SKILL.md                      router + hard rules
├── references/                   loaded on demand (审题, 提纲, 语言, de-template, search/evidence, revision, outline mode…)
├── assets/                       evidence-bank audit trail, ledger / report templates, past prompts 2011–2026, lint rules
├── scripts/check_essay.py        deterministic checks (stdlib only): write / draft / diff / claims
└── tests/                        unit tests, v1 baseline essays, v2 evaluation outputs, convergence evaluator
```

### Using the script

```bash
python scripts/check_essay.py write essay.md --keywords 题眼1,题眼2   # fresh essay: length (with/without punct), banned terms, tics…
python scripts/check_essay.py draft student.md --title "固定标题"      # student draft: deduction estimate, per-paragraph table
python scripts/check_essay.py diff old.md new.md                        # how much did an edit change?
python scripts/check_essay.py claims essay.md --ledger ledger.md       # every quote/title/number/name must be in the ledger
python -m unittest discover -s tests                                    # run the tests
```

The script reports only; it never rewrites. Without code execution the skill falls back to manual checklists. Without web search it uses only the verified `evidence-bank.md`.

### Credits and limits

- De-template rules are distilled from [op7418/Humanizer-zh](https://github.com/op7418/humanizer-zh) (MIT), itself based on blader/humanizer, hardikpandya/stop-slop and Wikipedia "Signs of AI writing".
- Nothing here guarantees passing an AI detector or a higher exam score; see `CHANGELOG.md` for what was and wasn't measured.