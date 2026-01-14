# Skills

A collection of skills that extend Claude's capabilities for specialized tasks.

## Available Skills

| Skill | Description |
|-------|-------------|
| [dns-troubleshooter](./dns-troubleshooter/) | *It's not DNS / There's no way it's DNS / It was DNS.* Diagnose DNS issues including delegation verification, SPF validation, record conflicts, and authoritative vs local DNS comparison |

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

### VS Code with GitHub Copilot

1. Open your project in VS Code
2. Create a `.github/copilot/skills/` directory in your workspace root
3. Copy the skill folder into it:

```
your-project/
├── .github/
│   └── copilot/
│       └── skills/
│           └── dns-troubleshooter/
│               ├── SKILL.md
│               └── references/
│                   └── spf.md
└── ... your code
```

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

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for information on creating your own skills, running evaluations, and development setup.

## License

See [LICENSE](./LICENSE) for details.
