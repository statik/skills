# Justfile for skills repository
# https://github.com/casey/just

# Model aliases for convenience
anthropic_sonnet := "anthropic/claude-sonnet-4-5-20250514"
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

# Run InspectAI evaluations
# Usage: just test [model] [log_dir] [display]
# Examples:
#   just test                                    # uses defaults
#   just test anthropic/claude-sonnet-4-5-20250514 ./logs none  # all args
test model=anthropic_sonnet log_dir="" display="":
    cd evals && uv run inspect eval dns_skill_eval.py --model {{ model }} {{ if log_dir != "" { "--log-dir " + log_dir } else { "" } }} {{ if display != "" { "--display " + display } else { "" } }}

# Run evals using AWS Bedrock (requires AWS credentials)
test-bedrock log_dir="" display="":
    cd evals && uv run inspect eval dns_skill_eval.py --model {{ bedrock_sonnet }} {{ if log_dir != "" { "--log-dir " + log_dir } else { "" } }} {{ if display != "" { "--display " + display } else { "" } }}

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
