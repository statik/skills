# Justfile for skills repository
# https://github.com/casey/just

# Model aliases for convenience
anthropic_sonnet := "anthropic/claude-sonnet-4-5-20250929"
bedrock_sonnet := "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Default recipe - show available commands
default:
    @just --list

# Setup development environment
setup:
    cd evals && uv sync

# Validate all skills using agentskills (from skills-ref package)
validate:
    uvx --from skills-ref agentskills validate dns-troubleshooter

# Run evals using Claude Code CLI with Anthropic API for scoring
test-claude-anthropic log_dir="" display="":
    cd evals && uv run inspect eval dns_skill_eval.py --model {{ anthropic_sonnet }} {{ if log_dir != "" { "--log-dir " + log_dir } else { "" } }} {{ if display != "" { "--display " + display } else { "" } }}

# Run evals using Claude Code CLI with AWS Bedrock for scoring
test-claude-bedrock log_dir="" display="":
    cd evals && uv run inspect eval dns_skill_eval.py --model {{ bedrock_sonnet }} {{ if log_dir != "" { "--log-dir " + log_dir } else { "" } }} {{ if display != "" { "--display " + display } else { "" } }}

# Run evals using GitHub Copilot CLI with Anthropic API for scoring
test-copilot-anthropic log_dir="" display="":
    cd evals && uv run inspect eval dns_skill_eval.py@dns_troubleshooter_copilot_eval --model {{ anthropic_sonnet }} {{ if log_dir != "" { "--log-dir " + log_dir } else { "" } }} {{ if display != "" { "--display " + display } else { "" } }}

# Run evals using GitHub Copilot CLI with AWS Bedrock for scoring
test-copilot-bedrock log_dir="" display="":
    cd evals && uv run inspect eval dns_skill_eval.py@dns_troubleshooter_copilot_eval --model {{ bedrock_sonnet }} {{ if log_dir != "" { "--log-dir " + log_dir } else { "" } }} {{ if display != "" { "--display " + display } else { "" } }}

# Alias: default test command (Claude Code CLI + Anthropic)
test log_dir="" display="": (test-claude-anthropic log_dir display)

# Test if GitHub Copilot CLI is loading the skill correctly
test-copilot-skill:
    cd evals && uv run python test_copilot_skill_loading.py

# Check if most recent eval log shows skill usage
check-skill-usage log_file="":
    cd evals && uv run python check_skill_usage.py {{ log_file }}

# Start the test DNS server (runs in foreground)
dns-server:
    cd evals && uv run python dns_server.py

# Run quick validation (no evals, just structure checks)
check: validate
    @echo "All validation checks passed!"

# Clean generated files
clean:
    rm -rf evals/.venv
    rm -rf evals/__pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Create a new release
# Usage: just release 1.0.0
release version:
    #!/usr/bin/env bash
    set -euo pipefail

    # Verify version matches SKILL.md metadata.version
    SKILL_VERSION=$(grep -A1 '^metadata:' dns-troubleshooter/SKILL.md | grep 'version:' | sed 's/.*version: //')
    if [ "$SKILL_VERSION" != "{{ version }}" ]; then
        echo "Error: Version mismatch!"
        echo "  SKILL.md metadata.version: $SKILL_VERSION"
        echo "  Requested version: {{ version }}"
        echo ""
        echo "Update dns-troubleshooter/SKILL.md first:"
        echo "  metadata:"
        echo "    version: {{ version }}"
        exit 1
    fi

    # Check for uncommitted changes
    if ! git diff --quiet HEAD; then
        echo "Error: You have uncommitted changes. Please commit first."
        exit 1
    fi

    # Create and push tag
    echo "Creating tag v{{ version }}..."
    git tag -a "v{{ version }}" -m "Release dns-troubleshooter v{{ version }}"
    git push origin "v{{ version }}"
    echo ""
    echo "Tag v{{ version }} pushed. GitHub Actions will create the release."
    echo "Watch progress at: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//' | sed 's/.git$//')/actions"
