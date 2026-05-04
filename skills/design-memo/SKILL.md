---
name: design-memo
description: "Produce polished, self-contained HTML design memos with Tufte-inspired editorial layout and scrollytelling interaction. This is the default output format for any plan, design, architecture proposal, implementation approach, decision record, or review document. For simple plans, ask the user whether they prefer plain text; default to HTML for non-trivial plans."
metadata:
  version: 1.0.0
  keywords:
    - design
    - architecture
    - plan
    - presentation
    - html
    - tufte
    - scrollytelling
    - memo
    - proposal
    - review
  triggers:
    - "create a plan"
    - "architecture proposal"
    - "implementation plan"
    - "design document"
    - "decision record"
    - "review document"
    - "design memo"
    - "plan the implementation"
  platforms:
    - claude-code
    - opencode
    - github-copilot
    - claude-desktop
---

# Design Memo

## Purpose

This is the default output format for plans and designs. When a user requests
any plan, design, architecture proposal, implementation approach, decision
record, or review document, offer to produce it as an HTML design memo. For
simple or quick plans, ask whether they would prefer plain text. Default to HTML
for non-trivial plans involving multiple components or architectural decisions.

The output is a single standalone HTML file with inline CSS and JavaScript,
readable as both a scrollable presentation and a long-form design memo. It
includes enough implementation detail that reviewers can evaluate the design
without reading the chat transcript.

## Output

- Create or update a single standalone `.html` file.
- Keep the file self-contained: inline CSS and JavaScript only.
- Do not depend on external fonts, scripts, CSS frameworks, image assets, or CDN
  libraries.
- Use semantic HTML sections so the document reads well as both a presentation
  and a long-form design memo.
- Include enough implementation detail that the presentation can be reviewed
  without reading the chat transcript.

## Output Location

- Place the output HTML file in a `docs/` subdirectory if one exists in the
  project.
- If no `docs/` directory exists, ask the user whether to create one or place
  the file in the current working directory.
- Never create `docs/` without user confirmation.

## Output File Naming

Name output files using the pattern `<topic>-design-memo.html`, where `<topic>`
is a lowercase, hyphenated summary of the subject matter. Examples:

- `cdn-migration-design-memo.html`
- `auth-flow-design-memo.html`
- `database-sharding-design-memo.html`

## Visual Direction

- Use a Tufte-inspired editorial layout:
  - Serif typography for headings and narrative text.
  - Restrained tables with strong horizontal rules.
  - Margin-note style callouts for caveats, rationale, and important review
    notes.
  - Wide content when detail is dense, but avoid a generic slide-deck look.
- Use a cinematic palette when requested. If no palette is specified, default to
  an Arrival-inspired Denis Villeneuve palette:
  - Foggy slate / mist gray backgrounds.
  - Charcoal ink for text.
  - Muted olive and amber for structure.
  - Blue-gray accents for progress and technical emphasis.
- Avoid copyrighted imagery or film stills. Use color, spacing, and atmosphere
  only.

## Default Palette Variables

Use these as the default Arrival-inspired palette unless the user requests a
different mood:

```css
:root {
  --paper: #cfd4cf;
  --paper-deep: #7f8985;
  --panel: #e6e6df;
  --ink: #171c1d;
  --muted: #4a5250;
  --olive: #4a4f3f;
  --amber: #9a7a55;
  --ochre: #b79b65;
  --mustard: #d6c7a4;
  --teal: #2f5557;
  --blue: #5f7f86;
  --line: #9aa39d;
  --code: #111819;
  --code-bg: #bdc8c3;
}
```

`--muted` is for secondary or supplementary text only (e.g., margin notes,
captions). Never use it for essential content — use `--ink` instead.

## Scrollytelling Interaction

Add lightweight scrollytelling affordances:

- A fixed top progress bar showing scroll progress.
- A right-side section rail with dots for each section.
- Hover labels for the dots.
- A sticky or fixed chapter indicator with the current section number and label.
- Active-section transitions, such as subtle opacity, lift, or scale changes.
- Keep all interaction implemented with small vanilla JavaScript.
- Hide progress UI in print and simplify it on small screens.
- Prefer `scroll-snap-type: y proximity` over mandatory snapping so long tables and
  code listings remain easy to read. Disable snapping on small screens and for
  users who prefer reduced motion.
- Add presentation-style keyboard shortcuts: `ArrowRight`, `ArrowDown`,
  `PageDown`, and `Space` advance; `ArrowLeft`, `ArrowUp`, and `PageUp` go back;
  `Home` and `End` jump to the first and last sections; number keys `1` through
  `9` jump directly to sections 1 through 9.

## Accessibility

- Ensure all text meets WCAG 2.1 AA contrast ratios (4.5:1 for body text, 3:1
  for large text) against palette backgrounds. Verify contrast when customizing
  the palette.
- Scrollytelling navigation dots must be keyboard-focusable (`<button>` elements)
  with visible focus indicators (outline or ring).
- Add `role="navigation"` and `aria-label="Section navigation"` to the section
  rail.
- Mark the progress bar with `role="progressbar"`, `aria-valuenow`,
  `aria-valuemin="0"`, and `aria-valuemax="100"`.
- Use `aria-current="step"` on the active section dot.
- Remove `aria-current` from inactive dots rather than setting it to `"false"`.
- Add `aria-keyshortcuts` to rail dots for the first nine number-key shortcuts.
- The sticky chapter indicator should use `aria-live="polite"` so screen readers
  announce section changes.
- Ensure all content is reachable without JavaScript: all content remains visible
  in document order (progressive enhancement, not JavaScript-dependent rendering).
- Use `prefers-reduced-motion` media query to disable scroll-triggered
  animations for users who prefer reduced motion.
- Do not dim or transform content by default. If using inactive-section styling,
  add a `.js` class from JavaScript and scope dimming to `.js section:not(.is-active)`
  so no-JS readers get fully readable content.
- Do not capture global shortcuts while focus is in editable controls. Let focused
  rail buttons keep their native `Enter`/`Space` activation behavior.

## Content Structure

For technical designs or plans, prefer this structure:

1. Opening decision or design thesis with the recommended path stated first.
2. Ordered behavior, architecture, or priority table.
3. Decision model / request flow / state machine.
4. Implementation draft or pseudocode.
5. Validation matrix with inputs, expected outcomes, and rationale.
6. Operational notes, such as caching, deployment, rollback, or monitoring.
7. Source/evidence inventory so reviewers can audit the analysis.
8. Confidence and caveats.

Adapt the section names to the user's domain. Do not keep route inventory or
background-analysis sections unless they directly support the design.

## Presentation Components

Use the richer presentation components from the skeleton when they help reviewers
scan the memo:

- A hero/decision slide with an eyebrow, decisive title, short thesis, and the
  first table of ordered decisions.
- `.card` and `.card-body` wrappers for dense sections.
- `.grid-2` or `.grid-3` for side-by-side decision models and caveats.
- `.source` blocks for evidence, files reviewed, assumptions, or alternatives.
- `.badge`, `.badge.success`, `.badge.warning`, and `.badge.danger` for
  classifications such as "recommended", "caveat", "blocked", or "pass-through".
- `.callout`, `.callout.warning`, and `.callout.danger` for review-critical
  notes that should not be buried in prose.
- `.footer` source summaries at the end of evidence-heavy memos.

## Code Listings

- Include syntax-highlighted code blocks for implementation drafts.
- Prefer a tiny inline highlighter or hand-authored spans over external
  libraries.
- If using an inline highlighter, escape HTML before assigning highlighted output
  to `innerHTML`.
- For infrastructure functions, include comments that explain the rationale for
  each major decision branch.
- Keep code examples realistic and directly usable, but label them as drafts
  when environmental details may vary.

## Review Quality Bar

- Preserve the user's intended behavior and clearly identify pass-through,
  rewrite, fallback, and unknown/default cases.
- Make rule ordering explicit when it matters.
- Include test cases that reviewers can scan quickly.
- Include a "Sources reviewed" footer or table for review documents and design
  memos based on code inspection.
- Surface caveats plainly rather than burying them in prose.
- Avoid masking unknown routes or failure cases in the design unless the user
  explicitly asks for catch-all behavior.

## HTML Implementation Notes

- Use one `<section>` per major step.
- Wrap sections in `<main>` and include a semantic `<header>` hero when the memo
  has a decision thesis.
- Add generated navigation by scanning `main > section` in JavaScript.
- Use CSS custom properties for the palette so future palette changes are easy.
- Validate embedded JavaScript syntax after edits.
- Keep the presentation readable when JavaScript is disabled: all content should
  remain visible in document order.
- Build labels from `.eyebrow` plus `h1`/`h2` when available so the rail and
  chapter indicator are meaningful.

## HTML Skeleton

Use this as a starting scaffold. Adapt the sections to match the plan content —
this is a structural reference, not a rigid template. Keep the accessibility
contract intact when changing the visual design.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Design Memo — TOPIC</title>
  <script>
    document.documentElement.className += " js";
  </script>
  <style>
    :root {
      color-scheme: light;
      --paper: #cfd4cf;
      --paper-deep: #7f8985;
      --panel: #e6e6df;
      --ink: #171c1d;
      --muted: #4a5250;
      --olive: #4a4f3f;
      --amber: #9a7a55;
      --ochre: #b79b65;
      --mustard: #d6c7a4;
      --teal: #2f5557;
      --blue: #5f7f86;
      --line: #9aa39d;
      --code: #111819;
      --code-bg: #bdc8c3;
    }

    *, *::before, *::after { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background:
        radial-gradient(circle at 14% 0%, rgba(214, 199, 164, 0.5), transparent 28rem),
        radial-gradient(circle at 86% 8%, rgba(95, 127, 134, 0.28), transparent 30rem),
        linear-gradient(135deg, #dce0dc, var(--paper) 52%, var(--paper-deep));
      color: var(--ink);
      line-height: 1.6;
    }

    .progress-bar {
      position: fixed;
      z-index: 20;
      top: 0;
      left: 0;
      width: 100%;
      height: 0.45rem;
      background: rgba(23, 28, 29, 0.13);
    }

    .progress-bar__fill {
      width: 0;
      height: 100%;
      background: linear-gradient(90deg, var(--olive), var(--ochre), var(--amber));
      transition: width 120ms linear;
    }

    .story-rail {
      position: fixed;
      z-index: 15;
      top: 50%;
      right: clamp(0.8rem, 2vw, 1.8rem);
      display: grid;
      gap: 0.8rem;
      transform: translateY(-50%);
    }

    .story-dot {
      position: relative;
      width: 0.78rem;
      height: 0.78rem;
      border: 1px solid var(--ink);
      border-radius: 999px;
      background: var(--panel);
      cursor: pointer;
      opacity: 0.72;
      transition: background 180ms ease, opacity 180ms ease, transform 180ms ease;
    }

    .story-dot:focus-visible {
      outline: 2px solid var(--teal);
      outline-offset: 4px;
    }

    .story-dot::after {
      position: absolute;
      top: 50%;
      right: 1.15rem;
      width: max-content;
      max-width: 14rem;
      padding: 0.22rem 0.5rem;
      border: 1px solid var(--line);
      background: rgba(230, 230, 223, 0.95);
      color: var(--ink);
      content: attr(aria-label);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.72rem;
      letter-spacing: 0.04em;
      opacity: 0;
      pointer-events: none;
      transform: translateY(-50%) translateX(0.3rem);
      transition: opacity 160ms ease, transform 160ms ease;
    }

    .story-dot:hover::after,
    .story-dot:focus-visible::after,
    .story-dot.is-active::after {
      opacity: 1;
      transform: translateY(-50%) translateX(0);
    }

    .story-dot.is-active {
      background: var(--olive);
      opacity: 1;
      transform: scale(1.35);
    }

    .chapter-indicator {
      position: fixed;
      z-index: 14;
      bottom: clamp(1rem, 3vw, 2rem);
      left: clamp(1rem, 4vw, 3rem);
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 0.6rem 0.85rem;
      align-items: center;
      max-width: min(28rem, calc(100vw - 7rem));
      padding: 0.75rem 0.95rem;
      border: 1px solid rgba(154, 122, 85, 0.8);
      background: rgba(230, 230, 223, 0.84);
      box-shadow: 0 10px 28px rgba(23, 28, 29, 0.14);
      backdrop-filter: blur(8px);
    }

    .chapter-indicator__number {
      color: var(--olive);
      font-size: 1.55rem;
      line-height: 1;
    }

    .chapter-indicator__label {
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    .chapter-indicator__rule {
      grid-column: 1 / -1;
      height: 1px;
      overflow: hidden;
      background: rgba(23, 28, 29, 0.18);
    }

    .chapter-indicator__rule span {
      display: block;
      width: 0;
      height: 100%;
      background: var(--ochre);
      transition: width 120ms linear;
    }

    main {
      scroll-snap-type: y proximity;
    }

    section {
      display: grid;
      min-height: 100vh;
      padding: 4.5rem clamp(1.25rem, 5vw, 6rem);
      place-items: center;
      scroll-snap-align: start;
    }

    .slide {
      width: min(1180px, 100%);
    }

    .card {
      overflow: hidden;
      border: 1px solid var(--line);
      border-top: 9px double var(--olive);
      background:
        linear-gradient(90deg, rgba(214, 199, 164, 0.26), transparent 36%),
        rgba(230, 230, 223, 0.96);
      box-shadow:
        0 1px 0 rgba(23, 28, 29, 0.18),
        0 18px 45px rgba(44, 55, 55, 0.16);
      transition: opacity 420ms ease, transform 420ms ease, box-shadow 420ms ease;
    }

    .js section:not(.is-active) .card {
      opacity: 0.76;
      transform: translateY(1.8rem) scale(0.985);
    }

    .js section.is-active .card {
      opacity: 1;
      transform: translateY(0) scale(1);
      box-shadow:
        0 1px 0 rgba(23, 28, 29, 0.18),
        0 26px 70px rgba(44, 55, 55, 0.22);
    }

    .card-body {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(13rem, 0.28fr);
      column-gap: clamp(2rem, 6vw, 5rem);
      padding: clamp(2rem, 4vw, 4.6rem);
    }

    .card-body > * {
      grid-column: 1;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 1.1rem;
      color: var(--teal);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.16em;
      text-transform: uppercase;
    }

    .eyebrow::before {
      width: 0.75rem;
      height: 0.75rem;
      border-radius: 999px;
      background: var(--ochre);
      content: "";
    }

    h1,
    h2,
    h3 {
      margin: 0;
      line-height: 1.05;
    }

    h1 {
      max-width: 820px;
      color: var(--olive);
      font-size: clamp(3rem, 7vw, 6.25rem);
      font-weight: 500;
      letter-spacing: -0.045em;
    }

    h2 {
      max-width: 780px;
      color: var(--olive);
      font-size: clamp(2.1rem, 4.6vw, 4.7rem);
      font-weight: 500;
      letter-spacing: -0.035em;
    }

    p {
      max-width: 700px;
      margin: 1.2rem 0 0;
      color: var(--muted);
      font-size: clamp(1.05rem, 1.55vw, 1.23rem);
    }

    .lead {
      max-width: 760px;
      font-size: clamp(1.25rem, 2.2vw, 1.62rem);
    }

    .grid {
      display: grid;
      gap: 1rem;
      margin-top: 2rem;
    }

    .grid-2 {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .grid-3 {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .source {
      padding: 1rem 1.15rem;
      border: 1px solid var(--line);
      background: rgba(230, 230, 223, 0.68);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .source strong {
      display: block;
      margin-bottom: 0.35rem;
    }

    .callout {
      grid-column: 2;
      align-self: start;
      margin-top: 2rem;
      padding: 0.35rem 0 0.35rem 1rem;
      border-left: 3px solid var(--teal);
      color: var(--muted);
      font-size: 0.98rem;
      font-style: italic;
    }

    .callout.warning {
      border-left-color: var(--ochre);
    }

    .callout.danger {
      border-left-color: var(--olive);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1.8rem;
      border-top: 2px solid var(--ink);
      border-bottom: 2px solid var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.88rem;
    }

    th, td {
      text-align: left;
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }

    th {
      background: rgba(214, 199, 164, 0.32);
      color: var(--ink);
      font-size: 0.8rem;
      letter-spacing: 0.07em;
      text-transform: uppercase;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      background: rgba(95, 127, 134, 0.2);
      color: #355e66;
      font-size: 0.78rem;
      font-weight: 800;
      white-space: nowrap;
    }

    .badge.success {
      background: rgba(31, 63, 70, 0.18);
      color: #1f3f46;
    }

    .badge.warning {
      background: rgba(214, 199, 164, 0.42);
      color: #5e4a2e;
    }

    .badge.danger {
      background: rgba(154, 122, 85, 0.28);
      color: var(--olive);
    }

    code,
    pre {
      border-radius: 10px;
      background: var(--code-bg);
      color: var(--code);
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    }

    code {
      padding: 0.15rem 0.4rem;
      font-size: 0.92em;
    }

    pre {
      overflow-x: auto;
      margin: 1.6rem 0 0;
      padding: 1.2rem 1.35rem;
      border: 1px solid var(--line);
      border-left: 6px solid var(--blue);
      font-size: 0.9rem;
      line-height: 1.55;
      white-space: pre-wrap;
    }

    .code-js {
      position: relative;
      background:
        linear-gradient(90deg, rgba(95, 127, 134, 0.17), transparent 44%),
        var(--code-bg);
    }

    .code-js::before {
      position: absolute;
      top: 0.65rem;
      right: 0.85rem;
      color: var(--muted);
      content: "JavaScript";
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .tok-keyword { color: var(--olive); font-weight: 700; }
    .tok-boolean { color: var(--teal); font-weight: 700; }
    .tok-string { color: #6b5537; }
    .tok-regex { color: #3a6670; }
    .tok-function { color: var(--teal); font-weight: 700; }
    .tok-comment { color: var(--muted); font-style: italic; }

    .footer {
      margin-top: 2rem;
      color: var(--muted);
      font-size: 0.9rem;
    }

    @media print {
      .progress-bar,
      .story-rail,
      .chapter-indicator {
        display: none;
      }

      body {
        background: #fff;
      }

      main {
        scroll-snap-type: none;
      }

      section {
        min-height: auto;
        break-inside: avoid;
        page-break-after: always;
      }

      .card {
        box-shadow: none;
      }
    }

    @media (max-width: 820px) {
      .story-rail,
      .chapter-indicator {
        display: none;
      }

      main {
        scroll-snap-type: none;
      }

      section {
        min-height: auto;
        padding-block: 2rem;
        scroll-snap-align: none;
      }

      .card-body {
        grid-template-columns: 1fr;
      }

      .callout {
        grid-column: 1;
      }

      .grid-2,
      .grid-3 {
        grid-template-columns: 1fr;
      }

      table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
      }
    }

    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        scroll-behavior: auto !important;
        transition: none !important;
      }

      main {
        scroll-snap-type: none;
      }

      section {
        scroll-snap-align: none;
      }
    }
  </style>
</head>
<body>
  <div class="progress-bar" role="progressbar" aria-label="Document scroll progress"
       aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
    <div class="progress-bar__fill"></div>
  </div>

  <nav class="story-rail" aria-label="Section navigation"></nav>

  <aside class="chapter-indicator" aria-live="polite">
    <span class="chapter-indicator__number">01</span>
    <span class="chapter-indicator__label">Decision</span>
    <span class="chapter-indicator__rule"><span></span></span>
  </aside>

  <main>
    <section>
      <div class="slide">
        <div class="card">
          <header class="card-body">
            <div class="eyebrow">Decision</div>
            <h1>State the recommended design in one sentence</h1>
            <p class="lead">
              Lead with the decision, then explain why it preserves the intended
              behavior and which alternatives were rejected.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Rule</th>
                  <th>Outcome</th>
                  <th>Rationale</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>1</td>
                  <td><code>critical-path</code></td>
                  <td><span class="badge success">Recommended</span></td>
                  <td>Summarize the highest-priority behavior first.</td>
                </tr>
                <tr>
                  <td>2</td>
                  <td><code>fallback</code></td>
                  <td><span class="badge warning">Caveat</span></td>
                  <td>Make defaults and unknown cases explicit.</td>
                </tr>
              </tbody>
            </table>
            <div class="callout warning">
              Use callouts for details reviewers must notice before approving.
            </div>
          </header>
        </div>
      </div>
    </section>

    <section>
      <div class="slide">
        <div class="card">
          <div class="card-body">
            <div class="eyebrow">Decision model</div>
            <h2>Show the request flow or state machine</h2>
            <div class="grid grid-2">
              <div class="source">
                <strong>1. First branch</strong>
                <span>Describe the condition, expected behavior, and owner.</span>
              </div>
              <div class="source">
                <strong>2. Second branch</strong>
                <span>Describe pass-through, rewrite, fallback, or rejection.</span>
              </div>
              <div class="source">
                <strong>3. Known-good path</strong>
                <span>Explain the normal successful path.</span>
              </div>
              <div class="source">
                <strong>4. Unknown/default path</strong>
                <span>Explain how unknown inputs fail safely.</span>
              </div>
            </div>
            <div class="callout">
              Rule ordering matters. Present ordered behavior before code.
            </div>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="slide">
        <div class="card">
          <div class="card-body">
            <div class="eyebrow">Implementation draft</div>
            <h2>Include realistic pseudocode or configuration</h2>
            <pre class="code-js" data-lang="js">function chooseBehavior(input) {
  // Preserve protected or externally-owned paths first.
  if (shouldPassThrough(input)) {
    return "pass-through";
  }

  // Then handle known application-owned routes.
  if (isKnownApplicationPath(input)) {
    return "rewrite";
  }

  // Unknown paths should fail explicitly unless catch-all behavior is required.
  return "not-found";
}</pre>
            <div class="callout">
              Label drafts when environment-specific names or APIs may vary.
            </div>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="slide">
        <div class="card">
          <div class="card-body">
            <div class="eyebrow">Validation</div>
            <h2>Provide a scan-friendly validation matrix</h2>
            <table>
              <thead>
                <tr>
                  <th>Input</th>
                  <th>Expected outcome</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>known-good</code></td>
                  <td>Success path</td>
                  <td>Confirms the intended behavior.</td>
                </tr>
                <tr>
                  <td><code>unknown</code></td>
                  <td>Explicit failure or fallback</td>
                  <td>Prevents accidental masking of errors.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="slide">
        <div class="card">
          <div class="card-body">
            <div class="eyebrow">Operations</div>
            <h2>Document deployment, caching, rollback, and monitoring</h2>
            <div class="grid grid-3">
              <div class="source"><strong>Deploy</strong><span>How the change rolls out.</span></div>
              <div class="source"><strong>Rollback</strong><span>How to return to the prior behavior.</span></div>
              <div class="source"><strong>Observe</strong><span>Signals that confirm success or failure.</span></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section>
      <div class="slide">
        <div class="card">
          <div class="card-body">
            <div class="eyebrow">Sources and caveats</div>
            <h2>Close with evidence, confidence, and follow-ups</h2>
            <div class="grid grid-2">
              <div class="source">
                <strong>High confidence</strong>
                <span>Summarize the files, APIs, traces, or docs reviewed.</span>
              </div>
              <div class="source">
                <strong>Main caveat</strong>
                <span>State the riskiest unknown plainly.</span>
              </div>
            </div>
            <div class="footer">
              Sources reviewed: <code>path/to/file</code>, <code>path/to/test</code>,
              and <code>relevant documentation</code>.
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>

  <script>
    (function () {
      var blocks = document.querySelectorAll('pre[data-lang="js"]');
      var tokenPattern =
        /(\/\/[^\n]*|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|\b(function|var|if|return)\b|\b(true|false)\b|\b([A-Za-z_$][\w$]*)(?=\s*\())/g;

      function escapeHtml(value) {
        return value
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;");
      }

      function classNameFor(token) {
        if (token.indexOf("//") === 0) return "tok-comment";
        if (token.charAt(0) === "'" || token.charAt(0) === '"') return "tok-string";
        if (/^(function|var|if|return)$/.test(token)) return "tok-keyword";
        if (/^(true|false)$/.test(token)) return "tok-boolean";
        return "tok-function";
      }

      function highlight(source) {
        var cursor = 0;
        var output = "";
        var match;

        while ((match = tokenPattern.exec(source)) !== null) {
          output += escapeHtml(source.slice(cursor, match.index));
          output += '<span class="' + classNameFor(match[0]) + '">' +
            escapeHtml(match[0]) + "</span>";
          cursor = match.index + match[0].length;
        }

        return output + escapeHtml(source.slice(cursor));
      }

      for (var i = 0; i < blocks.length; i += 1) {
        blocks[i].innerHTML = highlight(blocks[i].textContent);
      }

      var sections = document.querySelectorAll("main > section");
      var rail = document.querySelector(".story-rail");
      var progress = document.querySelector(".progress-bar");
      var progressFill = document.querySelector(".progress-bar__fill");
      var chapterNumber = document.querySelector(".chapter-indicator__number");
      var chapterLabel = document.querySelector(".chapter-indicator__label");
      var chapterRule = document.querySelector(".chapter-indicator__rule span");
      var dots = [];
      var activeIndex = 0;
      var prefersReducedMotion = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

      function twoDigit(value) {
        return value < 10 ? "0" + value : String(value);
      }

      function isEditableTarget(target) {
        if (!target) return false;
        var tagName = target.tagName ? target.tagName.toLowerCase() : "";
        return target.isContentEditable ||
          tagName === "input" ||
          tagName === "textarea" ||
          tagName === "select";
      }

      function sectionTitle(section, index) {
        var label = section.querySelector(".eyebrow");
        var heading = section.querySelector("h1, h2");
        if (label && heading) return label.textContent + ": " + heading.textContent;
        if (heading) return heading.textContent;
        return "Section " + String(index + 1);
      }

      function scrollToSection(index) {
        if (index < 0) index = 0;
        if (index >= sections.length) index = sections.length - 1;
        var target = sections[index];
        if (!target) return;

        target.scrollIntoView({
          behavior: prefersReducedMotion ? "auto" : "smooth",
          block: "start"
        });
      }

      function buildRail() {
        if (!rail) return;

        for (var index = 0; index < sections.length; index += 1) {
          var dot = document.createElement("button");
          dot.className = "story-dot";
          dot.type = "button";
          dot.setAttribute("aria-label", sectionTitle(sections[index], index));
          if (index < 9) {
            dot.setAttribute("aria-keyshortcuts", String(index + 1));
          }
          dot.dataset.index = String(index);
          dot.addEventListener("click", function () {
            scrollToSection(Number(this.dataset.index));
          });
          rail.appendChild(dot);
          dots.push(dot);
        }
      }

      function currentSectionIndex() {
        var viewportMiddle = window.scrollY + window.innerHeight * 0.45;
        var current = 0;

        for (var index = 0; index < sections.length; index += 1) {
          if (sections[index].offsetTop <= viewportMiddle) current = index;
        }

        return current;
      }

      function updateProgress() {
        var documentHeight = document.documentElement.scrollHeight - window.innerHeight;
        var pct = documentHeight > 0 ? window.scrollY / documentHeight : 0;
        pct = Math.max(0, Math.min(1, pct));

        if (progressFill) progressFill.style.width = pct * 100 + "%";
        if (chapterRule) chapterRule.style.width = pct * 100 + "%";
        if (progress) progress.setAttribute("aria-valuenow", String(Math.round(pct * 100)));
      }

      function updateActiveSection() {
        activeIndex = currentSectionIndex();

        for (var index = 0; index < sections.length; index += 1) {
          var isActive = index === activeIndex;
          sections[index].classList.toggle("is-active", isActive);
          if (dots[index]) {
            dots[index].classList.toggle("is-active", isActive);
            if (isActive) {
              dots[index].setAttribute("aria-current", "step");
            } else {
              dots[index].removeAttribute("aria-current");
            }
          }
        }

        if (chapterNumber) chapterNumber.textContent = twoDigit(activeIndex + 1);
        if (chapterLabel && sections[activeIndex]) {
          var label = sections[activeIndex].querySelector(".eyebrow");
          if (label) {
            chapterLabel.textContent = label.textContent;
          } else {
            chapterLabel.textContent = "Section " + String(activeIndex + 1);
          }
        }
      }

      function updateStoryState() {
        updateProgress();
        updateActiveSection();
      }

      function handleKeydown(event) {
        if (event.defaultPrevented ||
            event.altKey ||
            event.ctrlKey ||
            event.metaKey ||
            isEditableTarget(event.target)) {
          return;
        }

        var tagName = event.target && event.target.tagName
          ? event.target.tagName.toLowerCase()
          : "";
        if (tagName === "button" && (event.key === " " || event.key === "Enter")) {
          return;
        }

        if (/^[1-9]$/.test(event.key)) {
          var sectionIndex = Number(event.key) - 1;
          if (sectionIndex < sections.length) {
            event.preventDefault();
            scrollToSection(sectionIndex);
          }
          return;
        }

        if (event.key === "ArrowRight" ||
            event.key === "ArrowDown" ||
            event.key === "PageDown" ||
            event.key === " ") {
          event.preventDefault();
          scrollToSection(currentSectionIndex() + 1);
          return;
        }

        if (event.key === "ArrowLeft" ||
            event.key === "ArrowUp" ||
            event.key === "PageUp") {
          event.preventDefault();
          scrollToSection(currentSectionIndex() - 1);
          return;
        }

        if (event.key === "Home") {
          event.preventDefault();
          scrollToSection(0);
          return;
        }

        if (event.key === "End") {
          event.preventDefault();
          scrollToSection(sections.length - 1);
        }
      }

      buildRail();
      updateStoryState();
      window.addEventListener("scroll", updateStoryState, { passive: true });
      window.addEventListener("resize", updateStoryState);
      window.addEventListener("keydown", handleKeydown);
    })();
  </script>

</body>
</html>
```
