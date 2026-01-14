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
| `just test` | Run full evaluation suite |
| `just test-bedrock` | Run evals using AWS Bedrock |
| `just clean` | Remove generated files |

## Adding a New Skill

1. Create a directory with your skill name
2. Add a `SKILL.md` file with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: What this skill does
   ---

   # My Skill

   Instructions for Claude...
   ```
3. Optionally add `references/`, `scripts/`, or `assets/` directories
4. Run `just validate` to check your skill
5. Submit a pull request

## Running Evaluations

Evals require an API key. Choose one:

**Anthropic API:**
```bash
export ANTHROPIC_API_KEY="your-key"
just test
```

**AWS Bedrock:**
```bash
# Configure AWS credentials first
just test-bedrock
```

## Pull Request Guidelines

- Ensure `just validate` passes
- Run `just test` if you've modified skill behavior
- Keep changes focused and well-described
- CI will automatically run validation and evals on your PR

## Questions?

Open an issue if you have questions or run into problems.
