"""Tier-2 InspectAI eval for design-memo skill (LOCAL ONLY — costs LLM calls).

Runs the Claude Code CLI in a tempdir with the design-memo skill installed,
issues prompts that should (or should not) trigger the skill, then validates
any produced HTML with the deterministic scorers in html_scorers.py.

No LLM-as-judge — every check is deterministic. The CLI invocation is the
only LLM cost.

Environment Variables:
    DESIGN_MEMO_TIMEOUT: CLI timeout in seconds (default: 180)
    CLAUDE_BIN: Path to Claude CLI binary (default: 'claude')
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import ChatMessageAssistant, ModelOutput
from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Scorer,
    Target,
    accuracy,
    scorer,
    stderr,
)
from inspect_ai.solver import Solver, TaskState, solver

import html_scorers as hs

SKILL_PATH = Path(__file__).parent.parent / "design-memo" / "skills" / "design-memo"
CLI_TIMEOUT = int(os.environ.get("DESIGN_MEMO_TIMEOUT", "180"))
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")


# ---------- solver ----------


@dataclass
class MemoRun:
    response: str
    memo_path: str | None
    memo_html: str
    success: bool


def _setup_skill(work_dir: Path) -> None:
    skill_dest = work_dir / ".claude" / "skills" / "design-memo"
    skill_dest.parent.mkdir(parents=True, exist_ok=True)
    if skill_dest.exists():
        shutil.rmtree(skill_dest)
    shutil.copytree(SKILL_PATH, skill_dest)
    # Pre-create the documented default output directory so the skill writes
    # there without needing user confirmation in non-interactive mode.
    (work_dir / "design-memos").mkdir(exist_ok=True)


def _find_memo(work_dir: Path) -> Path | None:
    matches = [
        p
        for p in work_dir.rglob("*-design-memo.html")
        if ".claude" not in p.parts
    ]
    return matches[0] if matches else None


def _run_claude(prompt: str, work_dir: Path, model: str | None) -> MemoRun:
    cmd = [
        CLAUDE_BIN,
        "--print",
        "--dangerously-skip-permissions",
        "--output-format",
        "json",
    ]
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)

    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=CLI_TIMEOUT,
            env={
                **os.environ,
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
            },
        )
    except subprocess.TimeoutExpired:
        return MemoRun(f"timeout after {CLI_TIMEOUT}s", None, "", False)

    if result.returncode != 0:
        return MemoRun(
            f"claude exit {result.returncode}: {result.stderr}", None, "", False
        )

    try:
        trace = json.loads(result.stdout)
    except json.JSONDecodeError:
        trace = None

    response = ""
    if isinstance(trace, dict) and "result" in trace:
        response = trace["result"]
    elif isinstance(trace, list):
        for msg in reversed(trace):
            if msg.get("type") == "assistant":
                content = msg.get("content", [])
                texts = [
                    c.get("text", "") for c in content if c.get("type") == "text"
                ]
                response = "\n".join(texts)
                break

    memo_path = _find_memo(work_dir)
    memo_html = memo_path.read_text() if memo_path else ""
    return MemoRun(
        response=response or result.stdout,
        memo_path=str(memo_path.relative_to(work_dir)) if memo_path else None,
        memo_html=memo_html,
        success=True,
    )


@solver
def design_memo_solver(model: str | None = None) -> Solver:
    async def solve(state: TaskState, generate) -> TaskState:
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)
            _setup_skill(work_dir)

            run = await asyncio.to_thread(
                _run_claude, state.input_text, work_dir, model
            )

            state.metadata["memo_produced"] = run.memo_path is not None
            state.metadata["memo_path"] = run.memo_path
            state.metadata["memo_html"] = run.memo_html
            state.metadata["execution_success"] = run.success

            state.output = ModelOutput.from_content(
                model="claude-code", content=run.response
            )
            state.messages.append(ChatMessageAssistant(content=run.response))

        return state

    return solve


# ---------- scorers ----------


_STRUCTURE = (
    hs.html_parses,
    hs.semantic_layout,
    hs.palette_vars_defined,
    hs.ink_used_for_body,
    hs.print_media_query,
    hs.mobile_breakpoint,
)
_SELF_CONTAINED = (hs.no_external_assets, hs.inline_only)
_ACCESSIBILITY = (
    hs.wcag_aa_contrast,
    hs.focus_visible_styles,
    hs.reduced_motion_query,
    hs.progress_bar_aria,
    hs.rail_present,
    hs.chapter_indicator_live,
    hs.aria_keyshortcuts_in_js,
    hs.aria_current_step,
    hs.no_js_progressive,
    hs.keyboard_shortcuts,
    hs.editable_focus_guard,
)
_CODE_SAFETY = (hs.highlighter_escapes_html,)


def _evaluate_group(state: TaskState, group) -> Score:
    if not state.metadata.get("memo_produced"):
        return Score(
            value=CORRECT, answer="n/a", explanation="no memo to evaluate"
        )
    html = state.metadata.get("memo_html", "")
    results = [(fn.__name__, fn(html)) for fn in group]
    failures = [f"{name}: {r.detail}" for name, r in results if not r.passed]
    if not failures:
        return Score(
            value=CORRECT, answer="pass", explanation=f"all {len(group)} pass"
        )
    return Score(
        value=INCORRECT, answer="fail", explanation="; ".join(failures[:5])
    )


@scorer(metrics=[accuracy(), stderr()])
def memo_trigger() -> Scorer:
    """Did the agent produce a *-design-memo.html when expected?"""

    async def score(state: TaskState, target: Target) -> Score:
        produced = state.metadata.get("memo_produced", False)
        expected = state.metadata.get("expect_memo", True)
        if produced == expected:
            return Score(
                value=CORRECT,
                answer="produced" if produced else "skipped",
                explanation=f"trigger correct (expected={expected})",
            )
        if expected and not produced:
            return Score(
                value=INCORRECT,
                answer="missing",
                explanation="expected memo but none was created",
            )
        return Score(
            value=INCORRECT,
            answer="unexpected",
            explanation="memo created but trigger should have been declined",
        )

    return score


@scorer(metrics=[accuracy()])
def memo_quality() -> Scorer:
    """Composite: every deterministic check passes."""

    async def score(state: TaskState, target: Target) -> Score:
        return _evaluate_group(state, hs.ALL_SCORERS)

    return score


@scorer(metrics=[accuracy()])
def memo_structure() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        return _evaluate_group(state, _STRUCTURE)

    return score


@scorer(metrics=[accuracy()])
def memo_self_contained() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        return _evaluate_group(state, _SELF_CONTAINED)

    return score


@scorer(metrics=[accuracy()])
def memo_accessibility() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        return _evaluate_group(state, _ACCESSIBILITY)

    return score


@scorer(metrics=[accuracy()])
def memo_code_safety() -> Scorer:
    async def score(state: TaskState, target: Target) -> Score:
        return _evaluate_group(state, _CODE_SAFETY)

    return score


# ---------- samples ----------


POSITIVE_SAMPLES = [
    (
        "cdn-migration",
        "Plan the migration from CloudFront to Fastly for our static assets. "
        "Cover cache strategy, DNS cutover order, rollback, and observability.",
    ),
    (
        "auth-flow",
        "Design the authentication flow for a new mobile app: token issuance, "
        "refresh rotation, revocation, and session timeout policy.",
    ),
    (
        "database-sharding",
        "Architect a sharding strategy for a 50M-row orders table. Cover the "
        "shard key choice, routing layer, backfill, and rollback.",
    ),
    (
        "graphql-federation-adr",
        "Write a decision record for adopting GraphQL Federation across our "
        "backend services. Recommend a path and document alternatives.",
    ),
    (
        "payments-refactor",
        "Plan a refactor of our payment processing module to extract a "
        "vendor-agnostic interface so we can add a second payment provider.",
    ),
    (
        "rate-limiting",
        "Design the implementation approach for adding rate limiting to a "
        "public API: algorithm, storage, identity, error handling, and rollout.",
    ),
]

NEGATIVE_SAMPLES = [
    ("simple-math", "What is 47 * 23?"),
    ("typo-fix", "Fix the typo in this filename: redme.txt"),
    ("info-question", "Explain in two sentences what HTTPS is."),
]


def _build_samples(positive: bool = True, negative: bool = True) -> list[Sample]:
    samples: list[Sample] = []
    if positive:
        for sid, prompt in POSITIVE_SAMPLES:
            samples.append(
                Sample(
                    input=prompt,
                    target="produce HTML design memo",
                    metadata={
                        "sample_id": sid,
                        "category": "positive",
                        "expect_memo": True,
                    },
                )
            )
    if negative:
        for sid, prompt in NEGATIVE_SAMPLES:
            samples.append(
                Sample(
                    input=prompt,
                    target="do not produce HTML design memo",
                    metadata={
                        "sample_id": sid,
                        "category": "negative",
                        "expect_memo": False,
                    },
                )
            )
    return samples


# ---------- tasks ----------


def _scorers():
    return [
        memo_trigger(),
        memo_quality(),
        memo_structure(),
        memo_self_contained(),
        memo_accessibility(),
        memo_code_safety(),
    ]


@task
def design_memo_eval() -> Task:
    """Full end-to-end design-memo eval (positive + negative samples)."""
    return Task(
        dataset=MemoryDataset(samples=_build_samples(), name="design-memo-eval"),
        solver=[design_memo_solver()],
        scorer=_scorers(),
    )


@task
def design_memo_positive_eval() -> Task:
    """Positive samples only — useful for iterating on memo quality."""
    return Task(
        dataset=MemoryDataset(
            samples=_build_samples(positive=True, negative=False),
            name="design-memo-positive-eval",
        ),
        solver=[design_memo_solver()],
        scorer=_scorers(),
    )


@task
def design_memo_negative_eval() -> Task:
    """Negative controls — verify the skill does not trigger inappropriately."""
    return Task(
        dataset=MemoryDataset(
            samples=_build_samples(positive=False, negative=True),
            name="design-memo-negative-eval",
        ),
        solver=[design_memo_solver()],
        scorer=[memo_trigger()],
    )
