"""
InspectAI eval for dns-troubleshooter skill.

Tests the skill by running Claude Code CLI with the skill installed,
using a local test DNS server for queries.
"""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.model import ModelOutput, ChatMessageAssistant
from inspect_ai.scorer import model_graded_fact
from inspect_ai.solver import Solver, TaskState, solver

from dns_server import TestDNSServer
from test_zones import get_all_zones, SCENARIOS, TEST_DOMAIN

# Port for the test DNS server
DNS_PORT = int(os.environ.get("DNS_TEST_PORT", "5053"))

# Path to the skill
SKILL_PATH = Path(__file__).parent.parent / "dns-troubleshooter"

# Timeout for Claude Code execution (seconds)
CLAUDE_TIMEOUT = 120

# Global server instance for the eval
_server: TestDNSServer | None = None


def start_dns_server():
    """Start the test DNS server."""
    global _server
    if _server is None:
        zones = get_all_zones()
        _server = TestDNSServer(zones, port=DNS_PORT)
        _server.start()


def stop_dns_server():
    """Stop the test DNS server."""
    global _server
    if _server is not None:
        _server.stop()
        _server = None


def setup_skill_directory(work_dir: Path) -> None:
    """Set up the skill in the working directory's .claude/skills folder."""
    skills_dir = work_dir / ".claude" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Copy the skill to the working directory
    dest = skills_dir / "dns-troubleshooter"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SKILL_PATH, dest)


def setup_copilot_skill_directory(work_dir: Path) -> None:
    """Set up the skill in GitHub Copilot's skills folder."""
    skills_dir = work_dir / ".github" / "copilot" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Copy the skill to the working directory
    dest = skills_dir / "dns-troubleshooter"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SKILL_PATH, dest)


def run_claude_code(prompt: str, work_dir: Path, model: str | None = None) -> str:
    """Run Claude Code CLI with the given prompt and return the response."""
    # Build the command
    cmd = [
        "claude",
        "--print",
        "--dangerously-skip-permissions",
        "--output-format", "json",
    ]

    if model:
        cmd.extend(["--model", model])

    # Add the prompt
    cmd.append(prompt)

    # Run Claude Code
    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            env={**os.environ, "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "")},
        )

        if result.returncode != 0:
            return f"Error running Claude Code: {result.stderr}"

        # Parse JSON output to extract the response
        try:
            output = json.loads(result.stdout)
            # The JSON output contains the conversation - extract the last assistant message
            if isinstance(output, dict) and "result" in output:
                return output["result"]
            elif isinstance(output, list):
                # Find the last assistant message
                for msg in reversed(output):
                    if msg.get("type") == "assistant":
                        content = msg.get("content", [])
                        text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                        return "\n".join(text_parts)
            return result.stdout
        except json.JSONDecodeError:
            return result.stdout

    except subprocess.TimeoutExpired:
        return f"Error: Claude Code timed out after {CLAUDE_TIMEOUT} seconds"
    except Exception as e:
        return f"Error running Claude Code: {str(e)}"


def run_copilot_cli(prompt: str, work_dir: Path) -> str:
    """Run GitHub Copilot CLI with the given prompt and return the response."""
    # Build the command - using --prompt flag for non-interactive usage
    cmd = [
        "copilot",
        "--prompt", prompt,
    ]

    # Run GitHub Copilot CLI
    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT,
            env={**os.environ},
        )

        if result.returncode != 0:
            return f"Error running GitHub Copilot: {result.stderr}"

        # Return the stdout directly - Copilot CLI outputs text response
        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        return f"Error: GitHub Copilot timed out after {CLAUDE_TIMEOUT} seconds"
    except Exception as e:
        return f"Error running GitHub Copilot: {str(e)}"


@solver
def claude_code_solver(model: str | None = None) -> Solver:
    """
    Solver that runs Claude Code CLI with the dns-troubleshooter skill.

    This executes the actual Claude Code CLI rather than directly invoking the model,
    testing the skill as it would be used in practice.
    """

    async def solve(state: TaskState, generate) -> TaskState:
        # Create a temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)

            # Set up the skill in the working directory
            setup_skill_directory(work_dir)

            # Get the user's input prompt
            user_input = state.input_text

            # Add context about the test DNS server
            full_prompt = f"""{user_input}

IMPORTANT: For all DNS queries, use the test DNS server at 127.0.0.1 port {DNS_PORT}.
Use dig with: dig @127.0.0.1 -p {DNS_PORT} <domain> <record_type>

When analyzing DNS records, provide:
1. Your finding
2. The command you used to verify
3. Your diagnosis (valid, invalid, warning, insecure, incomplete)
4. Explanation of the issue if any"""

            # Run Claude Code and get the response
            response = await asyncio.to_thread(
                run_claude_code, full_prompt, work_dir, model
            )

            # Create the model output
            state.output = ModelOutput.from_content(
                model="claude-code",
                content=response,
            )

            # Add assistant message to the conversation
            state.messages.append(
                ChatMessageAssistant(content=response)
            )

        return state

    return solve


@solver
def copilot_cli_solver() -> Solver:
    """
    Solver that runs GitHub Copilot CLI with the dns-troubleshooter skill.

    This executes the actual GitHub Copilot CLI rather than directly invoking the model,
    testing the skill as it would be used with GitHub Copilot.
    """

    async def solve(state: TaskState, generate) -> TaskState:
        # Create a temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            work_dir = Path(temp_dir)

            # Set up the skill for GitHub Copilot
            setup_copilot_skill_directory(work_dir)

            # Get the user's input prompt
            user_input = state.input_text

            # Add context about the test DNS server
            full_prompt = f"""{user_input}

IMPORTANT: For all DNS queries, use the test DNS server at 127.0.0.1 port {DNS_PORT}.
Use dig with: dig @127.0.0.1 -p {DNS_PORT} <domain> <record_type>

When analyzing DNS records, provide:
1. Your finding
2. The command you used to verify
3. Your diagnosis (valid, invalid, warning, insecure, incomplete)
4. Explanation of the issue if any"""

            # Run GitHub Copilot CLI and get the response
            response = await asyncio.to_thread(
                run_copilot_cli, full_prompt, work_dir
            )

            # Create the model output
            state.output = ModelOutput.from_content(
                model="github-copilot",
                content=response,
            )

            # Add assistant message to the conversation
            state.messages.append(
                ChatMessageAssistant(content=response)
            )

        return state

    return solve


def create_spf_samples() -> list[Sample]:
    """Create evaluation samples for SPF scenarios."""
    samples = []

    for scenario_id, scenario in SCENARIOS.items():
        if scenario["category"] != "spf":
            continue

        domain = scenario["zone"]
        expected = scenario["expected_diagnosis"]
        description = scenario["description"]

        samples.append(
            Sample(
                input=f"Analyze the SPF record for {domain} and determine if it is properly configured. What issues, if any, exist?",
                target=f"The SPF record should be diagnosed as: {expected}. {description}",
                metadata={
                    "scenario_id": scenario_id,
                    "category": "spf",
                    "expected_diagnosis": expected,
                },
            )
        )

    return samples


def create_conflict_samples() -> list[Sample]:
    """Create evaluation samples for record conflict scenarios."""
    samples = []

    for scenario_id, scenario in SCENARIOS.items():
        if scenario["category"] != "conflict":
            continue

        domain = scenario["zone"]
        expected = scenario["expected_diagnosis"]
        description = scenario["description"]

        samples.append(
            Sample(
                input=f"Check the DNS records for {domain} for any conflicts or misconfigurations. Are there any issues?",
                target=f"The configuration should be diagnosed as: {expected}. {description}",
                metadata={
                    "scenario_id": scenario_id,
                    "category": "conflict",
                    "expected_diagnosis": expected,
                },
            )
        )

    return samples


def create_all_samples() -> list[Sample]:
    """Create all evaluation samples."""
    samples = []
    samples.extend(create_spf_samples())
    samples.extend(create_conflict_samples())
    return samples


@task
def dns_troubleshooter_eval() -> Task:
    """Main evaluation task for dns-troubleshooter skill using Claude Code CLI."""
    # Start the DNS server
    start_dns_server()

    samples = create_all_samples()
    dataset = MemoryDataset(samples=samples, name="dns-troubleshooter-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(),
        ],
        scorer=model_graded_fact(),
    )


@task
def dns_spf_eval() -> Task:
    """SPF-focused evaluation task using Claude Code CLI."""
    start_dns_server()

    samples = create_spf_samples()
    dataset = MemoryDataset(samples=samples, name="dns-spf-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(),
        ],
        scorer=model_graded_fact(),
    )


@task
def dns_conflict_eval() -> Task:
    """Record conflict evaluation task using Claude Code CLI."""
    start_dns_server()

    samples = create_conflict_samples()
    dataset = MemoryDataset(samples=samples, name="dns-conflict-eval")

    return Task(
        dataset=dataset,
        solver=[
            claude_code_solver(),
        ],
        scorer=model_graded_fact(),
    )


@task
def dns_troubleshooter_copilot_eval() -> Task:
    """Main evaluation task for dns-troubleshooter skill using GitHub Copilot CLI."""
    # Start the DNS server
    start_dns_server()

    samples = create_all_samples()
    dataset = MemoryDataset(samples=samples, name="dns-troubleshooter-copilot-eval")

    return Task(
        dataset=dataset,
        solver=[
            copilot_cli_solver(),
        ],
        scorer=model_graded_fact(),
    )


@task
def dns_spf_copilot_eval() -> Task:
    """SPF-focused evaluation task using GitHub Copilot CLI."""
    start_dns_server()

    samples = create_spf_samples()
    dataset = MemoryDataset(samples=samples, name="dns-spf-copilot-eval")

    return Task(
        dataset=dataset,
        solver=[
            copilot_cli_solver(),
        ],
        scorer=model_graded_fact(),
    )


@task
def dns_conflict_copilot_eval() -> Task:
    """Record conflict evaluation task using GitHub Copilot CLI."""
    start_dns_server()

    samples = create_conflict_samples()
    dataset = MemoryDataset(samples=samples, name="dns-conflict-copilot-eval")

    return Task(
        dataset=dataset,
        solver=[
            copilot_cli_solver(),
        ],
        scorer=model_graded_fact(),
    )


if __name__ == "__main__":
    # Quick test of the DNS server
    print(f"Starting DNS server on port {DNS_PORT}...")
    start_dns_server()
    print(f"Test with: dig @127.0.0.1 -p {DNS_PORT} spf-valid.{TEST_DOMAIN} TXT")
    print(f"Test with: dig @127.0.0.1 -p {DNS_PORT} spf-multiple.{TEST_DOMAIN} TXT")
    print("Press Ctrl+C to stop")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_dns_server()
        print("Server stopped.")
