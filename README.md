# Skills

A collection of skills that extend Claude's capabilities for specialized tasks.

## Available Skills

| Skill | Description |
|-------|-------------|
| [dns-troubleshooter](./dns-troubleshooter/) | *It's not DNS / There's no way it's DNS / It was DNS.* Diagnose DNS issues including delegation verification, SPF validation, record conflicts, and authoritative vs local DNS comparison |

> **Copilot Compatible:** All skills in this repository work with both Claude and GitHub Copilot (December 2025+).

## Quick Install

Use the install script for easy installation:

```bash
# Clone the repo
git clone https://github.com/statik/skills.git
cd skills

# Install to a specific platform
./install.sh --claude          # Claude Code
./install.sh --codex           # Codex CLI
./install.sh --opencode        # OpenCode
./install.sh --desktop         # Claude Desktop
./install.sh --copilot . .     # GitHub Copilot (current project)
./install.sh --all             # All global locations

# Or use just commands
just install-claude
just install-codex
just install-opencode
just install-all
```

## Installation

Skills can be added to Claude in several ways depending on your environment.

### Claude Code (CLI)

Clone this repository and copy skills to your project's `.claude/skills/` directory:

```bash
# Clone the repo
git clone https://github.com/statik/skills.git

# Copy a skill to your project
cp -r skills/dns-troubleshooter /path/to/your/project/.claude/skills/
```

Or add skills globally to `~/.claude/skills/`:

```bash
mkdir -p ~/.claude/skills
cp -r skills/dns-troubleshooter ~/.claude/skills/
```

### Codex CLI

Codex loads skills from `$CODEX_HOME/skills` (defaults to `~/.codex/skills`). Install the skill into that directory:

```bash
# Codex requires OPENAI_API_KEY
export OPENAI_API_KEY="your-key"

mkdir -p ~/.codex/skills
cp -r skills/dns-troubleshooter ~/.codex/skills/
```

To run Codex with the skill available:

```bash
codex exec "Check if the SPF record for example.com is valid."
```

### OpenCode

OpenCode natively supports skills in the same format. Copy skills to one of these locations:

**Project-level (recommended):**
```bash
# Native skills directory (OpenCode v1.0.190+)
cp -r skills/dns-troubleshooter /path/to/your/project/skill/

# Or the .opencode directory
cp -r skills/dns-troubleshooter /path/to/your/project/.opencode/skills/
```

**Global installation:**
```bash
# XDG config location (Linux/macOS)
mkdir -p ~/.config/opencode/skills
cp -r skills/dns-troubleshooter ~/.config/opencode/skills/

# Alternative global location
mkdir -p ~/.opencode/skills
cp -r skills/dns-troubleshooter ~/.opencode/skills/
```

### VS Code with GitHub Copilot

GitHub Copilot supports Agent Skills as of December 2025. Skills can be installed in multiple locations:

**Option 1: GitHub Skills directory (recommended)**
```
your-project/
├── .github/
│   └── skills/
│       └── dns-troubleshooter/
│           ├── SKILL.md
│           └── references/
│               └── spf.md
└── ... your code
```

**Option 2: Claude Skills directory (also supported)**

Copilot automatically discovers skills in `.claude/skills/`:
```
your-project/
├── .claude/
│   └── skills/
│       └── dns-troubleshooter/
│           ├── SKILL.md
│           └── references/
│               └── spf.md
└── ... your code
```

**Note:** Ensure the `chat.useAgentSkills` setting is enabled in VS Code.

### Claude.app (Desktop)

Skills can be added to Claude.app by placing them in your user skills directory:

**macOS:**
```bash
mkdir -p ~/Library/Application\ Support/Claude/skills
cp -r dns-troubleshooter ~/Library/Application\ Support/Claude/skills/
```

**Windows:**
```powershell
mkdir -p "$env:APPDATA\Claude\skills"
Copy-Item -Recurse dns-troubleshooter "$env:APPDATA\Claude\skills\"
```

**Linux:**
```bash
mkdir -p ~/.config/claude/skills
cp -r dns-troubleshooter ~/.config/claude/skills/
```

## Using Skills

Once installed, skills are automatically available to Claude. Simply ask Claude to perform tasks related to the skill's domain:

**DNS Troubleshooter examples:**
- "Why am I getting NXDOMAIN for example.com?"
- "Check if my SPF record is configured correctly"
- "Compare what my local DNS says vs the authoritative server for mysite.com"
- "Are there any conflicting DNS records for api.example.com?"

Claude will use the skill's knowledge and workflows to help diagnose and resolve issues.

## Evaluation Results

Skills are evaluated using [InspectAI](https://inspect.aisi.org.uk/). View the latest evaluation results at:

https://statik.github.io/skills/

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for information on creating your own skills, running evaluations, and development setup.

## License

See [LICENSE](./LICENSE) for details.
