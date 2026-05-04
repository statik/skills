"""Deterministic scorers for design-memo HTML output.

No LLM calls. Each scorer takes the HTML source as a string and returns a
ScoreResult. Scorers are intentionally narrow: one observable property each,
so a failure points to a single concrete defect.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ScoreResult:
    passed: bool
    detail: str = ""

    def __bool__(self) -> bool:
        return self.passed


REQUIRED_PALETTE_VARS = (
    "--paper",
    "--ink",
    "--olive",
    "--ochre",
    "--muted",
    "--code-bg",
)
REQUIRED_NAMED_KEYS = (
    "ArrowRight",
    "ArrowDown",
    "PageDown",
    "ArrowLeft",
    "ArrowUp",
    "PageUp",
    "Home",
    "End",
)


def _parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _all_css(soup: BeautifulSoup) -> str:
    return "\n".join(s.get_text() for s in soup.find_all("style"))


def _all_inline_js(soup: BeautifulSoup) -> str:
    return "\n".join(s.get_text() for s in soup.find_all("script") if not s.get("src"))


# ---------- output / parsing ----------


def html_parses(html: str) -> ScoreResult:
    if not html.strip():
        return ScoreResult(False, "empty input")
    soup = _parse(html)
    if not soup.find("html"):
        return ScoreResult(False, "no <html> root")
    if not soup.find("body"):
        return ScoreResult(False, "no <body>")
    return ScoreResult(True, "parsed")


# ---------- self-contained ----------

_EXTERNAL_URL_RE = re.compile(r"^\s*https?://", re.IGNORECASE)
_PROTOCOL_RELATIVE_RE = re.compile(r"^\s*//")


def no_external_assets(html: str) -> ScoreResult:
    soup = _parse(html)
    findings: list[str] = []
    candidates = (
        ("link", "href"),
        ("script", "src"),
        ("img", "src"),
        ("iframe", "src"),
        ("source", "src"),
        ("video", "src"),
        ("audio", "src"),
    )
    for tag, attr in candidates:
        for el in soup.find_all(tag):
            value = el.get(attr) or ""
            if _EXTERNAL_URL_RE.match(value) or _PROTOCOL_RELATIVE_RE.match(value):
                findings.append(f"<{tag} {attr}={value!r}>")
    css_blob = _all_css(soup)
    for match in re.finditer(
        r"url\(\s*['\"]?(https?:[^'\")\s]+|//[^'\")\s]+)", css_blob
    ):
        findings.append(f"CSS url: {match.group(1)}")
    if re.search(r"@import[^;]*https?:", css_blob):
        findings.append("@import with http URL")
    if findings:
        return ScoreResult(False, "external refs: " + "; ".join(findings[:5]))
    return ScoreResult(True, "no external assets")


def inline_only(html: str) -> ScoreResult:
    soup = _parse(html)
    sourced = [s for s in soup.find_all("script") if s.get("src")]
    if sourced:
        return ScoreResult(False, f"{len(sourced)} script(s) with src=")
    if not soup.find("style"):
        return ScoreResult(False, "no <style> block")
    return ScoreResult(True, "all CSS/JS inline")


# ---------- structure ----------


def semantic_layout(html: str, min_sections: int = 4) -> ScoreResult:
    soup = _parse(html)
    main = soup.find("main")
    if not main:
        return ScoreResult(False, "no <main>")
    sections = main.find_all("section", recursive=False)
    if len(sections) < min_sections:
        return ScoreResult(
            False, f"only {len(sections)} sections (need {min_sections})"
        )
    if not soup.find("header"):
        return ScoreResult(False, "no <header>")
    return ScoreResult(True, f"{len(sections)} sections")


def palette_vars_defined(
    html: str, required: tuple[str, ...] = REQUIRED_PALETTE_VARS
) -> ScoreResult:
    css = _all_css(_parse(html))
    missing = [v for v in required if not re.search(rf"{re.escape(v)}\s*:", css)]
    if missing:
        return ScoreResult(False, f"missing vars: {missing}")
    return ScoreResult(True, "palette vars defined")


def ink_used_for_body(html: str) -> ScoreResult:
    css = _all_css(_parse(html))
    match = re.search(r"\bbody\s*\{([^}]*)\}", css, re.DOTALL)
    if not match:
        return ScoreResult(False, "no body { } block")
    block = match.group(1)
    color_match = re.search(r"\bcolor\s*:\s*([^;}\n]+)", block)
    if not color_match:
        return ScoreResult(False, "body has no color rule")
    value = color_match.group(1).strip()
    if "--ink" in value:
        return ScoreResult(True, "body color = var(--ink)")
    if "--muted" in value:
        return ScoreResult(False, "body color uses --muted (use --ink)")
    return ScoreResult(False, f"body color = {value!r} (expected var(--ink))")


# ---------- scrollytelling ----------


def progress_bar_aria(html: str) -> ScoreResult:
    bar = _parse(html).find(attrs={"role": "progressbar"})
    if not bar:
        return ScoreResult(False, "no [role=progressbar]")
    missing = [
        a
        for a in ("aria-valuenow", "aria-valuemin", "aria-valuemax")
        if not bar.has_attr(a)
    ]
    if missing:
        return ScoreResult(False, f"progressbar missing: {missing}")
    return ScoreResult(True, "progressbar with aria attrs")


def rail_present(html: str) -> ScoreResult:
    soup = _parse(html)
    rail = soup.find("nav", class_="story-rail") or soup.find(
        "nav", attrs={"aria-label": True}
    )
    if not rail:
        return ScoreResult(False, "no rail nav")
    label = (rail.get("aria-label") or "").lower()
    if "section" not in label and "navigation" not in label:
        return ScoreResult(False, f"rail aria-label={label!r}")
    return ScoreResult(True, "rail present")


def chapter_indicator_live(html: str) -> ScoreResult:
    indicator = _parse(html).find("aside", attrs={"aria-live": True})
    if not indicator:
        return ScoreResult(False, "no aside[aria-live]")
    value = indicator.get("aria-live")
    if value not in ("polite", "assertive"):
        return ScoreResult(False, f"aria-live={value!r}")
    return ScoreResult(True, "chapter indicator live region")


def keyboard_shortcuts(html: str) -> ScoreResult:
    js = _all_inline_js(_parse(html))
    missing = [k for k in REQUIRED_NAMED_KEYS if k not in js]
    if missing:
        return ScoreResult(False, f"missing key handlers: {missing}")
    if not re.search(r'={2,3}\s*["\']\s["\']', js):
        return ScoreResult(False, "no Space key handler")
    if not re.search(r"\[1-9\]", js):
        return ScoreResult(False, "no number-key (1-9) handler")
    return ScoreResult(True, "all key handlers present")


def editable_focus_guard(html: str) -> ScoreResult:
    js = _all_inline_js(_parse(html))
    has_editable = bool(re.search(r"contenteditable", js, re.IGNORECASE))
    has_form_check = '"input"' in js and '"textarea"' in js
    if has_editable and has_form_check:
        return ScoreResult(True, "guards editable targets")
    return ScoreResult(
        False,
        f"missing editable guard (contenteditable={has_editable}, form_check={has_form_check})",
    )


# ---------- accessibility / contrast ----------

_HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})")


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        x = c / 255.0
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(c1: tuple[int, int, int], c2: tuple[int, int, int]) -> float:
    l1 = _relative_luminance(c1)
    l2 = _relative_luminance(c2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _extract_var(css: str, name: str) -> str | None:
    match = re.search(rf"{re.escape(name)}\s*:\s*([^;]+);", css)
    return match.group(1).strip() if match else None


def wcag_aa_contrast(html: str, min_ratio: float = 4.5) -> ScoreResult:
    css = _all_css(_parse(html))
    ink = _extract_var(css, "--ink")
    paper = _extract_var(css, "--paper")
    if not ink or not paper:
        return ScoreResult(False, "missing --ink or --paper")
    ink_match = _HEX_RE.search(ink)
    paper_match = _HEX_RE.search(paper)
    if not ink_match or not paper_match:
        return ScoreResult(False, f"non-hex palette: ink={ink}, paper={paper}")
    ratio = _contrast(_hex_to_rgb(ink_match.group(0)), _hex_to_rgb(paper_match.group(0)))
    if ratio < min_ratio:
        return ScoreResult(False, f"contrast {ratio:.2f}:1 below {min_ratio}:1")
    return ScoreResult(True, f"contrast {ratio:.2f}:1")


def focus_visible_styles(html: str) -> ScoreResult:
    if ":focus-visible" not in _all_css(_parse(html)):
        return ScoreResult(False, "no :focus-visible rule")
    return ScoreResult(True, ":focus-visible present")


def reduced_motion_query(html: str) -> ScoreResult:
    if "prefers-reduced-motion" not in _all_css(_parse(html)):
        return ScoreResult(False, "no prefers-reduced-motion query")
    return ScoreResult(True, "prefers-reduced-motion handled")


def no_js_progressive(html: str) -> ScoreResult:
    css = _all_css(_parse(html))
    if not re.search(r"\.js\s+section:not\(\.is-active\)", css):
        return ScoreResult(False, "dimming not gated on .js class")
    return ScoreResult(True, "progressive enhancement gated on .js")


def aria_keyshortcuts_in_js(html: str) -> ScoreResult:
    if "aria-keyshortcuts" not in _all_inline_js(_parse(html)):
        return ScoreResult(False, "JS does not set aria-keyshortcuts")
    return ScoreResult(True, "aria-keyshortcuts set in JS")


def aria_current_step(html: str) -> ScoreResult:
    js = _all_inline_js(_parse(html))
    if not re.search(r'aria-current["\']\s*,\s*["\']step["\']', js):
        return ScoreResult(False, 'no aria-current="step" assignment')
    if re.search(r'aria-current["\']\s*,\s*["\']false["\']', js):
        return ScoreResult(False, 'sets aria-current="false" instead of removing')
    if "removeAttribute" not in js:
        return ScoreResult(False, "no removeAttribute for aria-current")
    return ScoreResult(True, "aria-current managed correctly")


# ---------- code listing safety ----------


def highlighter_escapes_html(html: str) -> ScoreResult:
    js = _all_inline_js(_parse(html))
    if "innerHTML" not in js:
        return ScoreResult(True, "no innerHTML assignment")
    if re.search(r"escapeHtml|escape_html", js):
        return ScoreResult(True, "escape function present")
    if re.search(r'/&/g\s*,\s*["\']&amp;["\']', js):
        return ScoreResult(True, "explicit &amp; replacement present")
    return ScoreResult(False, "innerHTML without HTML escaping")


# ---------- print / mobile ----------


def print_media_query(html: str) -> ScoreResult:
    if not re.search(r"@media\s+print\s*\{", _all_css(_parse(html))):
        return ScoreResult(False, "no @media print block")
    return ScoreResult(True, "@media print present")


def mobile_breakpoint(html: str) -> ScoreResult:
    if not re.search(r"@media[^{]*max-width", _all_css(_parse(html))):
        return ScoreResult(False, "no max-width media query")
    return ScoreResult(True, "responsive breakpoint present")


# ---------- registry ----------

ALL_SCORERS = (
    html_parses,
    no_external_assets,
    inline_only,
    semantic_layout,
    palette_vars_defined,
    ink_used_for_body,
    progress_bar_aria,
    rail_present,
    chapter_indicator_live,
    keyboard_shortcuts,
    editable_focus_guard,
    wcag_aa_contrast,
    focus_visible_styles,
    reduced_motion_query,
    no_js_progressive,
    aria_keyshortcuts_in_js,
    aria_current_step,
    highlighter_escapes_html,
    print_media_query,
    mobile_breakpoint,
)
