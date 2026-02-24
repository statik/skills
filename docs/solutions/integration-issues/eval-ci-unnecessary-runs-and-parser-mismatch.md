---
title: "Eval CI runs on every PR, runs twice on merge, and summary always shows 0 correct"
date: 2026-02-18
category: integration-issues
tags:
  - ci
  - github-actions
  - eval
  - cost-optimization
  - branch-protection
  - inspect-ai
severity: medium
component: GitHub Actions CI workflows (validate-skills.yml, publish-evals.yml)
symptoms:
  - "Eval CI job runs on every PR even when no skill, eval, or Justfile changes are made"
  - "Eval CI runs twice on merge to main: once in validate-skills and once in publish-evals"
  - "PR eval summary comment always shows 0 correct / 0 incorrect for every skill"
  - "Every eval sample is marked as WARN in the PR comment regardless of actual results"
  - "Unnecessary LLM API costs from redundant and irrelevant eval runs"
  - "Using workflow-level path filters causes the required status check to never report, blocking PR merges"
root_cause: "Three independent issues: (1) No path filtering on eval workflows, so evals ran for all PRs. (2) Both validate-skills and publish-evals triggered evals on merge to main, causing duplicate runs. (3) The eval summary parser hardcoded 'model_graded_fact' as the scorer key, but the actual scorers use names like 'diagnosis_match' and 'skill_not_triggered', so scores were never found and defaulted to zero."
---

## Problem

Three interrelated CI issues caused wasted API costs and broken eval reporting:

**Unnecessary eval runs on unrelated PRs.** Every pull request triggered the full eval suite, even when the changes only touched documentation, configuration, or code outside the `skills/`, `evals/`, or `Justfile` paths. Since evals invoke LLM APIs, this generated avoidable costs.

**Duplicate eval runs on merge.** When a PR was merged to main, both `validate-skills.yml` (on push) and `publish-evals.yml` (on push) independently ran the eval suite, doubling the API spend for every merge.

**Eval summary always showing zeros.** The PR comment posted by the eval workflow displayed "0 correct / 0 incorrect" for every skill, with all individual samples marked as WARN. The summary parser looked for a scorer key called `model_graded_fact` in the eval results JSON, but the actual scorers were named `diagnosis_match`, `skill_not_triggered`, and similar domain-specific names. Since no score was found under the hardcoded key, every result fell through to the default zero/warning state.

**Branch protection deadlock with path filters.** An initial attempt to fix the first issue by adding workflow-level `paths:` filters caused a new problem: when a PR didn't touch the filtered paths, the workflow never ran at all, so the required status check never reported. This blocked PRs from merging.

## Root Cause

1. **No path filtering** on eval workflows, so every PR paid the full eval cost regardless of what changed.
2. **Both workflows triggered on push to main**, causing the same evals to run twice per merge.
3. **Hardcoded scorer name** in the summary parser (`model_graded_fact`) didn't match actual InspectAI scorer names (`diagnosis_match`, `skill_not_triggered`, etc.).
4. **Workflow-level `paths:` filters** prevent the workflow from running entirely, which means required status checks never report, making PRs unmergeable.

## Solution

### Step 1: Move path filtering inside the job

Instead of using workflow-level `paths:` filters (which prevent the workflow from running entirely), filtering happens as the first step of the `run-evals` job. It uses `gh pr diff` to check whether any changed files match relevant paths. If none do, it sets `SKIP_EVALS=true` in the GitHub Actions environment. All subsequent steps are conditioned on this variable. The job always runs and reports a status (satisfying branch protection), but skips expensive work when unnecessary.

```yaml
- name: Check for relevant changes
  if: github.event.action != 'closed'
  env:
    GH_TOKEN: ${{ github.token }}
    PR_NUMBER: ${{ github.event.pull_request.number }}
  run: |
    CHANGED_FILES=$(gh pr diff "$PR_NUMBER" --name-only)
    if echo "$CHANGED_FILES" | grep -qE '^(skills/|evals/|Justfile$)'; then
      echo "Relevant changes detected, evals will run"
    else
      echo "No relevant changes — skipping evals"
      echo "SKIP_EVALS=true" >> "$GITHUB_ENV"
    fi
```

When evals are skipped, the job still writes a summary and posts a PR comment indicating "Skipped (no relevant changes)" so reviewers have visibility.

### Step 2: Eliminate duplicate runs via artifact forwarding

The `publish-evals.yml` workflow (triggered on push to main) no longer re-runs evals. Instead, it locates the merged PR, finds the successful `validate-skills.yml` run for that PR's branch, and downloads the eval artifacts directly.

```bash
PR_NUMBER=$(gh api "/repos/$GITHUB_REPOSITORY/commits/$GITHUB_SHA/pulls" \
  --jq '.[0].number')
PR_BRANCH=$(gh pr view "$PR_NUMBER" \
  --json headRefName --jq '.headRefName')
RUN_ID=$(gh run list \
  --workflow validate-skills.yml \
  --branch "$PR_BRANCH" \
  --status completed \
  --limit 5 \
  --json databaseId,conclusion \
  --jq '[.[] | select(.conclusion=="success")] | .[0].databaseId')
gh run download "$RUN_ID" \
  --name inspect-eval-logs \
  --dir ./pr-eval-artifacts
```

A fallback path handles direct pushes to main and `workflow_dispatch` triggers by running evals fresh when no prior artifact is available.

### Step 3: Fix the eval summary parser

Instead of hardcoding `model_graded_fact`, the parser reads whatever scorer is present by taking the first value from the scores dictionary.

```python
def get_primary_value(sample):
    scores = sample.get("scores", {})
    if not scores:
        return "?"
    first_score = next(iter(scores.values()))
    return first_score.get("value", "?")
```

This works regardless of scorer name, restoring accurate correct/incorrect counts in PR comments.

## Prevention

### Path filters and required status checks are incompatible at the workflow trigger level

GitHub skips the entire workflow if paths don't match, so the required check never posts a status. The correct pattern: keep the workflow trigger broad, add a step inside the job that checks changed files and sets an output variable, then condition subsequent steps on that output.

### Deduplicate expensive work across workflow triggers

Merging a PR fires both the PR completion event and a push event to the target branch. Any work triggered by both events executes twice. Design for this: one workflow owns the expensive execution, others consume its artifacts.

### Parse data by structure, not by assumed constants

When consuming structured output from external tools (InspectAI, pytest, etc.), read keys dynamically from the data rather than hardcoding them. Different eval tasks produce different scorer names; the parser must handle all of them.

### Gate paid API calls explicitly

Any CI job that calls a paid API should have a documented cost-control mechanism. Path filtering, artifact reuse, and conditional execution are the three primary levers.

## Lessons Learned

1. **Merging a PR is a double event.** GitHub fires both PR completion and push-to-main. Workflows triggered by both will run twice. This is documented behavior, not a bug.
2. **"Runs on every PR" is the wrong default for expensive jobs.** Require an explicit trigger condition rather than relying on the absence of a skip condition.
3. **The first integration test is never enough.** The parser worked for the first eval task tested. When a second task used a different scorer, it broke silently. Test with multiple configurations.
4. **CI costs from API calls are invisible until tracked.** Without explicit monitoring, teams don't notice doubling until the bill arrives.

## Cross-References

- `docs/plan-pr-preview-evals.md` -- original plan for PR preview deployment and eval architecture
- `AGENTS.md` (lines 118-125) -- documents that both `validate` and `run-evals` must pass for merge
- `CONTRIBUTING.md` (lines 131-132) -- documents that CI automatically runs evals on PRs
- PR #28, #27 -- the PRs that implemented these fixes
- PR #25, #24, #5 -- earlier eval CI fixes
