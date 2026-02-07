# Agent Instructions

This document provides instructions for AI agents working on this repository.

## Repository Overview

This is a skills repository containing specialized capabilities that extend Claude's abilities for domain-specific tasks. Skills follow the [Agent Skills Specification](https://agentskills.io).

## Verifying Changes

Before submitting any changes, verify them using these steps:

### 1. Validate Skill Structure

All skills must pass validation using the `skills-ref` tool:

```bash
just validate
```

Or manually:

```bash
uvx --from skills-ref agentskills validate skills/dns-troubleshooter
```

This checks:
- SKILL.md exists with valid YAML frontmatter
- Required `name` and `description` fields are present
- File structure follows the specification

### 2. Run Evaluations

For changes to skill content or behavior, run the InspectAI evaluation suite:

```bash
just test
```

This starts a test DNS server and runs the evaluation suite. The evals test:
- SPF record validation scenarios
- DNS record conflict detection
- Delegation checking

#### Using AWS Bedrock

To run evals with AWS Bedrock instead of the Anthropic API:

```bash
just test-bedrock
```

This requires AWS credentials configured via environment variables or AWS CLI profile. You can also specify a custom model:

```bash
just test model="bedrock/anthropic.claude-sonnet-4-5-20250514-v1:0"
```

### 3. Quick Check

For structural changes only (no behavioral changes), a quick validation is sufficient:

```bash
just check
```

## Code Formatting

This repository contains primarily Markdown files (SKILL.md, reference docs) and Python evaluation code.

### Markdown Files

- Use standard Markdown formatting
- SKILL.md files must have YAML frontmatter with `name` and `description`
- Keep line lengths reasonable for readability

### Python Code (in `evals/`)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep test scenarios well-documented in `test_zones.py`

## File Structure

```
.claude-plugin/
├── marketplace.json        # Plugin marketplace manifest
└── plugin.json             # Plugin metadata
skills/
├── dns-troubleshooter/     # Example skill
│   ├── SKILL.md           # Required: skill definition
│   └── references/        # Optional: reference documentation
evals/                      # InspectAI evaluation suite
├── dns_skill_eval.py       # Evaluation tasks
├── dns_server.py           # Test DNS server
└── test_zones.py           # Test data
Justfile                    # Development commands
AGENTS.md                   # This file
```

## Creating New Skills

When creating a new skill:

1. Create a directory with the skill name
2. Add a `SKILL.md` with YAML frontmatter:
   ```yaml
   ---
   name: skill-name
   description: Brief description of what the skill does
   ---
   ```
3. Add skill instructions in the Markdown body
4. Optionally add `references/`, `scripts/`, or `assets/` directories
5. Validate with `just validate`
6. Consider adding evaluation tests if the skill has testable behavior

## CI/CD

GitHub Actions automatically runs on PRs and pushes to main:

1. **validate** job: Checks skill structure with `skills-ref`
2. **run-evals** job: Runs the InspectAI evaluation suite

Both jobs must pass for changes to be merged.

## Common Issues

### uvx not found

Install uv (which provides uvx):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Eval failures

Check that:
- The test DNS server can bind to port 5053
- Required credentials are configured:
  - Anthropic API: `ANTHROPIC_API_KEY` environment variable
  - AWS Bedrock: AWS credentials via environment variables or `~/.aws/credentials`
- The model specified is available and has sufficient quota

### Import errors in evals

Ensure dependencies are installed:
```bash
cd evals && uv sync
```
