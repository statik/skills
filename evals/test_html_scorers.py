"""Tier-1 fixture-only tests for design-memo HTML scorers.

No LLM calls. The canonical "good" memo is the HTML skeleton embedded in
design-memo/skills/design-memo/SKILL.md - extracting it here keeps the spec authoritative.
Negative cases are surgical mutations of the good skeleton, so each failing
assertion points at exactly one defect.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import html_scorers as hs

SKILL_MD = Path(__file__).parent.parent / "design-memo" / "skills" / "design-memo" / "SKILL.md"


# ---------- fixture extraction ----------


@pytest.fixture(scope="session")
def good_html() -> str:
    text = SKILL_MD.read_text()
    match = re.search(r"```html\n(.*?)\n```", text, re.DOTALL)
    if not match:
        pytest.fail("HTML skeleton fence not found in SKILL.md")
    return match.group(1)


def _mutate(html: str, find: str, replace: str) -> str:
    if find not in html:
        raise AssertionError(f"mutation source not in skeleton: {find!r}")
    return html.replace(find, replace, 1)


# ---------- positive: skeleton passes every scorer ----------


@pytest.mark.parametrize("scorer", hs.ALL_SCORERS, ids=lambda s: s.__name__)
def test_skeleton_passes(scorer, good_html):
    result = scorer(good_html)
    assert result.passed, f"{scorer.__name__}: {result.detail}"


# ---------- negative: targeted mutations break exactly one scorer ----------


def test_empty_input_fails_html_parses():
    assert not hs.html_parses("")
    assert not hs.html_parses("   \n  ")


def test_external_link_fails_no_external_assets(good_html):
    bad = _mutate(
        good_html,
        "</head>",
        '<link rel="stylesheet" href="https://fonts.googleapis.com/x"></head>',
    )
    result = hs.no_external_assets(bad)
    assert not result.passed
    assert "fonts.googleapis.com" in result.detail


def test_external_script_fails_no_external_assets(good_html):
    bad = _mutate(
        good_html,
        "</head>",
        '<script src="https://cdn.example.com/x.js"></script></head>',
    )
    assert not hs.no_external_assets(bad)


def test_external_image_fails_no_external_assets(good_html):
    bad = _mutate(
        good_html, "<body>", '<body><img src="https://i.example.com/a.png">'
    )
    assert not hs.no_external_assets(bad)


def test_css_external_url_fails_no_external_assets(good_html):
    bad = _mutate(
        good_html,
        "color-scheme: light;",
        "color-scheme: light; background-image: url(https://example.com/bg.png);",
    )
    assert not hs.no_external_assets(bad)


def test_sourced_script_fails_inline_only(good_html):
    bad = _mutate(good_html, "</head>", '<script src="x.js"></script></head>')
    assert not hs.inline_only(bad)


def test_missing_main_fails_semantic_layout(good_html):
    bad = good_html.replace("<main>", "<div>", 1).replace("</main>", "</div>", 1)
    assert not hs.semantic_layout(bad)


def test_missing_palette_var_fails(good_html):
    bad = _mutate(good_html, "--ink: #171c1d;", "")
    assert not hs.palette_vars_defined(bad)


def test_body_uses_muted_fails_ink_for_body(good_html):
    bad = _mutate(good_html, "color: var(--ink);", "color: var(--muted);")
    result = hs.ink_used_for_body(bad)
    assert not result.passed
    assert "--muted" in result.detail


def test_low_contrast_palette_fails_wcag(good_html):
    bad = _mutate(good_html, "--ink: #171c1d;", "--ink: #aab2af;")
    result = hs.wcag_aa_contrast(bad)
    assert not result.passed
    assert "below" in result.detail


def test_non_hex_palette_fails_wcag(good_html):
    bad = _mutate(good_html, "--ink: #171c1d;", "--ink: var(--paper);")
    assert not hs.wcag_aa_contrast(bad)


def test_missing_progressbar_role_fails(good_html):
    bad = _mutate(good_html, 'role="progressbar"', "")
    assert not hs.progress_bar_aria(bad)


def test_missing_progressbar_value_attrs_fails(good_html):
    bad = _mutate(good_html, 'aria-valuenow="0"', "")
    assert not hs.progress_bar_aria(bad)


def test_missing_rail_fails(good_html):
    bad = _mutate(
        good_html,
        '<nav class="story-rail" aria-label="Section navigation"></nav>',
        "",
    )
    assert not hs.rail_present(bad)


def test_missing_chapter_indicator_fails(good_html):
    bad = _mutate(good_html, 'aria-live="polite"', "")
    assert not hs.chapter_indicator_live(bad)


def test_missing_named_key_fails_keyboard(good_html):
    bad = _mutate(good_html, '"ArrowRight"', '"X"')
    result = hs.keyboard_shortcuts(bad)
    assert not result.passed
    assert "ArrowRight" in result.detail


def test_missing_space_handler_fails_keyboard(good_html):
    bad = good_html.replace('event.key === " "', 'event.key === "Spacebar"')
    assert not hs.keyboard_shortcuts(bad)


def test_missing_number_handler_fails_keyboard(good_html):
    bad = good_html.replace("/^[1-9]$/", "/^_$/")
    assert not hs.keyboard_shortcuts(bad)


def test_missing_editable_guard_fails(good_html):
    bad = _mutate(good_html, "isContentEditable", "x")
    assert not hs.editable_focus_guard(bad)


def test_no_focus_visible_fails(good_html):
    bad = good_html.replace(":focus-visible", ":hover")
    assert not hs.focus_visible_styles(bad)


def test_no_reduced_motion_fails(good_html):
    bad = good_html.replace("prefers-reduced-motion", "prefers-color-scheme")
    assert not hs.reduced_motion_query(bad)


def test_no_js_class_gating_fails(good_html):
    bad = good_html.replace(".js section:not(.is-active)", "section:not(.is-active)")
    assert not hs.no_js_progressive(bad)


def test_missing_keyshortcuts_fails(good_html):
    bad = good_html.replace("aria-keyshortcuts", "data-keyshortcuts")
    assert not hs.aria_keyshortcuts_in_js(bad)


def test_aria_current_false_fails(good_html):
    bad = _mutate(
        good_html,
        'removeAttribute("aria-current")',
        'setAttribute("aria-current", "false")',
    )
    result = hs.aria_current_step(bad)
    assert not result.passed
    assert "false" in result.detail


def test_innerhtml_without_escape_fails(good_html):
    no_escape_fn = re.sub(
        r"function escapeHtml\(value\)\s*\{[^}]+\}", "", good_html, count=1
    )
    bad = no_escape_fn.replace("escapeHtml(", "(").replace(
        '/&/g, "&amp;"', '/&/g, "&"'
    )
    assert "innerHTML" in bad, "mutation removed innerHTML by accident"
    assert not hs.highlighter_escapes_html(bad)


def test_no_print_query_fails(good_html):
    bad = good_html.replace("@media print", "@media notprint")
    assert not hs.print_media_query(bad)


def test_no_mobile_breakpoint_fails(good_html):
    bad = re.sub(
        r"@media\s*\(\s*max-width[^{]*",
        "@media (orientation: landscape) ",
        good_html,
    )
    assert not hs.mobile_breakpoint(bad)
