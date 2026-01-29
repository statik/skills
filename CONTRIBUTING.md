# Contributing

Thanks for your interest in contributing to this skills repository!

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/statik/skills.git
   cd skills
   ```

2. **Install dependencies**
   ```bash
   just setup
   ```

3. **Make your changes**

4. **Validate and test**
   ```bash
   just check      # Quick validation
   just test       # Full evaluation suite (requires ANTHROPIC_API_KEY)
   ```

## Development Commands

Run `just` to see all available commands:

| Command | Description |
|---------|-------------|
| `just setup` | Install dependencies |
| `just validate` | Validate skill structure |
| `just check` | Quick validation (no evals) |
| `just test` | Run evaluations (alias for test-claude-anthropic) |
| `just test-claude-anthropic` | Claude Code CLI + Anthropic scoring |
| `just test-claude-bedrock` | Claude Code CLI + Bedrock scoring |
| `just test-codex` | Codex CLI + OpenAI scoring |
| `just release <version>` | Create a new release |
| `just clean` | Remove generated files |

## Creating a New Skill

Each skill is a directory containing:

```
my-skill/
├── SKILL.md          # Required: Instructions and metadata
├── scripts/          # Optional: Executable scripts
├── references/       # Optional: Reference documentation
└── assets/           # Optional: Templates, images, etc.
```

### SKILL.md Structure

The `SKILL.md` file must include YAML frontmatter with `name` and `description` fields:

```yaml
---
name: my-skill
description: What this skill does and when to use it.
metadata:
  version: 1.0.0
---

# My Skill

Instructions for Claude on how to use this skill...
```

See the [Agent Skills Specification](https://agentskills.io) for detailed documentation.

### Steps to Add a Skill

1. Create a directory with your skill name
2. Add a `SKILL.md` file with the required frontmatter
3. Optionally add `references/`, `scripts/`, or `assets/` directories
4. Run `just validate` to check your skill
5. Submit a pull request

### Updating the Manifest

When adding or modifying skills, update `manifest.json` at the repo root:

1. Add a new entry to the `skills` array with:
   - `name`: Skill directory name
   - `version`: Current version from SKILL.md
   - `path`: Relative path to skill directory
   - `description`: Brief description
   - `keywords`: Array of relevant keywords
   - `platforms`: Supported platforms
   - `files`: Map of skill files

2. Keep the manifest in sync with SKILL.md versions

## Running Evaluations

Evaluations test skills by running them through CLI tools and scoring the results.

### Evaluation Options

All commands follow the pattern `test-<generation>-<scoring>`:

**Claude Code CLI + Anthropic API (default):**
```bash
export ANTHROPIC_API_KEY="your-key"
just test-claude-anthropic  # or just: just test
```
Tests the skill using Claude Code CLI with the skill installed in `.claude/skills/`.

**Claude Code CLI + AWS Bedrock:**
```bash
# Configure AWS credentials first
just test-claude-bedrock
```
Uses Claude Code CLI for generation and AWS Bedrock for scoring.

**Codex CLI + OpenAI API:**
```bash
# Configure OPENAI_API_KEY first
just test-codex
```
Uses Codex CLI for generation. The `DNS_SKILL_RUNNER=codex` environment variable switches the eval
runner, while InspectAI uses the specified OpenAI model for scoring.

## Pull Request Guidelines

- Ensure `just validate` passes
- Run `just test` if you've modified skill behavior
- Keep changes focused and well-described
- CI will automatically run validation and evals on your PR

## Publishing Releases

Skills are distributed as versioned zip files via GitHub Releases.

### Release Process

1. **Update the version in SKILL.md**

   Edit `dns-troubleshooter/SKILL.md` and update the `metadata.version` field in the frontmatter:
   ```yaml
   ---
   name: dns-troubleshooter
   description: ...
   metadata:
     version: 1.1.0  # bump this
   ---
   ```

2. **Commit the version bump**
   ```bash
   git add dns-troubleshooter/SKILL.md
   git commit -m "Bump dns-troubleshooter to v1.1.0"
   git push
   ```

3. **Create the release**
   ```bash
   just release 1.1.0
   ```

   This command:
   - Verifies the SKILL.md version matches the release version
   - Checks for uncommitted changes
   - Creates an annotated git tag (`v1.1.0`)
   - Pushes the tag to GitHub

4. **GitHub Actions takes over**

   The `release.yml` workflow automatically:
   - Creates a zip file of the skill directory
   - Publishes a GitHub Release with the zip attached
   - Includes installation instructions in the release notes

### Version Numbering

Follow [semantic versioning](https://semver.org/):
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes to skill behavior
- **MINOR** (1.0.0 → 1.1.0): New features, backward compatible
- **PATCH** (1.0.0 → 1.0.1): Bug fixes, documentation updates

### Verifying a Release

After pushing a tag, check the [Actions tab](https://github.com/statik/skills/actions) to monitor the release workflow. Once complete, verify:
- The release appears on the [Releases page](https://github.com/statik/skills/releases)
- The zip file downloads correctly
- The zip contains the expected files

## Questions?

Open an issue if you have questions or run into problems.
