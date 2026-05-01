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
- A sticky chapter indicator with the current section number and label.
- Active-section transitions, such as subtle opacity, lift, or scale changes.
- Keep all interaction implemented with small vanilla JavaScript.
- Hide progress UI in print and simplify it on small screens.

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
- The sticky chapter indicator should use `aria-live="polite"` so screen readers
  announce section changes.
- Ensure all content is reachable without JavaScript: all content remains visible
  in document order (progressive enhancement, not JavaScript-dependent rendering).
- Use `prefers-reduced-motion` media query to disable scroll-triggered
  animations for users who prefer reduced motion.

## Content Structure

For technical designs or plans, prefer this structure:

1. Opening decision or design thesis.
2. Ordered behavior or architecture table.
3. Decision model / request flow / state machine.
4. Implementation draft or pseudocode.
5. Validation matrix with inputs, expected outcomes, and rationale.
6. Operational notes, such as caching, deployment, rollback, or monitoring.
7. Confidence and caveats.

Adapt the section names to the user's domain. Do not keep route inventory or
background-analysis sections unless they directly support the design.

## Code Listings

- Include syntax-highlighted code blocks for implementation drafts.
- Prefer a tiny inline highlighter or hand-authored spans over external
  libraries.
- For infrastructure functions, include comments that explain the rationale for
  each major decision branch.
- Keep code examples realistic and directly usable, but label them as drafts
  when environmental details may vary.

## Review Quality Bar

- Preserve the user's intended behavior and clearly identify pass-through,
  rewrite, fallback, and unknown/default cases.
- Make rule ordering explicit when it matters.
- Include test cases that reviewers can scan quickly.
- Surface caveats plainly rather than burying them in prose.
- Avoid masking unknown routes or failure cases in the design unless the user
  explicitly asks for catch-all behavior.

## HTML Implementation Notes

- Use one `<section>` per major step.
- Add `data`-free, generated navigation by scanning sections in JavaScript.
- Use CSS custom properties for the palette so future palette changes are easy.
- Validate embedded JavaScript syntax after edits.
- Keep the presentation readable when JavaScript is disabled: all content should
  remain visible in document order.

## HTML Skeleton

Use this as a starting scaffold. Adapt the sections to match the plan content —
this is a structural reference, not a rigid template.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Design Memo — TOPIC</title>
  <style>
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

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: Georgia, "Times New Roman", serif;
      background: var(--paper);
      color: var(--ink);
      line-height: 1.6;
      max-width: 960px;
      margin: 0 auto;
      padding: 2rem 1.5rem 4rem;
    }

    /* Progress bar */
    #progress {
      position: fixed;
      top: 0;
      left: 0;
      height: 3px;
      background: var(--teal);
      width: 0%;
      z-index: 100;
      transition: width 80ms linear;
    }

    /* Section rail */
    #rail {
      position: fixed;
      right: 1.5rem;
      top: 50%;
      transform: translateY(-50%);
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      z-index: 90;
    }

    #rail button {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      border: 2px solid var(--line);
      background: transparent;
      cursor: pointer;
      padding: 0;
      position: relative;
      transition: background 0.2s, border-color 0.2s;
    }

    #rail button:focus-visible {
      outline: 2px solid var(--teal);
      outline-offset: 2px;
    }

    #rail button[aria-current="step"] {
      background: var(--teal);
      border-color: var(--teal);
    }

    #rail button .label {
      position: absolute;
      right: 1.25rem;
      top: 50%;
      transform: translateY(-50%);
      white-space: nowrap;
      font-size: 0.75rem;
      color: var(--muted);
      opacity: 0;
      transition: opacity 0.15s;
      pointer-events: none;
    }

    #rail button:hover .label,
    #rail button:focus .label {
      opacity: 1;
    }

    /* Chapter indicator */
    #chapter {
      position: sticky;
      top: 0.5rem;
      font-size: 0.8rem;
      color: var(--muted);
      padding: 0.25rem 0;
      z-index: 80;
    }

    /* Sections */
    section {
      margin: 3rem 0;
      opacity: 0.4;
      transition: opacity 0.4s ease;
    }

    section.active { opacity: 1; }

    section h2 {
      font-size: 1.5rem;
      border-bottom: 2px solid var(--line);
      padding-bottom: 0.25rem;
      margin-bottom: 1rem;
      color: var(--ink);
    }

    /* Margin notes */
    .margin-note {
      float: right;
      clear: right;
      width: 200px;
      margin-right: -240px;
      font-size: 0.8rem;
      color: var(--muted);
      border-left: 2px solid var(--line);
      padding-left: 0.5rem;
    }

    /* Tables */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
    }

    th, td {
      text-align: left;
      padding: 0.5rem 0.75rem;
      border-bottom: 1px solid var(--line);
    }

    th { border-bottom: 2px solid var(--ink); }

    /* Code */
    pre {
      background: var(--code-bg);
      color: var(--code);
      padding: 1rem;
      overflow-x: auto;
      font-size: 0.85rem;
      border-left: 3px solid var(--olive);
      margin: 1rem 0;
    }

    code {
      font-family: "SF Mono", "Cascadia Code", "Fira Code", monospace;
    }

    /* Print */
    @media print {
      #progress, #rail, #chapter { display: none; }
      section { opacity: 1; break-inside: avoid; }
    }

    /* Small screens */
    @media (max-width: 720px) {
      #rail { display: none; }
      .margin-note {
        float: none;
        width: auto;
        margin: 0.5rem 0;
      }
    }

    /* Reduced motion */
    @media (prefers-reduced-motion: reduce) {
      section { transition: none; }
      #progress { transition: none; }
    }
  </style>
</head>
<body>

  <div id="progress" role="progressbar"
       aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>

  <div id="chapter" aria-live="polite"></div>

  <section>
    <h2>1. Design Thesis</h2>
    <!-- Opening decision or design thesis -->
  </section>

  <section>
    <h2>2. Architecture</h2>
    <!-- Ordered behavior or architecture table -->
  </section>

  <section>
    <h2>3. Decision Model</h2>
    <!-- Decision model / request flow / state machine -->
  </section>

  <section>
    <h2>4. Implementation Draft</h2>
    <!-- Implementation draft or pseudocode -->
  </section>

  <section>
    <h2>5. Validation</h2>
    <!-- Validation matrix -->
  </section>

  <section>
    <h2>6. Operations</h2>
    <!-- Operational notes -->
  </section>

  <section>
    <h2>7. Confidence & Caveats</h2>
    <!-- Caveats and confidence levels -->
  </section>

  <nav id="rail" role="navigation" aria-label="Section navigation"></nav>

  <script>
    (function () {
      var sections = document.querySelectorAll("section");
      var rail = document.getElementById("rail");
      var progress = document.getElementById("progress");
      var chapter = document.getElementById("chapter");

      /* Build rail dots */
      sections.forEach(function (sec, i) {
        var heading = sec.querySelector("h2");
        var btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("aria-label", heading ? heading.textContent : "Section " + (i + 1));
        var label = document.createElement("span");
        label.className = "label";
        label.textContent = heading ? heading.textContent : "Section " + (i + 1);
        btn.appendChild(label);
        btn.addEventListener("click", function () {
          sec.scrollIntoView({ behavior: "smooth" });
        });
        rail.appendChild(btn);
      });

      var dots = rail.querySelectorAll("button");

      function onScroll() {
        /* Progress bar */
        var scrollTop = window.scrollY;
        var docHeight = document.documentElement.scrollHeight - window.innerHeight;
        var pct = docHeight > 0 ? Math.round((scrollTop / docHeight) * 100) : 0;
        progress.style.width = pct + "%";
        progress.setAttribute("aria-valuenow", pct);

        /* Active section */
        var current = 0;
        sections.forEach(function (sec, i) {
          var rect = sec.getBoundingClientRect();
          if (rect.top <= window.innerHeight * 0.4) current = i;
        });

        sections.forEach(function (sec, i) {
          sec.classList.toggle("active", i === current);
        });

        dots.forEach(function (dot, i) {
          if (i === current) {
            dot.setAttribute("aria-current", "step");
          } else {
            dot.removeAttribute("aria-current");
          }
        });

        /* Chapter indicator */
        var heading = sections[current] && sections[current].querySelector("h2");
        if (heading) chapter.textContent = heading.textContent;
      }

      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    })();
  </script>

</body>
</html>
```
