# Changelog

## shanghai-gaokao-essay v2 (branch `feat/essay-v2`, 2026-10-18)

### Added
- **Four-mode router** (SKILL.md): W write · O outline (审题 / 立意 candidates scored / outline / verified materials, no essay) · O 立意打磨 · R revise (diagnosis by default; local edit on request, title fixed).
- **Evidence ledger + source tiers** (`references/search-enhancement.md`, `assets/evidence-ledger.md`): every named person, work, event, number and quotation in an essay must map to a verified ledger row before delivery; searches are done before drafting.
- **`scripts/check_essay.py`** (stdlib only, reports only): `write`, `draft`, `diff`, `claims`; 46 unit tests; rules in `assets/lint-rules.json`.
- **De-template pass** (`references/de-template.md`, Step 3.5), distilled from Humanizer-zh (MIT) and adapted to argumentative exam essays.
- **evidence-bank fully fact-checked** (51 entries): 36 kept, 10 paraphrase-only, 5 corrected; per-entry 〔直引〕/〔转述〕/〔修正〕 tags; fake-quote blocklist; full audit trail in `assets/evidence-audit.json`.
- **`assets/past-prompts.md`**: 上海卷 2011–2026 with provenance (2017–2025 string-matched against shmeea.edu.cn).
- Test fixtures: `tests/baseline_v1/` (old skill), `tests/eval_v2/` (new skill, outlines, revisions with planted-defect drafts and answer key), `tests/eval_convergence.py`.

### Changed
- `exemplar-outline.md`: full-text paragraph examples removed (one reference paragraph kept); outlines no longer carry the old stock phrases.
- `language-and-style.md`, `structure-and-outline.md`: fixed stock phrases ("诚然 / 更值得警惕的是 / 归根结底 / 由此看来 / 真正的X") replaced by the *function* plus rotating options.
- `prompt-analysis.md`: adds type E (寓言设喻); the claim "审题偏差直接封顶52分" corrected to the published rubric wording (三类 39–51 / 四类 21–38).
- Length rule: recommended 900–1000 (with punctuation), hard 900–1100; for student drafts the hard line is the official 800.
- 五段骨架 / 六段 / 6–8 段 wording unified.

### Fixed (found during evaluation)
- `claims` missed well-known names and produced "speaker" noise; now uses a name list, requires a quote after "X说", and can check against a ledger (`--ledger`).
- Punctuation errors are now located (paragraph + snippet), including unclosed 书名号 and ASCII quotes; previously only a count was reported, and a revising agent left one in.
- `diff` now reports `old_sentences_changed_ratio` (how many original sentences were touched). The character-level ratio badly under-reports edits that add sentences (0.176 vs 0.481 for one test edit).

### Evaluation (small, single-run; treat as directional)
**Write mode, 5 prompts (A–E types), old vs new** (`tests/eval_convergence.py`):

| | old | new |
|---|---|---|
| paragraph openers shared by all essays at the same position | 5/5 (para 2 "诚然", para 5 "由此看来") | 0/5 |
| tic-phrase hits (诚然 / 更值得警惕的是 / 归根结底 / 由此看来 / 渡口) | 18 | 0 |
| 5-grams shared by ≥ half of essays | 10 | 0 |
| essays with hard script findings | 1 (banned word "赋能") | 0 |

Caveat: the new essays were written with the linter visible, so this measures compliance with the new rules, not whether the essays read better or score higher. No blind human comparison has been done yet.

**Revise mode, 3 synthetic drafts with planted defects:** both factual defects (an invented 鲁迅 quotation; 《题西林壁》 credited to 黄庭坚) were caught and fixed, the correct 苏轼 example was kept, titles stayed unchanged; the concept-drift and "three parallel legs" draft was diagnosed correctly. Misses: the edit of draft 3 left 2 of 4 planted stock-phrase openers and 1 ASCII quote, and by the sentence-level metric changed 48% of the original sentences (over the 40% budget; the agent had reported the character ratio of 0.18); draft 2's missing concession/boundary layer was only patched with one sentence (the agent said so and explained it needs L3 work).

**Outline mode, 3 prompts:** all three produced the full deliverable with no essay text; evaluator feedback led to the tie-break, absorption and exam-version size rules.

### Known limitations
- Nothing here guarantees passing an AI detector or a higher exam score.
- 15 of 82 evidence-bank source claims could not be re-fetched automatically (non-ASCII URL encoding / anti-bot); they rest on subagent reports.
- 2011–2016 prompt wordings come from secondary sources and differ slightly between outlets; 2026 was transcribed from an image on shmeea.edu.cn.
- Whether punctuation counts toward the word limit is unconfirmed from official sources; both counts are reported.
- `check_essay.py` cannot judge typos, fake quotations, mismatched attributions, or concept drift; these rely on the model's reading and on search.
- Sub-band cut points (二类上 59–62, 二类中 55–58, 二类下 52–54) come from several consistent public reposts of the rubric, not from the exam authority itself.
