# Plan: PR Preview for InspectAI Eval Results

## Problem

When reviewing PRs that modify skills or evals, reviewers currently only see a
markdown summary table in the PR comment (pass/fail per sample). The full
interactive InspectAI viewer — with detailed traces, scores, model outputs, and
scorer explanations — is only available on the main branch deployment at
`https://statik.github.io/skills/` after merging.

This makes it hard to assess eval quality before merging. Reviewers need to
either download the artifact ZIP and run `inspect view` locally, or trust the
summary table alone.

## Goal

Deploy a per-PR preview of the InspectAI HTML viewer so reviewers can click a
link in the PR comment and immediately explore full eval results interactively.

## Approach

Use [`rossjrw/pr-preview-action`](https://github.com/marketplace/actions/deploy-pr-preview)
to deploy the `inspect view bundle` output to GitHub Pages under
`pr-preview/pr-{number}/` for each PR. Clean up previews when PRs close.

**Preview URL pattern:** `https://statik.github.io/skills/pr-preview/pr-{number}/`

## Changes Required

### 1. Modify `validate-skills.yml` — Add preview deployment

**File:** `.github/workflows/validate-skills.yml`

#### a) Update triggers to include PR close events

The pr-preview-action needs the `closed` event to clean up previews:

```yaml
on:
  pull_request:
    branches: [main]
    types: [opened, reopened, synchronize, closed]
```

#### b) Update permissions

The action needs write access to push to the `gh-pages` branch:

```yaml
permissions:
  contents: write    # was: read — needed for gh-pages push
  pull-requests: write
```

#### c) Add concurrency group

Prevent race conditions when multiple pushes happen quickly on the same PR:

```yaml
concurrency: preview-${{ github.ref }}
```

#### d) Add `inspect view bundle` step to `run-evals` job

After the existing "Run InspectAI evals" step, generate the static HTML bundle:

```yaml
- name: Generate eval viewer bundle
  if: env.SKIP_EVALS != 'true'
  working-directory: evals
  run: |
    uv run inspect view bundle \
      --log-dir ./logs \
      --output-dir ../pr-preview-site \
      --overwrite
    touch ../pr-preview-site/.nojekyll
```

#### e) Add pr-preview-action step

Deploy the generated bundle to gh-pages under `pr-preview/pr-{number}/`:

```yaml
- name: Deploy PR preview
  if: always()
  uses: rossjrw/pr-preview-action@v1
  with:
    source-dir: ./pr-preview-site/
    preview-branch: gh-pages
    umbrella-dir: pr-preview
    action: auto
    comment: false   # we handle our own comment (see below)
```

Setting `comment: false` because we already have a custom PR comment step. We'll
enhance it instead.

#### f) Enhance the PR comment with preview link

Update the "Comment on PR" step to include the preview link. Modify the Python
summary script to append a link:

```python
# At the end of the summary generation:
pr_number = os.environ.get("PR_NUMBER", "")
repo = os.environ.get("GITHUB_REPOSITORY", "")
if pr_number and repo:
    owner = repo.split("/")[0]
    repo_name = repo.split("/")[1]
    preview_url = f"https://{owner}.github.io/{repo_name}/pr-preview/pr-{pr_number}/"
    summary += f"\n**[View full eval results]({preview_url})**\n"
```

Pass the PR number as an environment variable:

```yaml
env:
  PR_NUMBER: ${{ github.event.pull_request.number }}
  GITHUB_REPOSITORY: ${{ github.repository }}
```

### 2. Modify `publish-evals.yml` — Stop force-pushing gh-pages

**File:** `.github/workflows/publish-evals.yml`

The current deployment does `git push -f` to gh-pages, which **destroys all PR
preview directories**. The pr-preview-action docs explicitly warn about this.

#### Option A (Recommended): Use `JamesIves/github-pages-deploy-action`

Replace the manual git-push-based deploy with a managed action that supports
excluding directories from cleanup:

```yaml
- name: Deploy to gh-pages
  uses: JamesIves/github-pages-deploy-action@v4
  with:
    branch: gh-pages
    folder: site
    clean: true
    clean-exclude: pr-preview/
    force: false
```

This preserves the `pr-preview/` directory while replacing all other content.

#### Option B (Alternative): Manual deploy with preservation

If preferring to avoid another third-party action, manually preserve the
`pr-preview/` directory:

```yaml
- name: Deploy to gh-pages
  run: |
    cd site
    git init
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"

    # Fetch existing gh-pages to preserve pr-preview/
    git remote add origin https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}.git
    git fetch origin gh-pages || true
    git checkout -b gh-pages

    # Restore pr-preview directory from existing gh-pages
    git checkout origin/gh-pages -- pr-preview/ 2>/dev/null || true

    git add -A
    git commit -m "Update eval results - $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    git push -f origin gh-pages
```

### 3. Repository Settings (one-time manual step)

Verify these settings are configured:

1. **GitHub Pages source:** Settings → Pages → "Deploy from a branch" → `gh-pages` / `/ (root)`
2. **Workflow permissions:** Settings → Actions → General → "Read and write permissions" enabled

These should already be configured since `publish-evals.yml` currently deploys
to gh-pages, but worth verifying.

## Implementation Order

1. **Modify `publish-evals.yml` first** — Switch to non-destructive deployment
   so existing gh-pages content strategy is safe. Merge this to main.
2. **Modify `validate-skills.yml`** — Add the bundle generation and
   pr-preview-action steps. This can be tested on a PR itself.
3. **Verify** — Open a test PR, confirm the preview deploys and the link works.

## Considerations

### Eval skipping on closed PRs

When a PR is closed, the `run-evals` job should not re-run evals. The
pr-preview-action with `action: auto` handles this — it detects the `closed`
event and only runs the cleanup (removal) step. However, we should gate the
expensive eval steps to not run on close:

```yaml
- name: Run InspectAI evals
  if: env.SKIP_EVALS != 'true' && github.event.action != 'closed'
```

### gh-pages branch size

Each PR preview includes a full InspectAI HTML bundle (~a few MB). With many
open PRs, this could grow. The pr-preview-action automatically cleans up on PR
close, so this is self-managing. For extra safety, we could add a scheduled
workflow to prune stale previews.

### Fork PRs

`rossjrw/pr-preview-action@v1` does not support fork PRs (no write access to
gh-pages). This is a known limitation. Fork PRs will still get the markdown
summary comment but not the interactive preview. A v2 of the action with fork
support is planned upstream.

### Cost

The eval run itself is already happening in the PR workflow. The additional
`inspect view bundle` step is a local HTML generation step (no API calls, runs
in seconds). The only new cost is the gh-pages push, which is minimal.

### Wait for deployment

Consider setting `wait-for-pages-deployment: true` on the pr-preview-action so
the comment link is guaranteed to work when posted. This adds ~30-60 seconds
but prevents broken links.

## Summary of File Changes

| File | Change |
|------|--------|
| `.github/workflows/validate-skills.yml` | Add PR close trigger, update permissions, add concurrency, add bundle generation step, add pr-preview-action step, enhance PR comment with preview link |
| `.github/workflows/publish-evals.yml` | Replace force-push deploy with `JamesIves/github-pages-deploy-action` (or manual preservation of `pr-preview/`) |

No changes needed to eval code, scorers, Justfile, or skill definitions.
