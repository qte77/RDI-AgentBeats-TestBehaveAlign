# Ralph Loop Learnings

<!-- markdownlint-disable MD024 MD025 -->

## 1. Story Completion

- [ ] AC tests behavior, not shape ("returns score>20" not "returns dict")
- [ ] Integration story exists after every 3-5 component stories
- [ ] No orphaned modules — all components wired
- [ ] Wiring verified behaviorally: if A returns X, B produces expected Y
- [ ] Smoke test passes (E2E flow works end-to-end)
- [ ] `generate_prd_json.py --dry-run` AC/files counts match expectations

## 2. PRD Parser

`generate_prd_json.py` silently drops content not matching its regex.

| Constraint | Fix |
| --- | --- |
| One `#####` heading per story | Split combined headings into separate ones |
| Top-level `- [ ]` only | Flatten indented sub-items to individual checkboxes |
| Sub-feature needs own `**Files**:` | Add per-sub-feature, remove parent's |
| Parser copies parent description | Fix manually in prd.json + rehash |

```text
BAD:  - [ ] Module with:        ← parser sees 1 item
        - helper_a()
        - helper_b()
GOOD: - [ ] Module created       ← parser sees 3 items
      - [ ] helper_a()
      - [ ] helper_b()
```

## 3. Platform Integration

- [ ] Study reference implementation BEFORE coding
- [ ] Extract exact interface contract (CLI args, ports, response format)
- [ ] Default configuration (ports, timeouts) matches platform defaults
- [ ] Entry point pattern matches platform's invocation method
- [ ] Add explicit integration story to verify against platform tooling
- [ ] Test with platform's orchestration tools, not local equivalents

## 4. Worktree Merge

```bash
# After Ralph completes (from main repo)
git merge --squash ralph/<branch>
git commit -m "feat(sprintN): implement stories via Ralph"
git worktree remove ../<worktree-dir>
git branch -d ralph/<branch>
```

- [ ] Squash merge — collapses RED/GREEN/REFACTOR noise into one revertable commit
- [ ] Don't edit `prd.json` story files on source branch while Ralph runs
- [ ] After `-X ours` conflict resolution, `git rm` files added exclusively by the other branch

## 5. Story Scope

PRD `files` lists often miss pre-existing tests asserting on renamed symbols or changed output.

- [x] Grep full test tree for renamed/changed symbols before implementation; add consuming files to story scope
- [x] Exit codes 137/143 (SIGTERM/OOM) = inconclusive, not PASS — retry or flag
- [ ] After each story, run `uv run pytest --inline-snapshot=review` to surface stale snapshots
- [ ] Flag source files with tests in multiple directories — consolidate to prevent oversight
- [ ] Post-story: run tests importing changed modules specifically, not just full suite
